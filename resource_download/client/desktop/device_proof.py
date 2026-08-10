"""Central LS-DEVICE-V3 proof builder for the desktop client."""

from __future__ import annotations

import hashlib
from typing import Any

from license_service_client.device import activation_proof, request_proof

from .device_identity import DeviceIdentity, DeviceIdentityManager


AUDIENCE = "rd"


class DeviceProofService:
    def __init__(self, identity_manager: DeviceIdentityManager | None = None, *, audience: str = AUDIENCE) -> None:
        self.identity_manager = identity_manager or DeviceIdentityManager()
        self.audience = audience

    def identity(self) -> DeviceIdentity:
        return self.identity_manager.load_or_create()

    def activation_proof(self, license_key: str) -> dict[str, Any]:
        identity = self.identity()
        return activation_proof(
            identity.private_key,
            audience=self.audience,
            license_key=license_key,
            device_id=identity.device_id,
            public_key_b64=identity.public_key,
            key_algorithm=identity.key_algorithm,
        )

    def request_proof(self, method: str, request_target: str, raw_body: bytes) -> dict[str, Any]:
        identity = self.identity()
        body_sha256 = hashlib.sha256(raw_body).hexdigest().lower()
        return request_proof(
            identity.private_key,
            audience=self.audience,
            method=method.upper(),
            request_target=request_target,
            body_sha256=body_sha256,
            key_algorithm=identity.key_algorithm,
        )

    def request_headers(self, method: str, request_target: str, raw_body: bytes) -> dict[str, str]:
        identity = self.identity()
        proof = self.request_proof(method, request_target, raw_body)
        return {
            "X-Device-Id": identity.device_id,
            "X-Device-Key-Algorithm": identity.key_algorithm,
            "X-Device-Proof-Timestamp": str(proof["timestamp"]),
            "X-Device-Proof-Nonce": str(proof["nonce"]),
            "X-Device-Proof-Signature": str(proof["signature"]),
        }
