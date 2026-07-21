from dotenv import load_dotenv
import os

load_dotenv()

SERVER_SECRET           = os.getenv("SERVER_SECRET", "dev_secret_change_in_prod")
CARDNET_WEBHOOK_SECRET  = os.getenv("CARDNET_WEBHOOK_SECRET", "dev_webhook_secret")
DATABASE_URL            = os.getenv("DATABASE_URL", "./sx_license.db")
ADMIN_API_KEY           = os.getenv("ADMIN_API_KEY", "dev_admin_key")
PORT                    = int(os.getenv("PORT", "8000"))

# Token 校验时钟宽限（秒），防网络抖动误判
TOKEN_CLOCK_SKEW_SEC = 60
