"""Client-owned polling timer for ranking/latest/discovery refreshes."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TimerState:
    enabled: bool = False
    interval_seconds: int = 300
    error_count: int = 0
    last_poll_at: str = ""
    last_success_at: str = ""
    last_error: str = ""
    next_poll_at: str = ""


class ClientTimer:
    """Non-reentrant timer with persisted state and exponential backoff."""

    def __init__(
        self,
        poll: Callable[[], Any],
        state_path: str | Path,
        *,
        interval_seconds: int = 300,
        max_backoff_seconds: int = 3600,
    ) -> None:
        self.poll = poll
        self.state_path = Path(state_path).expanduser().resolve()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_backoff_seconds = max(1, int(max_backoff_seconds))
        self.state = self._load()
        self.state.interval_seconds = max(1, int(interval_seconds or self.state.interval_seconds))
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._in_flight = threading.Lock()
        self._thread: threading.Thread | None = None

    def _load(self) -> TimerState:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            return TimerState(**{key: payload[key] for key in asdict(TimerState()) if key in payload})
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return TimerState()

    def _save(self) -> None:
        temp = self.state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(asdict(self.state), ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.state_path)

    def configure(self, *, enabled: bool, interval_seconds: int | None = None) -> TimerState:
        self.state.enabled = bool(enabled)
        if interval_seconds is not None:
            self.state.interval_seconds = max(1, int(interval_seconds))
        self._save()
        if self.state.enabled:
            self.start()
        else:
            self.stop()
        return self.state

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.state.enabled = True
        self._stop.clear()
        self._save()
        self._thread = threading.Thread(target=self._run, name="rd-client-timer", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.state.enabled = False
        self._stop.set()
        self._wake.set()
        self._save()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=5)
        self._thread = None

    def trigger_now(self) -> bool:
        """Request an immediate poll; returns false if one is already running."""
        if not self._in_flight.acquire(blocking=False):
            return False
        try:
            self._poll_once_locked()
        finally:
            self._in_flight.release()
        return True

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def _next_delay(self) -> float:
        if self.state.error_count <= 0:
            return float(self.state.interval_seconds)
        return float(
            min(
                self.max_backoff_seconds,
                self.state.interval_seconds * (2 ** min(self.state.error_count, 8)),
            )
        )

    def poll_once(self) -> bool:
        if not self._in_flight.acquire(blocking=False):
            return False
        try:
            return self._poll_once_locked()
        finally:
            self._in_flight.release()

    def _poll_once_locked(self) -> bool:
        self.state.last_poll_at = _now()
        try:
            self.poll()
        except Exception as exc:  # noqa: BLE001 - error is persisted for UI
            self.state.error_count += 1
            self.state.last_error = type(exc).__name__
            delay = min(
                self.max_backoff_seconds,
                self.state.interval_seconds * (2 ** min(self.state.error_count, 8)),
            )
            self.state.next_poll_at = datetime.fromtimestamp(
                time.time() + delay, timezone.utc
            ).isoformat()
            self._save()
            return False
        self.state.error_count = 0
        self.state.last_error = ""
        self.state.last_success_at = self.state.last_poll_at
        self.state.next_poll_at = datetime.fromtimestamp(
            time.time() + self.state.interval_seconds, timezone.utc
        ).isoformat()
        self._save()
        return True

    def _run(self) -> None:
        while not self._stop.is_set():
            self._wake.wait(timeout=self._next_delay())
            self._wake.clear()
            if self._stop.is_set() or not self.state.enabled:
                continue
            self.poll_once()
