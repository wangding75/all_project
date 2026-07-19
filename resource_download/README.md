# resource_download

多平台内容下载中转（**方案 2**：托管服务端 + 瘦客户端）。  
当前主路径：**红果，复用 [zhangbaio/hongguo](https://github.com/zhangbaio/hongguo)**。

权威计划见 [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md)。  
红果接入说明见 [`docs/hongguo_reuse.md`](./docs/hongguo_reuse.md)。

## 目录

```text
server/                 # 中转服务端（FastAPI）
  app/                  # API / 鉴权 / 任务
  platforms/hongguo/    # 适配 vendor/hongguo（主路径）
  platforms/fanqie/     # 遗留/后置
  run.py
vendor/hongguo/         # 上游 clone（config.json 自备，勿提交）
scripts/                # e2e_hongguo / e2e_fanqie
docs/
data/
```

## 快速开始（红果主路径）

### 0. 准备上游

```powershell
git clone --depth 1 https://github.com/zhangbaio/hongguo.git vendor/hongguo
# 配置 config.json + 签名环境（Frida / SIGN_SERVER），先在 vendor 内用 offline_dl 验证
```

### 1. 启动本仓服务端

需要 **Python 3.10+**（推荐 `py -3.14`）。

```powershell
cd server
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install requests pycryptodome
python run.py
```

默认：`http://127.0.0.1:8000`，`X-API-Key: dev-key-change-me`。

> **⚠️ 生产环境请在 `server/.env` 中设置 `api_key=<随机强密钥>`，默认值仅限本地开发！**



### 2. 脚本验收

```powershell
$env:API_BASE="http://127.0.0.1:8000"
$env:API_KEY="dev-key-change-me"
python scripts/smoke_health.py
python scripts/e2e_hongguo.py --search "剧名" --range 1-1
```

## 里程碑

| 级别 | 范围 |
|------|------|
| **MVP-H** | 复用 hongguo + relay + e2e 出 MP4 |
| **MVP-F** | 番茄 App 会话 |
| 之后 | 客户端 UI、订阅配额 |

## 说明

- 会话与签名在服务端；用户客户端不贴源站 Cookie。  
- 仅供个人学习研究，请遵守平台条款与版权法。
