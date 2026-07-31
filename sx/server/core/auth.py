import hashlib
import hmac as _hmac
import time
import json
import base64
from functools import lru_cache
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from config import (
    ALLOW_LEGACY_TOKEN_MIGRATION,
    LEGACY_TOKEN_SECRET,
    TOKEN_CLOCK_SKEW_SEC,
    TOKEN_PRIVATE_KEY_PEM,
)


def _b64_encode(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")


def _b64_decode(data: str) -> str:
    padded = data + "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode()


@lru_cache(maxsize=1)
def _private_key():
    return serialization.load_pem_private_key(
        TOKEN_PRIVATE_KEY_PEM.encode(), password=None
    )


def _b64_encode_bytes(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64_decode_bytes(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign_payload(payload_b64: str) -> str:
    signature = _private_key().sign(
        payload_b64.encode(),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return _b64_encode_bytes(signature)


def _verify_rsa_signature(payload_b64: str, signature_b64: str) -> bool:
    try:
        _private_key().public_key().verify(
            _b64_decode_bytes(signature_b64),
            payload_b64.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def _verify_legacy_hmac(payload_b64: str, signature: str) -> bool:
    if not ALLOW_LEGACY_TOKEN_MIGRATION:
        return False
    expected = _hmac.new(
        LEGACY_TOKEN_SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()
    return _hmac.compare_digest(signature, expected)


def create_token(card_key: str, device_id: str, expire_at: int) -> str:
    """
    签发 Token = base64url(payload).rsa_signature
    payload = { card_key, device_id, expire_at, issued_at }
    """
    payload = {
        "card_key":  card_key,
        "device_id": device_id,
        "expire_at": expire_at,
        "issued_at": int(time.time() * 1000),
        "token_version": 2,
    }
    payload_b64 = _b64_encode(json.dumps(payload, separators=(',', ':')))
    sig = _sign_payload(payload_b64)
    return f"{payload_b64}.{sig}"


def verify_token(token: str, device_id: str) -> dict | None:
    """
    校验 Token 合法性
    返回 payload dict（含 expire_at）；失败返回 None
    """
    try:
        parts = token.split(".", 1)
        if len(parts) != 2:
            return None
        payload_b64, sig = parts

        # RSA is the current format. Legacy HMAC is accepted only during an
        # explicitly enabled migration window.
        if not (_verify_rsa_signature(payload_b64, sig)
                or _verify_legacy_hmac(payload_b64, sig)):
            return None

        # 解码
        payload = json.loads(_b64_decode(payload_b64))

        # 校验设备绑定
        if payload.get("device_id") != device_id:
            return None

        # 校验过期（-1 = 永久）
        expire_at = payload.get("expire_at", 0)
        if expire_at != -1:
            now_ms = int(time.time() * 1000)
            if now_ms > expire_at + TOKEN_CLOCK_SKEW_SEC * 1000:
                return None

        return payload
    except Exception:
        return None
