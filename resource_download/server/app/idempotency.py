"""Short-lived, process-local idempotency records for Job creation.

RD is intentionally a single-worker service.  A process-local store therefore
closes the check/create/quota race without introducing a second durable secret
store.  Only the sanitized Job response is retained, never request credentials.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any


IDEMPOTENCY_TTL_SECONDS = 300
IDEMPOTENCY_WAIT_SECONDS = 60


class IdempotencyConflict(ValueError):
    """The same authenticated key was reused with a different payload."""


class IdempotencyInProgress(TimeoutError):
    """The original request did not finish within the bounded wait."""


@dataclass
class _Entry:
    fingerprint: str
    expires_at: float
    event: threading.Event = field(default_factory=threading.Event)
    response: dict[str, Any] | None = None


def request_fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class IdempotencyStore:
    def __init__(self, *, ttl_seconds: int = IDEMPOTENCY_TTL_SECONDS) -> None:
        self.ttl_seconds = max(1, int(ttl_seconds))
        self._lock = threading.RLock()
        self._entries: dict[tuple[str, str], _Entry] = {}

    def _prune(self, now: float) -> None:
        expired = [key for key, entry in self._entries.items() if entry.expires_at <= now]
        for key in expired:
            self._entries.pop(key, None)

    def begin(self, scope: str, key: str, fingerprint: str) -> tuple[bool, _Entry]:
        now = time.monotonic()
        lookup = (scope, key)
        with self._lock:
            self._prune(now)
            entry = self._entries.get(lookup)
            if entry is not None:
                if entry.fingerprint != fingerprint:
                    raise IdempotencyConflict("IDEMPOTENCY_CONFLICT")
                return False, entry
            entry = _Entry(fingerprint=fingerprint, expires_at=now + self.ttl_seconds)
            self._entries[lookup] = entry
            return True, entry

    def complete(self, scope: str, key: str, entry: _Entry, response: dict[str, Any]) -> None:
        with self._lock:
            current = self._entries.get((scope, key))
            if current is not entry:
                return
            entry.response = response
            entry.expires_at = time.monotonic() + self.ttl_seconds
            entry.event.set()

    def fail(self, scope: str, key: str, entry: _Entry) -> None:
        with self._lock:
            current = self._entries.get((scope, key))
            if current is entry:
                self._entries.pop((scope, key), None)
                entry.event.set()

    def wait(self, entry: _Entry) -> dict[str, Any] | None:
        if not entry.event.wait(timeout=IDEMPOTENCY_WAIT_SECONDS):
            raise IdempotencyInProgress("IDEMPOTENCY_IN_PROGRESS")
        return entry.response


idempotency_store = IdempotencyStore()
