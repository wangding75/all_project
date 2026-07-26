from dotenv import load_dotenv
import os
import sys
import warnings

load_dotenv()

SERVER_SECRET           = os.getenv("SERVER_SECRET", "sx_dev_secret_2026")
CARDNET_WEBHOOK_SECRET  = os.getenv("CARDNET_WEBHOOK_SECRET", "dev_webhook_secret")
DATABASE_URL            = os.getenv("DATABASE_URL", "./sx_license.db")
ADMIN_API_KEY           = os.getenv("ADMIN_API_KEY", "dev_admin_key")
PORT                    = int(os.getenv("PORT", "8000"))

# Token 校验时钟宽限（秒），防网络抖动误判
TOKEN_CLOCK_SKEW_SEC = 60

_DEFAULT_SECRETS = {
    "SERVER_SECRET": "sx_dev_secret_2026",
    "ADMIN_API_KEY": "dev_admin_key",
    "CARDNET_WEBHOOK_SECRET": "dev_webhook_secret",
}

def _check_production_secrets():
    """Fail fast when SX_ENV=production still uses known-default secrets."""
    env = (os.getenv("SX_ENV") or os.getenv("ENV") or "dev").lower()
    weak = []
    if SERVER_SECRET == _DEFAULT_SECRETS["SERVER_SECRET"]:
        weak.append("SERVER_SECRET")
    if ADMIN_API_KEY == _DEFAULT_SECRETS["ADMIN_API_KEY"]:
        weak.append("ADMIN_API_KEY")
    if CARDNET_WEBHOOK_SECRET == _DEFAULT_SECRETS["CARDNET_WEBHOOK_SECRET"]:
        weak.append("CARDNET_WEBHOOK_SECRET")
    if not weak:
        return
    msg = f"Insecure default secrets still in use: {', '.join(weak)}"
    if env in ("prod", "production"):
        print(f"[FATAL] {msg}. Set env vars before production deploy.", file=sys.stderr)
        sys.exit(1)
    warnings.warn(f"[DEV] {msg}", stacklevel=1)

_check_production_secrets()
