"""Persistent LS-DEVICE-V3 identity for the Windows desktop client.

The private key never leaves this module and is protected with the current
Windows user's DPAPI.  The storage interface is deliberately small so the
same proof layer can be tested without touching a real user profile.
"""

from __future__ import annotations

import copy
import ctypes
from ctypes import wintypes
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from license_service_client.device import derive_device_id, generate_device_identity
from license_service_client.signing import ED25519, b64u_encode, private_key


class DeviceIdentityError(RuntimeError):
    """A local device identity cannot safely be used."""

    code = "DEVICE_IDENTITY_INVALID"


class DeviceIdentityInvalid(DeviceIdentityError):
    code = "DEVICE_IDENTITY_INVALID"


class DeviceIdentityStorageUnavailable(DeviceIdentityError):
    code = "DEVICE_IDENTITY_STORAGE_UNAVAILABLE"


class IdentityStore(Protocol):
    def load(self) -> dict[str, Any] | None: ...

    def save(self, payload: dict[str, Any]) -> None: ...

    def delete(self) -> None: ...


@dataclass(frozen=True)
class DeviceIdentity:
    device_id: str
    key_algorithm: str
    public_key: str
    # repr=False prevents accidental key disclosure in test failures/logging.
    private_key: str = field(repr=False)


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _dpapi_protect(value: bytes) -> bytes:
    if sys.platform != "win32":
        raise DeviceIdentityStorageUnavailable("Windows DPAPI is unavailable")
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    source = ctypes.create_string_buffer(value)
    source_blob = _DATA_BLOB(len(value), ctypes.cast(source, ctypes.POINTER(ctypes.c_byte)))
    protected_blob = _DATA_BLOB()
    description = ctypes.create_unicode_buffer("ResourceDownloader Device Identity")
    ok = crypt32.CryptProtectData(
        ctypes.byref(source_blob),
        ctypes.byref(description),
        None,
        None,
        None,
        0,
        ctypes.byref(protected_blob),
    )
    if not ok:
        raise DeviceIdentityStorageUnavailable("Windows user security storage rejected the identity")
    try:
        return ctypes.string_at(protected_blob.pbData, protected_blob.cbData)
    finally:
        kernel32.LocalFree(protected_blob.pbData)


def _dpapi_unprotect(value: bytes) -> bytes:
    if sys.platform != "win32":
        raise DeviceIdentityStorageUnavailable("Windows DPAPI is unavailable")
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    source = ctypes.create_string_buffer(value)
    source_blob = _DATA_BLOB(len(value), ctypes.cast(source, ctypes.POINTER(ctypes.c_byte)))
    clear_blob = _DATA_BLOB()
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(source_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(clear_blob),
    )
    if not ok:
        raise DeviceIdentityInvalid("Windows user security storage cannot decrypt the identity")
    try:
        return ctypes.string_at(clear_blob.pbData, clear_blob.cbData)
    finally:
        kernel32.LocalFree(clear_blob.pbData)


def default_identity_path() -> Path:
    app_data = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / ".resource-downloader"))
    return app_data / "ResourceDownloader" / "device_identity.dpapi"


class WindowsDpapiIdentityStore:
    """User-scoped DPAPI store; the project directory is never used."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = (path or default_identity_path()).expanduser()

    def load(self) -> dict[str, Any] | None:
        if not self.path.is_file():
            return None
        try:
            clear = _dpapi_unprotect(self.path.read_bytes())
            value = json.loads(clear.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError("identity payload is not an object")
            return value
        except DeviceIdentityError:
            raise
        except Exception as exc:  # noqa: BLE001 - convert all corruption to a stable local state
            raise DeviceIdentityInvalid("stored device identity is corrupted") from exc

    def save(self, payload: dict[str, Any]) -> None:
        try:
            clear = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
            protected = _dpapi_protect(clear)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            with temporary.open("wb") as handle:
                handle.write(protected)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(self.path)
        except DeviceIdentityError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DeviceIdentityStorageUnavailable("cannot save device identity in Windows user storage") from exc

    def delete(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as exc:
            raise DeviceIdentityStorageUnavailable("cannot reset device identity") from exc


class MemoryIdentityStore:
    """Non-persistent test store; never used by the desktop runtime."""

    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self.payload = copy.deepcopy(payload)

    def load(self) -> dict[str, Any] | None:
        return copy.deepcopy(self.payload)

    def save(self, payload: dict[str, Any]) -> None:
        self.payload = copy.deepcopy(payload)

    def delete(self) -> None:
        self.payload = None


class DeviceIdentityManager:
    """Load, validate, generate and explicitly reset one stable identity."""

    def __init__(self, store: IdentityStore | None = None) -> None:
        self.store = store or WindowsDpapiIdentityStore()

    @staticmethod
    def _new_identity() -> DeviceIdentity:
        device_id, private, public = generate_device_identity()
        return DeviceIdentity(device_id=device_id, key_algorithm=ED25519, public_key=public, private_key=private)

    @staticmethod
    def _validate(payload: dict[str, Any]) -> DeviceIdentity:
        try:
            if int(payload.get("version", 0)) != 1:
                raise ValueError("unsupported identity version")
            algorithm = str(payload["key_algorithm"])
            private = str(payload["private_key"])
            public = str(payload["public_key"])
            device_id = str(payload["device_id"])
            if algorithm != ED25519 or not private or not public or not device_id:
                raise ValueError("unsupported identity fields")
            key = private_key(private)
            derived_public = b64u_encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))
            if derived_public != public:
                raise ValueError("private/public key mismatch")
            if derive_device_id(public, algorithm) != device_id:
                raise ValueError("device id mismatch")
            return DeviceIdentity(device_id=device_id, key_algorithm=algorithm, public_key=public, private_key=private)
        except Exception as exc:  # noqa: BLE001 - no silent identity replacement
            if isinstance(exc, DeviceIdentityInvalid):
                raise
            raise DeviceIdentityInvalid("stored device identity failed validation") from exc

    def load_or_create(self) -> DeviceIdentity:
        payload = self.store.load()
        if payload is None:
            identity = self._new_identity()
            self.store.save(
                {
                    "version": 1,
                    "key_algorithm": identity.key_algorithm,
                    "device_id": identity.device_id,
                    "public_key": identity.public_key,
                    "private_key": identity.private_key,
                }
            )
            return identity
        return self._validate(payload)

    def reset(self) -> DeviceIdentity:
        """Delete only after an explicit user action, then create a new identity."""
        self.store.delete()
        return self.load_or_create()
