"""One desktop HTTP boundary; protected requests are signed here only."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from .device_proof import DeviceProofService


_PROTECTED_JOB_RETRY = re.compile(r"^/v1/jobs/[^/]+/retry$")
_PROTECTED_JOB_PATH = re.compile(r"^/v1/jobs(?:/.*)?$")
_PROTECTED_FILE_PATH = re.compile(r"^/v1/files(?:/.*)?$")
_PROTECTED_DOWNLOAD_PATH = re.compile(r"^/v1/downloads(?:/.*)?$")
_PROTECTED_CONTENT_PATHS = {
    "/v1/search",
    "/v1/detail",
    "/v1/discover",
    "/v1/batch/resolve",
    "/v1/image/recognize",
    "/v1/hongguo/people",
    "/v1/license/status",
    "/v1/resolve",
}
_RETRYABLE_HTTP = {408, 425, 429, 500, 502, 503, 504}
_KNOWN_LICENSE_REASONS = {
    "DEVICE_PROOF_REQUIRED",
    "DEVICE_PROOF_INVALID",
    "INVALID_DEVICE_PROOF",
    "DEVICE_PROOF_EXPIRED",
    "DEVICE_PROOF_REPLAYED",
    "DEVICE_NOT_ACTIVATED",
    "DEVICE_REVOKED",
    "LICENSE_EXPIRED",
    "LICENSE_REVOKED",
    "DEVICE_LIMIT_REACHED",
    "INVALID_KEY",
    "LICENSE_SERVICE_UNAVAILABLE",
    "PLAN_ENTITLEMENT_INVALID",
}


def is_protected_endpoint(method: str, request_target: str) -> bool:
    """Exact RD client scope frozen by the current server guard."""
    parsed = urllib.parse.urlsplit(request_target)
    path = parsed.path
    method = method.upper()
    if (
        _PROTECTED_JOB_PATH.fullmatch(path)
        or _PROTECTED_FILE_PATH.fullmatch(path)
        or _PROTECTED_DOWNLOAD_PATH.fullmatch(path)
    ):
        return True
    if path in _PROTECTED_CONTENT_PATHS:
        return True
    return path.startswith("/v1/automation/hongguo-new")


def normalize_reason(status_code: int, detail: Any) -> str:
    reason = str(detail or "").strip()
    if reason == "INVALID_DEVICE_PROOF":
        reason = "DEVICE_PROOF_INVALID"
    if status_code == 503 and reason not in {"LICENSE_SERVICE_UNAVAILABLE", "LICENSE_SERVICE_TIMEOUT"}:
        return "LICENSE_SERVICE_UNAVAILABLE"
    return reason or ("LICENSE_SERVICE_UNAVAILABLE" if status_code == 503 else f"HTTP_{status_code}")


class DesktopHttpError(RuntimeError):
    def __init__(self, status_code: int, reason: str) -> None:
        super().__init__(reason)
        self.status_code = status_code
        self.reason = reason


BodyFactory = bytes | bytearray | str | Callable[[], bytes]


class DesktopHttpClient:
    def __init__(self, api_base: str, proof_service: DeviceProofService, *, max_retries: int = 1) -> None:
        self.api_base = api_base.rstrip("/")
        self.proof_service = proof_service
        self.max_retries = max(0, int(max_retries))

    @staticmethod
    def _raw_body(body: bytes | bytearray | str) -> bytes:
        if isinstance(body, bytes):
            return body
        if isinstance(body, bytearray):
            return bytes(body)
        if isinstance(body, str):
            return body.encode("utf-8")
        raise TypeError("desktop HTTP body must already be serialized bytes or UTF-8 text")

    @staticmethod
    def _error_from_http(exc: urllib.error.HTTPError) -> DesktopHttpError:
        detail: Any = ""
        try:
            payload = json.loads(exc.read().decode("utf-8", errors="replace"))
            detail = payload.get("detail") if isinstance(payload, dict) else payload
        except Exception:  # noqa: BLE001 - stable status mapping below
            detail = ""
        if isinstance(detail, list):
            detail = "HTTP request rejected"
        return DesktopHttpError(exc.code, normalize_reason(exc.code, detail))

    def request_json(
        self,
        method: str,
        request_target: str,
        body: BodyFactory = b"",
        *,
        access_token: str = "",
        api_key: str = "",
        idempotency_key: str = "",
        protected: bool | None = None,
    ) -> Any:
        parsed = urllib.parse.urlsplit(request_target)
        if not request_target.startswith("/") or request_target.startswith("//") or not parsed.path:
            raise ValueError("request target must be an RD path plus optional query")
        method = method.upper()
        protected = is_protected_endpoint(method, request_target) if protected is None else protected
        url = f"{self.api_base}{request_target}"

        for attempt in range(self.max_retries + 1):
            raw_body = self._raw_body(body() if callable(body) else body)
            headers = {"Content-Type": "application/json"}
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            elif api_key:
                headers["X-API-Key"] = api_key
            if idempotency_key:
                headers["Idempotency-Key"] = idempotency_key
            if protected:
                # This call is intentionally inside the retry loop: every retry gets
                # a fresh timestamp/nonce/signature over this exact raw body.
                headers.update(self.proof_service.request_headers(method, request_target, raw_body))
            request = urllib.request.Request(url, data=raw_body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    content = response.read()
                if not content:
                    return {}
                return json.loads(content.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                error = self._error_from_http(exc)
                if exc.code in _RETRYABLE_HTTP and attempt < self.max_retries:
                    continue
                raise error from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt < self.max_retries:
                    continue
                raise DesktopHttpError(503, "CLIENT_NETWORK_UNAVAILABLE") from exc

        raise DesktopHttpError(503, "CLIENT_NETWORK_UNAVAILABLE")
