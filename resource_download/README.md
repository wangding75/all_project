# resource_download

多平台内容下载中转（**方案 2**：托管服务端 + 瘦客户端）。  
**客户端不含 App 适配**；适配与 Frida/签名仅在服务端，随平台更新在服务端热修。

**当前代码版本**：`1.0.0`（`pyproject.toml` / `server/app/version.py`）

## 架构（冻结）

详见 [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md) **§0.1 客户端/服务端边界**。

| 侧 | 目录 | 职责 |
|----|------|------|
| **服务端** | `server/` | 中转 API、卡密 VIP、任务、番茄/红果适配 |
| **客户端** | `client/` | 登录/激活、连服务端下载；以后排行榜/热榜/上新 |
| **禁止进客户端** | `platforms` / Frida / `vendor` | 履约只在服务端 |

```text
client (瘦)  --HTTPS API-->  server (中转 + 适配 + 设备/签名)
```

## 文档怎么读

| 文档 | 职责 |
|------|------|
| [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md) | **架构决策与 client/server 冻结边界** |
| [`POST_MVP_PLAN.md`](./POST_MVP_PLAN.md) | 阶段进度与剩余 backlog |
| [`client/README.md`](./client/README.md) | 瘦客户端启动方式 |
| [`docs/api.md`](./docs/api.md) | HTTP API 契约 |
| [`docs/hongguo_setup.md`](./docs/hongguo_setup.md) / [`docs/fanqie_app_setup.md`](./docs/fanqie_app_setup.md) | 平台环境（服务端） |
| [`docs/deployment.md`](./docs/deployment.md) | 生产部署 |
| [`docs/release.md`](./docs/release.md) | 打包说明 |
| [`docs/release_gate.md`](./docs/release_gate.md) | 发版门禁 |

## 目录

```text
server/                 # 中转服务端
  app/                  # API / 鉴权 / 任务
  platforms/            # 平台适配（仅服务端）
  run.py
client/                 # 瘦客户端
  ui/                   # Web UI
  desktop/              # 桌面壳（默认 CLIENT_MODE=thin）
vendor/hongguo/         # 上游（仅服务端，勿提交密钥）
scripts/                # smoke / e2e / build_exe / ops
docs/
data/                   # 运行时
```

## 快速开始

### 1. 服务端（中转）

```powershell
cd server
pip install -r requirements.txt
# 或根目录: pip install -r requirements.txt
python run.py
```

默认：`http://127.0.0.1:8000`，开发 Key：`X-API-Key: dev-key-change-me`。

生产请配置强随机 `api_key` / `jwt_secret`，见 `docs/production.env.example`。

### 2. 瘦客户端

```powershell
# 桌面壳（连已启动的服务端）
$env:API_BASE = "http://127.0.0.1:8000"
python client/desktop/main.py
```

或浏览器：`http://127.0.0.1:8000/ui/`

**本机一体演示（仅开发）**：

```powershell
$env:CLIENT_MODE = "embedded"
python client/desktop/main.py
```

### 3. 打包

```powershell
# 当前仍产出桌面 EXE（内可嵌服务供演示；生产应以独立 server + 瘦 client 部署）
python scripts/build_exe.py --noconsole
# 产物：dist/ResourceDownloader.exe
```

### 4. 脚本验收（服务端）

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY  = "dev-key-change-me"
python scripts/smoke_health.py
python scripts/e2e_hongguo.py --search "剧名" --range 1-1
```

更多见 [`scripts/README.md`](./scripts/README.md)。番茄/红果设备与 Frida 属**服务端运维**，见平台 setup 文档。

## 说明

- 会话与签名在服务端；用户客户端不贴源站 Cookie 作为主路径。  
- 仅供个人学习研究，请遵守平台条款与版权法。
