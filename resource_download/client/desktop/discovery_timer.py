"""Client-owned discovery polling and optional local auto-enqueue."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode

from .client_timer import ClientTimer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else dict(default)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return dict(default)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


class ClientDiscoveryTimer:
    """Persisted discovery timer whose only server dependency is read-only API."""

    DEFAULT_CONFIG: dict[str, Any] = {
        "platform": "all",
        "kinds": ["hot", "new"],
        "limit": 24,
        "auto_enqueue": False,
        "scan_limit": 50,
        "min_episode_count": 0,
        "max_auto_enqueue_per_scan": 20,
        "include_keywords": [],
        "exclude_keywords": [],
        "author_keywords": [],
    }

    def __init__(
        self,
        request: Callable[[str, str, str], dict[str, Any]],
        resolve: Callable[[dict[str, Any], str, str], dict[str, Any]],
        state_dir: str | Path,
    ) -> None:
        self._request = request
        self._resolve = resolve
        self._state_dir = Path(state_dir).expanduser().resolve()
        self._config_path = self._state_dir / "discovery_config.json"
        self._cache_path = self._state_dir / "discovery_cache.json"
        self._config = {**self.DEFAULT_CONFIG, **_read_json(self._config_path, self.DEFAULT_CONFIG)}
        self._cache = _read_json(self._cache_path, {})
        self._credentials = {"access_token": "", "api_key": ""}
        self._lock = threading.RLock()
        self.timer = ClientTimer(
            self._poll,
            self._state_dir / "discovery_timer.json",
            interval_seconds=int(self._config.get("interval_seconds") or 300),
        )
        if bool(self._config.get("enabled")):
            self.timer.start()

    def configure(
        self,
        settings: dict[str, Any] | None,
        access_token: str = "",
        api_key: str = "",
    ) -> dict[str, Any]:
        settings = dict(settings or {})
        with self._lock:
            self._credentials = {
                "access_token": str(access_token or ""),
                "api_key": str(api_key or ""),
            }
            for key in self.DEFAULT_CONFIG:
                if key in settings:
                    self._config[key] = settings[key]
            interval = max(30, min(86400, int(settings.get("interval_seconds") or 300)))
            self._config["interval_seconds"] = interval
            self._config["enabled"] = bool(settings.get("enabled", self._config.get("enabled", False)))
            self._config["last_configured_at"] = _now()
            _write_json(self._config_path, self._config)
            self.timer.configure(enabled=bool(self._config["enabled"]), interval_seconds=interval)
        return self.status()

    def set_credentials(self, access_token: str = "", api_key: str = "") -> None:
        with self._lock:
            self._credentials = {
                "access_token": str(access_token or ""),
                "api_key": str(api_key or ""),
            }
            should_start = bool(self._config.get("enabled")) and bool(
                self._credentials["access_token"] or self._credentials["api_key"]
            )
        if should_start:
            self.timer.start()

    def trigger_now(self) -> dict[str, Any]:
        self.timer.trigger_now()
        return self.status()

    def shutdown(self) -> None:
        self.timer.stop()

    def status(self) -> dict[str, Any]:
        with self._lock:
            timer_state = self.timer.state
            cache = dict(self._cache)
            config = dict(self._config)
        return {
            **config,
            "enabled": bool(timer_state.enabled),
            "interval_seconds": timer_state.interval_seconds,
            "last_scan_at": timer_state.last_poll_at,
            "next_scan_at": timer_state.next_poll_at,
            "last_error": cache.get("last_error") or timer_state.last_error,
            "error_count": timer_state.error_count,
            "baseline_initialized": bool(cache.get("baseline_initialized")),
            "known_count": len(cache.get("known_keys") or []),
            "last_detected_count": int(cache.get("last_detected_count") or 0),
            "total_enqueued_count": int(cache.get("total_enqueued_count") or 0),
            "logs": list(cache.get("logs") or [])[-50:],
            "timer_state": "running" if self.timer.running else "stopped",
        }

    def _poll(self) -> None:
        with self._lock:
            config = dict(self._config)
            credentials = dict(self._credentials)
            cache = dict(self._cache)
        if not credentials["access_token"] and not credentials["api_key"]:
            raise RuntimeError("CLIENT_DISCOVERY_AUTH_REQUIRED")

        query: dict[str, str] = {
            "platform": str(config.get("platform") or "all"),
            "kinds": ",".join(str(value) for value in config.get("kinds") or ["hot", "new"]),
            "limit": str(max(1, min(50, int(config.get("limit") or config.get("scan_limit") or 24)))),
            "min_episode_count": str(max(0, int(config.get("min_episode_count") or 0))),
        }
        target = f"/v1/discover?{urlencode(query)}"
        data = self._request(target, credentials["access_token"], credentials["api_key"])
        sections = data.get("sections") or []
        items: list[dict[str, Any]] = []
        for section in sections:
            for item in section.get("items") or []:
                if isinstance(item, dict) and item.get("id"):
                    items.append(dict(item))

        known_keys = {str(value) for value in cache.get("known_keys") or []}
        enqueued_keys = {str(value) for value in cache.get("enqueued_keys") or []}
        current_keys = {self._item_key(item) for item in items}
        baseline_initialized = bool(cache.get("baseline_initialized"))
        new_items = [item for item in items if self._item_key(item) not in known_keys]
        if not baseline_initialized:
            new_items = []
        auto_errors: list[str] = []
        enqueue_count = 0
        if bool(config.get("auto_enqueue")):
            budget = max(0, min(50, int(config.get("max_auto_enqueue_per_scan") or 20)))
            for item in new_items:
                key = self._item_key(item)
                if key in enqueued_keys or enqueue_count >= budget:
                    continue
                if not self._matches_filters(item, config):
                    continue
                try:
                    result = self._resolve(item, credentials["access_token"], credentials["api_key"])
                    if not result.get("ok", True):
                        raise RuntimeError(str(result.get("reason") or "CLIENT_RESOLVE_FAILED"))
                    enqueued_keys.add(key)
                    enqueue_count += 1
                except Exception as exc:  # noqa: BLE001 - persisted for UI/backoff context
                    auto_errors.append(f"{key}:{type(exc).__name__}")

        logs = list(cache.get("logs") or [])
        if new_items or auto_errors:
            logs.append(
                {
                    "timestamp": _now(),
                    "level": "error" if auto_errors else "info",
                    "message": (
                        f"discovery found {len(new_items)} new items; auto-enqueue errors: {', '.join(auto_errors)}"
                        if auto_errors
                        else f"discovery found {len(new_items)} new items"
                    ),
                }
            )
        cache = {
            "updated_at": _now(),
            "data": data,
            "last_error": "; ".join(auto_errors),
            "baseline_initialized": True,
            "known_keys": sorted((known_keys | current_keys))[-5000:],
            "enqueued_keys": sorted(enqueued_keys)[-5000:],
            "last_detected_count": len(new_items),
            "total_enqueued_count": int(cache.get("total_enqueued_count") or 0) + enqueue_count,
            "logs": logs[-50:],
        }
        with self._lock:
            self._cache = cache
            _write_json(self._cache_path, cache)

    @staticmethod
    def _item_key(item: dict[str, Any]) -> str:
        return f"{str(item.get('platform') or '')}:{str(item.get('id') or '')}"

    @staticmethod
    def _matches_filters(item: dict[str, Any], config: dict[str, Any]) -> bool:
        haystack = " ".join(
            str(value or "")
            for value in (
                item.get("title"),
                item.get("author"),
                item.get("desc"),
                (item.get("extra") or {}).get("category") if isinstance(item.get("extra"), dict) else "",
            )
        ).lower()
        include = [str(value).strip().lower() for value in config.get("include_keywords") or [] if str(value).strip()]
        exclude = [str(value).strip().lower() for value in config.get("exclude_keywords") or [] if str(value).strip()]
        authors = [str(value).strip().lower() for value in config.get("author_keywords") or [] if str(value).strip()]
        author = str(item.get("author") or "").lower()
        return (
            (not include or any(value in haystack for value in include))
            and not any(value in haystack for value in exclude)
            and (not authors or any(value in author for value in authors))
        )
