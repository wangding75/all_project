from dotenv import load_dotenv
import os
import sys
import warnings
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

load_dotenv()

_ENV = (os.getenv("SX_ENV") or os.getenv("ENV") or "dev").lower()
_DEFAULT_CLIENT_SIGN_SECRET = "sx_dev_secret_2026"
_DEFAULT_TOKEN_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDE5DQsoaygfPE2
GDShzZZQAD0sdtB40yfBKZqf8sykyGwoJFNlsSWMKAVKmFTQLsMUFrHL73ImmZ0p
4TgrV6MtI+QOTxqDL86Wx4Z7XE/CDDMtKG9fwOefqJl/+K2heQTyrol/6Al2bdId
uio1pRCxPD200bFfXorQZg5+U9oyDK1E/aumF9ydYGyturjbqXukHnPTzXyOCfdG
FAMEsGKH7Ejt4rsyPxQ2EAUsuTXeFB1MO3deDDKNJYKUtxhfAaFNiDXc3QaYZgQx
DJdhrVCELNbjhxfzyMoT47hPapxrh+dEM4B/MdfD9RK726eckErOOmEOENNvmCY1
Wb8C6sz9AgMBAAECggEAAcLyPeKlvbsrGUsher/GdClxt//JdltFRB161wAqw9/7
Kmdwy5HIfowucpq8Si8w6vFtCSBiSrrIb4Mmp9SdOXPUatWwV14fy1+LnMztoGnQ
MhDmNjAZTRIKwDIEXlPL2d6lN5y8K5q97NV+jS5Qi5VjY/EVqinECitE6UJsyv0o
Bu8cA5L87tEs43+n5N+/6rM6zku0JwPGBuDvhPg7M0CCDIHy2uepw9xpvllzRyCK
mX6cm6+VOn8oWxlzuWG8olos1WbEfXkDyiUHq4nfbOrCL++FYmAM7jXWKCJHfUsO
oPudH7wMv7+cKdJDpVWSCHRIbbe/ZSlTMGXE10sxzQKBgQDmaGK6kVVadie5UY2V
5S8SkqVu8rMlzKLGY8xCWe5rlQtjeDV0nGNRwY1sO2qXJDNkYzcFCxog2ilt2WLm
zvysg6Yq8aBuDYZBAkImoCeEA3Or+Yp1hmKgmOD0CR3xzRAqszJGqZr2BVSNmcIT
/gCJw+ph9koi8TvgkM7jNGSwBwKBgQDawskZiHYGiBoe6KxPaVErT0MYTCQvcBSB
9FfhBIR5SN90hBYMubmz0W4/1Pz9p8O782dd9uHzrwg5lgJ6jJ3DaZ7ebICb7jN6
MvHQ/7ibZyyIe4GEDixlU/aG3uxW+erj/VL4oIm3xb9EU4qZwv84g/08p6KxQs/3
dwHzELpR2wKBgBbZNSkxLlipLOlIuBSsRI2/8x3cfX17HI016lSOHIGYpyd3DT4C
ICtEWWTpQ3m3gk0rNZKPdkjZuZAGJbOjxRTKfVj22yTuvGiH881mxmRl/zuHpH5h
FDi+0FgC63BGGJtTZ+HwAcjx4F+mZsOaxazju8N5LALpDzoGwi1vzahTAoGBAMtV
L7xW1XU+viCqnbZ2Kqb51mBYLW4WXElqRuB05XkiHejb+O69FnmoGTSlkL1oWQty
s0podh6dOyTjZMxptR30J2GQMn49CoXzokZj2kA/xunY+ko3LlbEkylLPRue0hA1
3xAPj9JLsHset34x/C2YqSHeot7mPg1DBYHas4PvAoGARxCTZ5Lda1LdgFga7N/F
k/QT50DpB9qoSToSBlzjOVeG8dJ5zS8DSPxIYfVh3M+idxhp4TihtGWKZHwedTa7
W7perWe8XskgJn64emhdKbzST1UzarG+ZQNeSEg9fcSGeDK0n//NMfAaTwI6zvEM
VmRTSW2if+jfexASymKpE/Y=
-----END PRIVATE KEY-----"""

# CLIENT_SIGN_SECRET is embedded in the app and authenticates activation
# requests only. TOKEN_PRIVATE_KEY_PEM never leaves the server.
CLIENT_SIGN_SECRET = os.getenv(
    "CLIENT_SIGN_SECRET",
    os.getenv("SERVER_SECRET", _DEFAULT_CLIENT_SIGN_SECRET),
)
TOKEN_PRIVATE_KEY_PEM = os.getenv(
    "TOKEN_PRIVATE_KEY_PEM", _DEFAULT_TOKEN_PRIVATE_KEY
).replace("\\n", "\n")

# Temporary migration support for tokens issued before asymmetric signing.
LEGACY_TOKEN_SECRET = os.getenv(
    "LEGACY_TOKEN_SECRET",
    os.getenv("SERVER_SECRET", _DEFAULT_CLIENT_SIGN_SECRET),
)
ALLOW_LEGACY_TOKEN_MIGRATION = os.getenv(
    "ALLOW_LEGACY_TOKEN_MIGRATION",
    "false" if _ENV in ("prod", "production") else "true",
).lower() in ("1", "true", "yes")

CARDNET_WEBHOOK_SECRET  = os.getenv("CARDNET_WEBHOOK_SECRET", "dev_webhook_secret")
DATABASE_URL            = os.getenv("DATABASE_URL", "./sx_license.db")
ADMIN_API_KEY           = os.getenv("ADMIN_API_KEY", "dev_admin_key")
PORT                    = int(os.getenv("PORT", "8000"))

# Token 校验时钟宽限（秒），防网络抖动误判
TOKEN_CLOCK_SKEW_SEC = 60

_DEFAULT_SECRETS = {
    "CLIENT_SIGN_SECRET": _DEFAULT_CLIENT_SIGN_SECRET,
    "ADMIN_API_KEY": "dev_admin_key",
    "CARDNET_WEBHOOK_SECRET": "dev_webhook_secret",
}

def _check_production_secrets():
    """Fail fast when SX_ENV=production still uses known-default secrets."""
    weak = []
    if (CLIENT_SIGN_SECRET == _DEFAULT_SECRETS["CLIENT_SIGN_SECRET"]
            or CLIENT_SIGN_SECRET.startswith("CHANGE_ME")
            or len(CLIENT_SIGN_SECRET) < 32):
        weak.append("CLIENT_SIGN_SECRET")
    token_key_is_default = (
        TOKEN_PRIVATE_KEY_PEM.strip() == _DEFAULT_TOKEN_PRIVATE_KEY.strip()
    )
    token_key_invalid = False
    try:
        parsed_key = serialization.load_pem_private_key(
            TOKEN_PRIVATE_KEY_PEM.encode(), password=None
        )
        token_key_invalid = (
            not isinstance(parsed_key, rsa.RSAPrivateKey)
            or parsed_key.key_size < 2048
        )
    except Exception:
        token_key_invalid = True
    if token_key_is_default or token_key_invalid:
        weak.append("TOKEN_PRIVATE_KEY_PEM")
    if (ADMIN_API_KEY == _DEFAULT_SECRETS["ADMIN_API_KEY"]
            or ADMIN_API_KEY.startswith("CHANGE_ME")
            or len(ADMIN_API_KEY) < 32):
        weak.append("ADMIN_API_KEY")
    if (CARDNET_WEBHOOK_SECRET == _DEFAULT_SECRETS["CARDNET_WEBHOOK_SECRET"]
            or CARDNET_WEBHOOK_SECRET.startswith("CHANGE_ME")
            or len(CARDNET_WEBHOOK_SECRET) < 32):
        weak.append("CARDNET_WEBHOOK_SECRET")
    if (ALLOW_LEGACY_TOKEN_MIGRATION
            and LEGACY_TOKEN_SECRET == CLIENT_SIGN_SECRET):
        weak.append("LEGACY_TOKEN_SECRET(shared with client)")
    if not weak:
        return
    msg = f"Insecure default secrets still in use: {', '.join(weak)}"
    if _ENV in ("prod", "production"):
        print(f"[FATAL] {msg}. Set env vars before production deploy.", file=sys.stderr)
        sys.exit(1)
    warnings.warn(f"[DEV] {msg}", stacklevel=1)

_check_production_secrets()
