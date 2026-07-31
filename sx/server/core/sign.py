import hashlib
import hmac
from fastapi import HTTPException


def verify_client_sign(card_key: str, device_id: str, sign: str, app_secret: str):
    """
    校验客户端请求签名
    规则：MD5(card_key + device_id + app_secret).upper()
    """
    raw = card_key + device_id + app_secret
    expected = hashlib.md5(raw.encode()).hexdigest().upper()
    if not hmac.compare_digest(sign.upper(), expected):
        raise HTTPException(status_code=401, detail="签名验证失败")
