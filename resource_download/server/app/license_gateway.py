"""Thin RD adapter around the versioned License Service Server SDK.

This module intentionally owns no License/Device database state.  RD keeps its
own users, jobs and quota in SQLite; License Service remains the only source of
truth for activation and Device License authorization.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

_gateway: "LicenseGateway | None" = None


def _hashed_device_id(device_id: str) -> str:
    return hashlib.sha256(device_id.encode("utf-8")).hexdigest()[:16]


@dataclass
class LicenseGateway:
    """Application-lifetime License Service client and state adapter."""

    client: Any = None
    configured: bool = False
    config_error: str = ""
    cache_ttl_seconds: int = 0
    last_reachable: bool = False
    last_request_id: str = ""
    last_latency_ms: float | None = None

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "LicenseGateway":
        settings = settings or get_settings()
        required = {
            "base_url": settings.license_service_base_url.strip(),
            "key_id": settings.license_service_key_id.strip(),
            "private_key": settings.license_service_private_key.strip(),
            "audience": settings.license_service_audience.strip(),
        }
        if not all(required.values()):
            return cls(
                configured=False,
                config_error="LICENSE_SERVICE_CONFIGURATION_INCOMPLETE",
                cache_ttl_seconds=settings.license_cache_ttl_seconds,
            )
        if required["audience"] != "rd":
            return cls(
                configured=False,
                config_error="LICENSE_SERVICE_AUDIENCE_INVALID",
                cache_ttl_seconds=settings.license_cache_ttl_seconds,
            )

        try:
            from license_service_client import LicenseServerClient, MemoryReplayStore

            replay_store = (
                MemoryReplayStore(max_entries=100_000)
                if settings.license_cache_ttl_seconds > 0
                else None
            )
            verify: bool | str = settings.license_service_verify
            if settings.license_service_ca_bundle.strip():
                verify = settings.license_service_ca_bundle.strip()
            cert: Any = None
            client_cert = settings.license_service_client_cert.strip()
            client_key = settings.license_service_client_key.strip()
            if client_cert and client_key:
                cert = (client_cert, client_key)
            elif client_cert:
                cert = client_cert

            client = LicenseServerClient(
                required["base_url"],
                required["key_id"],
                required["private_key"],
                audience=required["audience"],
                timeout=settings.license_service_timeout,
                verify=verify,
                cert=cert,
                cache_ttl_seconds=settings.license_cache_ttl_seconds,
                replay_store=replay_store,
            )
        except Exception as exc:  # invalid credential/config must fail closed
            logger.error(
                "License SDK initialization failed: error_type=%s",
                type(exc).__name__,
            )
            return cls(
                configured=False,
                config_error="LICENSE_SERVICE_CONFIGURATION_INVALID",
                cache_ttl_seconds=settings.license_cache_ttl_seconds,
            )
        return cls(
            client=client,
            configured=True,
            cache_ttl_seconds=settings.license_cache_ttl_seconds,
        )

    def _record_result(
        self,
        *,
        device_id: str | None,
        result: dict[str, Any],
        started: float,
        request_id: str = "",
    ) -> dict[str, Any]:
        self.last_latency_ms = round((time.perf_counter() - started) * 1000, 2)
        self.last_request_id = request_id
        decision = str(result.get("decision") or "UNKNOWN")
        self.last_reachable = decision != "UNKNOWN"
        logger.info(
            "license_decision=%s license_reason=%s license_source=%s "
            "license_latency_ms=%s license_service_request_id=%s device_id_hash=%s",
            decision,
            str(result.get("reason") or "UNKNOWN"),
            str(result.get("source") or "unknown"),
            self.last_latency_ms,
            request_id or "-",
            _hashed_device_id(device_id) if device_id else "-",
        )
        return result

    @staticmethod
    def _unknown(reason: str) -> dict[str, Any]:
        return {
            "activated": False,
            "reason": reason,
            "decision": "UNKNOWN",
            "source": "fail_closed",
        }

    def activate(self, payload: dict[str, Any], *, request_id: str = "") -> dict[str, Any]:
        """Proxy activation to License Service without touching RD SQLite."""
        started = time.perf_counter()
        device_id = str(payload.get("device_id") or "")
        if self.client is None:
            return self._record_result(
                device_id=device_id,
                result=self._unknown("LICENSE_SERVICE_UNAVAILABLE"),
                started=started,
                request_id=request_id,
            )
        try:
            result = dict(self.client.activate(payload) or {})
            result["decision"] = "ACTIVE" if bool(result.get("activated")) else "INACTIVE"
            result.setdefault("source", "remote")
            return self._record_result(
                device_id=device_id,
                result=result,
                started=started,
                request_id=request_id,
            )
        except httpx.TimeoutException:
            result = self._unknown("LICENSE_SERVICE_TIMEOUT")
        except httpx.RequestError:
            result = self._unknown("LICENSE_SERVICE_UNAVAILABLE")
        except httpx.HTTPStatusError:
            result = self._unknown("LICENSE_SERVICE_REJECTED")
        except Exception as exc:  # never expose SDK/credential internals to clients
            logger.error("License activation failed: error_type=%s", type(exc).__name__)
            result = self._unknown("LICENSE_SERVICE_UNAVAILABLE")
        return self._record_result(
            device_id=device_id,
            result=result,
            started=started,
            request_id=request_id,
        )

    def authorize_request(
        self,
        *,
        device_id: str,
        request_method: str,
        request_target: str,
        raw_body: bytes,
        device_proof: dict[str, Any],
        device_key_algorithm: str,
        request_id: str = "",
    ) -> dict[str, Any]:
        """Check the real RD request using the SDK's V3 transport/caching path."""
        started = time.perf_counter()
        if self.client is None:
            return self._record_result(
                device_id=device_id,
                result=self._unknown("LICENSE_SERVICE_UNAVAILABLE"),
                started=started,
                request_id=request_id,
            )
        try:
            result = dict(
                self.client.check_device_request(
                    device_id=device_id,
                    request_method=request_method,
                    request_target=request_target,
                    raw_body=raw_body,
                    device_proof=device_proof,
                    device_key_algorithm=device_key_algorithm,
                )
                or {}
            )
        except httpx.TimeoutException:
            result = self._unknown("LICENSE_SERVICE_TIMEOUT")
        except httpx.RequestError:
            result = self._unknown("LICENSE_SERVICE_UNAVAILABLE")
        except Exception as exc:  # fail closed and keep SDK internals out of HTTP
            logger.error("License authorization failed: error_type=%s", type(exc).__name__)
            result = self._unknown("LICENSE_SERVICE_UNAVAILABLE")
        result.setdefault("decision", "ACTIVE" if result.get("activated") else "INACTIVE")
        result.setdefault("source", "remote")
        return self._record_result(
            device_id=device_id,
            result=result,
            started=started,
            request_id=request_id,
        )

    def health(self) -> dict[str, Any]:
        return {
            "license_service_configured": self.configured,
            "license_service_reachable": self.last_reachable if self.configured else False,
            "license_cache_ttl_seconds": self.cache_ttl_seconds,
        }

    def close(self) -> None:
        if self.client is not None:
            self.client.close()


def set_license_gateway(gateway: LicenseGateway | None) -> None:
    global _gateway
    _gateway = gateway


def get_license_gateway() -> LicenseGateway:
    global _gateway
    if _gateway is None:
        _gateway = LicenseGateway.from_settings()
    return _gateway


def initialize_license_gateway(settings: Settings | None = None) -> LicenseGateway:
    gateway = LicenseGateway.from_settings(settings)
    set_license_gateway(gateway)
    return gateway


def close_license_gateway() -> None:
    global _gateway
    if _gateway is not None:
        _gateway.close()
    _gateway = None
