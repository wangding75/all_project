"""Short-lived, process-local idempotency records for Download Resolve.

RD is intentionally a single-worker service.  A process-local store therefore
closes the check/resolve/quota race without introducing a second durable secret
store. Only the sanitized resolve response is retained, never request credentials.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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

    def begin(self, scope: str, key: str, fingerprint: str, *, db=None) -> tuple[bool, _Entry]:
        now = time.monotonic()
        lookup = (scope, key)
        with self._lock:
            self._prune(now)
            entry = self._entries.get(lookup)
            if entry is not None:
                if entry.fingerprint != fingerprint:
                    raise IdempotencyConflict("IDEMPOTENCY_CONFLICT")
                return False, entry
            if db is not None:
                from app.models_orm import IdempotencyRecord

                now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
                row = (
                    db.query(IdempotencyRecord)
                    .filter(
                        IdempotencyRecord.scope == scope,
                        IdempotencyRecord.key == key,
                    )
                    .first()
                )
                if row is not None and row.expires_at <= now_utc:
                    db.delete(row)
                    db.commit()
                    row = None
                if row is not None:
                    if row.fingerprint != fingerprint:
                        raise IdempotencyConflict("IDEMPOTENCY_CONFLICT")
                    durable_response = None
                    if row.response_json:
                        try:
                            decoded = json.loads(row.response_json)
                            if isinstance(decoded, dict):
                                durable_response = decoded
                        except (TypeError, ValueError):
                            durable_response = None
                    entry = _Entry(
                        fingerprint=fingerprint,
                        expires_at=time.monotonic() + self.ttl_seconds,
                        response=durable_response,
                    )
                    self._entries[lookup] = entry
                    return False, entry
                db.add(
                    IdempotencyRecord(
                        scope=scope,
                        key=key,
                        fingerprint=fingerprint,
                        expires_at=now_utc + timedelta(seconds=self.ttl_seconds),
                    )
                )
                db.commit()
            entry = _Entry(fingerprint=fingerprint, expires_at=now + self.ttl_seconds)
            self._entries[lookup] = entry
            return True, entry

    def complete(self, scope: str, key: str, entry: _Entry, response: dict[str, Any], *, db=None) -> None:
        with self._lock:
            current = self._entries.get((scope, key))
            if current is not entry:
                return
            entry.response = response
            entry.expires_at = time.monotonic() + self.ttl_seconds
            if db is not None:
                from app.models_orm import IdempotencyRecord

                row = (
                    db.query(IdempotencyRecord)
                    .filter(
                        IdempotencyRecord.scope == scope,
                        IdempotencyRecord.key == key,
                        IdempotencyRecord.fingerprint == entry.fingerprint,
                    )
                    .first()
                )
                if row is not None:
                    row.response_json = json.dumps(response, ensure_ascii=False, separators=(",", ":"))
                    row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
                        seconds=self.ttl_seconds
                    )
                    db.commit()
            entry.event.set()

    def fail(self, scope: str, key: str, entry: _Entry, *, db=None) -> None:
        with self._lock:
            current = self._entries.get((scope, key))
            if current is entry:
                self._entries.pop((scope, key), None)
                if db is not None:
                    from app.models_orm import IdempotencyRecord

                    row = (
                        db.query(IdempotencyRecord)
                        .filter(
                            IdempotencyRecord.scope == scope,
                            IdempotencyRecord.key == key,
                            IdempotencyRecord.fingerprint == entry.fingerprint,
                        )
                        .first()
                    )
                    if row is not None:
                        db.delete(row)
                        db.commit()
                entry.event.set()

    def wait(self, entry: _Entry) -> dict[str, Any] | None:
        if entry.response is not None:
            return entry.response
        if not entry.event.wait(timeout=IDEMPOTENCY_WAIT_SECONDS):
            raise IdempotencyInProgress("IDEMPOTENCY_IN_PROGRESS")
        return entry.response


idempotency_store = IdempotencyStore()
