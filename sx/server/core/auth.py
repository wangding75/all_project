import hashlib
import hmac as _hmac
import time
import json
import base64
from config import SERVER_SECRET, TOKEN_CLOCK_SKEW_SEC


def _b64_encode(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")


def _b64_decode(data: str) -> str:
    padded = data + "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode()


def _sign_payload(payload_b64: str) -> str:
    return _hmac.new(
        SERVER_SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()


def create_token(card_key: str, device_id: str, expire_at: int) -> str:
    """
    签发 Token = base64url(payload).hmac_signature
    payload = { card_key, device_id, expire_at, issued_at }
    """
    payload = {
        "card_key":  card_key,
        "device_id": device_id,
        "expire_at": expire_at,
        "issued_at": int(time.time() * 1000)
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

        # 验签（防时序攻击）
        expected_sig = _sign_payload(payload_b64)
        if not _hmac.compare_digest(sig, expected_sig):
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
