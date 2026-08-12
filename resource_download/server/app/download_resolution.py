"""Download Resolve and short-lived proxy tickets.

The module deliberately contains no file-system or server download-record state.  A proxy
ticket only retains the platform request context for a short time so that a
client can retry an already-authorized stream.
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any

from app.models import DownloadDescriptor, DownloadMode, PlatformName


PROXY_TTL_SECONDS = 300


@dataclass(frozen=True)
class ProxyTicket:
    platform: PlatformName
    resource_id: str
    range_spec: str
    options: dict[str, Any]
    upstream_url: str | None
    upstream_headers: dict[str, str]
    expires_at: float


class ProxyTicketStore:
    """Bounded in-memory proxy contexts; no bytes or downloaded files."""

    def __init__(self, *, ttl_seconds: int = PROXY_TTL_SECONDS, max_entries: int = 10_000) -> None:
        self.ttl_seconds = max(30, int(ttl_seconds))
        self.max_entries = max(100, int(max_entries))
        self._items: dict[str, ProxyTicket] = {}
        self._lock = threading.RLock()

    def issue(
        self,
        *,
        platform: PlatformName,
        resource_id: str,
        range_spec: str,
        options: dict[str, Any] | None = None,
        upstream_url: str | None = None,
        upstream_headers: dict[str, str] | None = None,
    ) -> tuple[str, int]:
        now = time.time()
        token = secrets.token_urlsafe(32)
        expires = now + self.ttl_seconds
        with self._lock:
            self._purge(now)
            if len(self._items) >= self.max_entries:
                oldest = min(self._items, key=lambda key: self._items[key].expires_at)
                self._items.pop(oldest, None)
            self._items[token] = ProxyTicket(
                platform=platform,
                resource_id=resource_id,
                range_spec=range_spec,
                options=dict(options or {}),
                upstream_url=upstream_url,
                upstream_headers=dict(upstream_headers or {}),
                expires_at=expires,
            )
        return token, int(expires)

    def get(self, token: str) -> ProxyTicket | None:
        now = time.time()
        with self._lock:
            self._purge(now)
            item = self._items.get(token)
            if item is None or item.expires_at <= now:
                return None
            return item

    def _purge(self, now: float) -> None:
        expired = [key for key, item in self._items.items() if item.expires_at <= now]
        for key in expired:
            self._items.pop(key, None)


proxy_ticket_store = ProxyTicketStore()


def _descriptor_expiry(expires_epoch: int | None) -> str | None:
    if expires_epoch is None:
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(expires_epoch, timezone.utc).isoformat()


async def normalize_platform_resolution(
    *,
    platform: PlatformName,
    resource_id: str,
    title: str,
    media_type: str,
    suggested_filename: str,
    range_spec: str,
    options: dict[str, Any],
    resolved: Any,
) -> list[DownloadDescriptor]:
    """Convert adapter output into safe public descriptors and issue tickets."""

    rows = resolved if isinstance(resolved, list) else [resolved]
    descriptors: list[DownloadDescriptor] = []
    for row in rows:
        if isinstance(row, DownloadDescriptor):
            descriptor = row
            if descriptor.download_mode == DownloadMode.proxy and descriptor.request_token:
                descriptors.append(descriptor)
                continue
            rows_data = descriptor.model_dump(mode="json")
        elif isinstance(row, dict):
            rows_data = dict(row)
        else:
            raise ValueError("platform returned an invalid Download Resolve result")

        mode = DownloadMode(str(rows_data.get("download_mode") or "direct"))
        item_id = str(rows_data.get("resource_id") or resource_id)
        item_title = str(rows_data.get("title") or title or item_id)
        item_media_type = str(rows_data.get("media_type") or media_type or "application/octet-stream")
        item_filename = str(rows_data.get("suggested_filename") or suggested_filename or f"{item_id}.bin")
        url = rows_data.get("url")
        headers = {
            str(key): str(value)
            for key, value in dict(rows_data.get("headers") or {}).items()
            if str(key).lower() not in {"cookie", "authorization", "x-api-key"}
        }
        expires_epoch = rows_data.get("expires_epoch")
        if expires_epoch is None and rows_data.get("expires_at"):
            expires_at = str(rows_data["expires_at"])
        else:
            expires_at = _descriptor_expiry(int(expires_epoch)) if expires_epoch else None

        if mode == DownloadMode.direct:
            descriptor = DownloadDescriptor(
                platform=platform,
                resource_id=item_id,
                title=item_title,
                media_type=item_media_type,
                suggested_filename=item_filename,
                expires_at=expires_at,
                download_mode=mode,
                url=str(url or ""),
                headers=headers,
                size_bytes=rows_data.get("size_bytes") or rows_data.get("size"),
                range_supported=rows_data.get("range_supported"),
                extra=dict(rows_data.get("extra") or {}),
            )
            descriptors.append(descriptor)
            continue

        token, token_expires = proxy_ticket_store.issue(
            platform=platform,
            resource_id=item_id,
            range_spec=range_spec,
            options=options,
            upstream_url=str(url) if url else None,
            upstream_headers=headers,
        )
        descriptor = DownloadDescriptor(
            platform=platform,
            resource_id=item_id,
            title=item_title,
            media_type=item_media_type,
            suggested_filename=item_filename,
            expires_at=expires_at or _descriptor_expiry(token_expires),
            download_mode=DownloadMode.proxy,
            proxy_url=f"/v1/downloads/proxy/{token}",
            request_token=token,
            size_bytes=rows_data.get("size_bytes") or rows_data.get("size"),
            range_supported=rows_data.get("range_supported"),
            extra=dict(rows_data.get("extra") or {}),
        )
        descriptors.append(descriptor)
    if not descriptors:
        raise ValueError("platform returned no downloadable resource")
    return descriptors
