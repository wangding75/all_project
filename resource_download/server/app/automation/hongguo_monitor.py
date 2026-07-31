"""红果上新识别与自动入队。

首次扫描只建立当前资源基线，后续仅把新出现的 series_id 识别为上新，
避免启用自动下载时误把已有列表批量加入队列。
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.auth import Identity
from app.config import Settings, get_settings
from app.jobs import JobManager, get_job_manager
from app.models import (
    DiscoverItem,
    HongguoMonitorConfig,
    HongguoMonitorLog,
    HongguoMonitorStatus,
    JobStatus,
    PlatformName,
)
from platforms.registry import get_platform


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _identity_key(identity: Identity) -> str:
    if identity.kind == "user" and identity.user_id is not None:
        return f"user:{identity.user_id}"
    return "ops"


class HongguoMonitorService:
    def __init__(
        self,
        settings: Settings | None = None,
        manager: JobManager | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.manager = manager or get_job_manager()
        self.path = self.settings.data_dir / "automation" / "hongguo_monitors.json"
        self._policies: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                self._policies = {
                    str(key): value
                    for key, value in payload.items()
                    if isinstance(value, dict)
                }
        except Exception:
            corrupted = self.path.with_suffix(self.path.suffix + ".corrupted")
            try:
                os.replace(self.path, corrupted)
            except OSError:
                pass

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(self._policies, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temp, self.path)

    @staticmethod
    def _default_policy(identity: Identity) -> dict[str, Any]:
        config = HongguoMonitorConfig()
        return {
            **config.model_dump(),
            "owner_kind": "user" if identity.kind == "user" else "ops",
            "owner_user_id": identity.user_id if identity.kind == "user" else None,
            "baseline_initialized": False,
            "known_ids": [],
            "last_scan_at": "",
            "last_success_at": "",
            "last_error": "",
            "last_detected_count": 0,
            "total_detected_count": 0,
            "total_enqueued_count": 0,
            "recent_items": [],
            "logs": [],
        }

    @staticmethod
    def _status(policy: dict[str, Any]) -> HongguoMonitorStatus:
        recent = []
        for item in policy.get("recent_items") or []:
            try:
                recent.append(DiscoverItem(**item))
            except Exception:
                continue
        logs = []
        for entry in policy.get("logs") or []:
            try:
                logs.append(HongguoMonitorLog(**entry))
            except Exception:
                continue
        config_values = {}
        for key, field in HongguoMonitorConfig.model_fields.items():
            config_values[key] = (
                policy[key]
                if key in policy
                else field.get_default(call_default_factory=True)
            )
        next_scan_at = ""
        if config_values.get("enabled"):
            try:
                last = datetime.fromisoformat(str(policy.get("last_scan_at") or ""))
            except ValueError:
                last = datetime.now(timezone.utc)
            next_scan_at = (
                last + timedelta(seconds=int(config_values.get("interval_seconds") or 60))
            ).isoformat()
        return HongguoMonitorStatus(
            **config_values,
            baseline_initialized=bool(policy.get("baseline_initialized")),
            known_count=len(policy.get("known_ids") or []),
            last_scan_at=str(policy.get("last_scan_at") or ""),
            last_success_at=str(policy.get("last_success_at") or ""),
            last_error=str(policy.get("last_error") or ""),
            last_detected_count=int(policy.get("last_detected_count") or 0),
            total_detected_count=int(policy.get("total_detected_count") or 0),
            total_enqueued_count=int(policy.get("total_enqueued_count") or 0),
            next_scan_at=next_scan_at,
            recent_items=recent,
            logs=logs[-20:],
        )

    @staticmethod
    def _append_log(
        policy: dict[str, Any],
        message: str,
        *,
        level: str = "info",
        detected: int = 0,
        enqueued: int = 0,
    ) -> None:
        logs = list(policy.get("logs") or [])
        logs.append(
            {
                "timestamp": _utc_now(),
                "level": level,
                "message": message,
                "detected": detected,
                "enqueued": enqueued,
            }
        )
        policy["logs"] = logs[-200:]

    @staticmethod
    def _matches_rules(policy: dict[str, Any], item: DiscoverItem) -> bool:
        text = " ".join(
            [
                str(item.title or ""),
                str(item.desc or ""),
                str(item.extra.get("category") or ""),
            ]
        ).lower()
        author = str(item.author or "").lower()
        include = [
            str(value).strip().lower()
            for value in policy.get("include_keywords") or []
            if str(value).strip()
        ]
        exclude = [
            str(value).strip().lower()
            for value in policy.get("exclude_keywords") or []
            if str(value).strip()
        ]
        authors = [
            str(value).strip().lower()
            for value in policy.get("author_keywords") or []
            if str(value).strip()
        ]
        if include and not any(keyword in text for keyword in include):
            return False
        if exclude and any(keyword in text for keyword in exclude):
            return False
        if authors and not any(keyword in author for keyword in authors):
            return False
        minimum = int(policy.get("min_episode_count") or 0)
        if minimum:
            try:
                episode_count = int(item.extra.get("episode_count") or 0)
            except (TypeError, ValueError):
                episode_count = 0
            if episode_count < minimum:
                return False
        return True

    async def get_status(self, identity: Identity) -> HongguoMonitorStatus:
        key = _identity_key(identity)
        async with self._lock:
            policy = self._policies.setdefault(key, self._default_policy(identity))
            return self._status(policy)

    async def configure(
        self,
        identity: Identity,
        config: HongguoMonitorConfig,
    ) -> HongguoMonitorStatus:
        key = _identity_key(identity)
        async with self._lock:
            policy = self._policies.setdefault(key, self._default_policy(identity))
            values = config.model_dump()
            for field_name in ("include_keywords", "exclude_keywords", "author_keywords"):
                values[field_name] = list(
                    dict.fromkeys(
                        str(value).strip()
                        for value in values.get(field_name) or []
                        if str(value).strip()
                    )
                )[:20]
            policy.update(values)
            policy["owner_kind"] = "user" if identity.kind == "user" else "ops"
            policy["owner_user_id"] = identity.user_id if identity.kind == "user" else None
            await asyncio.to_thread(self._persist)
            result = self._status(policy)
        if config.enabled:
            self.start()
        return result

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop_event.clear()
            self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def scan_now(self, identity: Identity) -> HongguoMonitorStatus:
        return await self._scan_key(_identity_key(identity))

    async def _scan_key(self, key: str) -> HongguoMonitorStatus:
        async with self._lock:
            policy = self._policies.get(key)
            if policy is None:
                identity = Identity(kind="api_key", is_ops=True)
                policy = self._default_policy(identity)
                self._policies[key] = policy
            snapshot = dict(policy)
            snapshot["known_ids"] = list(policy.get("known_ids") or [])

        now = _utc_now()
        try:
            platform = get_platform(PlatformName.hongguo)
            rows = await platform.discover(
                "new",
                limit=int(snapshot.get("scan_limit") or 50),
            )
            known = set(str(value) for value in snapshot.get("known_ids") or [])
            baseline_initialized = bool(snapshot.get("baseline_initialized"))
            detected_all = [
                item for item in rows if baseline_initialized and str(item.id) not in known
            ]
            detected = [
                item for item in detected_all if self._matches_rules(snapshot, item)
            ]
            known.update(str(item.id) for item in rows)
            enqueued = 0
            item_errors: list[str] = []
            failed_ids: set[str] = set()
            if snapshot.get("auto_enqueue"):
                enqueue_limit = int(snapshot.get("max_auto_enqueue_per_scan") or 20)
                for item in detected[:enqueue_limit]:
                    try:
                        if await self._enqueue_item(snapshot, item):
                            enqueued += 1
                    except Exception as exc:  # noqa: BLE001
                        item_errors.append(f"{item.title}: {exc}")
                        failed_ids.add(str(item.id))
            known.difference_update(failed_ids)

            async with self._lock:
                policy = self._policies[key]
                policy["baseline_initialized"] = True
                policy["known_ids"] = list(known)[-1000:]
                policy["last_scan_at"] = now
                policy["last_success_at"] = now
                policy["last_error"] = "；".join(item_errors[:3])
                policy["last_detected_count"] = len(detected)
                policy["total_detected_count"] = int(
                    policy.get("total_detected_count") or 0
                ) + len(detected)
                policy["total_enqueued_count"] = int(
                    policy.get("total_enqueued_count") or 0
                ) + enqueued
                policy["recent_items"] = [
                    item.model_dump(mode="json") for item in detected[:20]
                ]
                if not baseline_initialized:
                    self._append_log(
                        policy,
                        f"已建立上新基线，共记录 {len(rows)} 条资源",
                    )
                else:
                    filtered_count = len(detected_all) - len(detected)
                    message = (
                        f"扫描完成：发现 {len(detected_all)} 条新增，"
                        f"规则命中 {len(detected)} 条，入队 {enqueued} 条"
                    )
                    if filtered_count:
                        message += f"，过滤 {filtered_count} 条"
                    if item_errors:
                        message += f"，失败 {len(item_errors)} 条"
                    self._append_log(
                        policy,
                        message,
                        level="warning" if item_errors else "info",
                        detected=len(detected),
                        enqueued=enqueued,
                    )
                await asyncio.to_thread(self._persist)
                return self._status(policy)
        except Exception as exc:
            async with self._lock:
                policy = self._policies[key]
                policy["last_scan_at"] = now
                policy["last_error"] = str(exc)
                self._append_log(
                    policy,
                    f"扫描失败：{exc}",
                    level="error",
                )
                await asyncio.to_thread(self._persist)
                return self._status(policy)

    async def _enqueue_item(
        self,
        policy: dict[str, Any],
        item: DiscoverItem,
    ) -> bool:
        owner_kind = str(policy.get("owner_kind") or "ops")
        owner_user_id = policy.get("owner_user_id")
        identity = Identity(
            kind="user" if owner_kind == "user" else "api_key",
            user_id=int(owner_user_id) if owner_user_id is not None else None,
            is_ops=owner_kind != "user",
        )
        existing, _ = await self.manager.list_jobs_for(
            identity,
            page=1,
            page_size=1000,
        )
        if any(
            job.platform == PlatformName.hongguo
            and job.item_id == str(item.id)
            and job.status != JobStatus.cancelled
            for job in existing
        ):
            return False

        db = None
        try:
            if identity.kind == "user":
                from datetime import datetime

                from app.db import SessionLocal
                from app.models_orm import User
                from app.quota import check_job_quota, increment_job_quota

                db = SessionLocal()
                user = db.query(User).filter(User.id == identity.user_id).first()
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                if (
                    user is None
                    or not user.is_active
                    or user.vip_expires_at is None
                    or user.vip_expires_at <= now
                ):
                    raise RuntimeError("VIP 已失效，自动入队已跳过")
                check_job_quota(identity, db)

            await self.manager.create_job(
                platform=PlatformName.hongguo,
                item_id=str(item.id),
                range_spec="all",
                options={
                    "title": item.title,
                    "quality": str(policy.get("quality") or "1080p"),
                    "concurrency": int(policy.get("concurrency") or 2),
                    "download_cover": bool(policy.get("download_cover")),
                    "download_desc": bool(policy.get("download_desc")),
                    "source": "hongguo_new_monitor",
                },
                max_active=self.settings.max_queued_jobs,
                owner_user_id=identity.user_id,
                owner_kind="user" if identity.kind == "user" else "ops",
            )
            if identity.kind == "user" and db is not None:
                increment_job_quota(identity, db)
            return True
        finally:
            if db is not None:
                db.close()

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            now = datetime.now(timezone.utc)
            async with self._lock:
                due_keys = []
                for key, policy in self._policies.items():
                    if not policy.get("enabled"):
                        continue
                    last_raw = str(policy.get("last_scan_at") or "")
                    try:
                        last = datetime.fromisoformat(last_raw)
                    except ValueError:
                        last = datetime.fromtimestamp(0, tz=timezone.utc)
                    interval = int(policy.get("interval_seconds") or 60)
                    if (now - last).total_seconds() >= interval:
                        due_keys.append(key)
            for key in due_keys:
                if self._stop_event.is_set():
                    break
                await self._scan_key(key)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=5)
            except asyncio.TimeoutError:
                pass


_service: HongguoMonitorService | None = None


def get_hongguo_monitor_service() -> HongguoMonitorService:
    global _service
    if _service is None:
        _service = HongguoMonitorService()
    return _service
