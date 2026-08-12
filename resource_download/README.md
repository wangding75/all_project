# resource_download

多平台内容下载（**方案 2**：托管服务端 + 完整本地下载产品）。
**客户端不含 App 适配**；Fanqie/Hongguo 私有兼容、Frida、签名仅在服务端，随平台更新在服务端热修。

> **架构基线**：自 2026-08-12 起，以
> [`docs/ARCHITECTURE_BOUNDARY.md`](./docs/ARCHITECTURE_BOUNDARY.md) 为唯一权威边界文件。
> 文档状态：**NORMATIVE / FROZEN**。

**当前代码版本**：`1.0.0`（`pyproject.toml` / `server/app/version.py`）

---

## 架构（冻结）

详见 [`docs/ARCHITECTURE_BOUNDARY.md`](./docs/ARCHITECTURE_BOUNDARY.md)（NORMATIVE / FROZEN）。

| 侧 | 目录 | 职责 |
|----|------|------|
| **服务端** | `server/` | Hongguo/Fanqie 平台适配、资源解析、License/Quota/Idempotency、必要 Streaming Proxy |
| **客户端** | `client/` | 完整本地下载产品：DownloadTask、Queue、Progress、Retry、断点续传、本地文件、SQLite、下载历史、定时查询 |
| **禁止进客户端** | `platforms/` / Frida / `vendor` | 平台兼容性留在服务端 |
| **禁止进服务端** | 下载文件落盘 / Server Job 长期管理 / Automation Scheduler | 职责属于客户端 |

```text
Desktop Client                           RD Server
  DownloadManager                           │
  Local SQLite/History                      │ License/Quota
  Client Timer / Polling                    │ Platform Adapt (Hongguo/Fanqie)
  Queue/Retry/Progress                      │ Frida/Hook/Sign/Session
                    Device Proof + Request  │
                    ──────────────────────► │
                    ◄── DownloadDescriptor ─┤
                                            │ License Service (rd Tenant)
```

> **RD Server 不保存下载文件，不管理用户下载任务，不做 Automation Scheduler。**
> **文件只落在 Desktop Client 本地。**

---

## 文档怎么读

| 文档 | 职责 |
|------|------|
| [`docs/ARCHITECTURE_BOUNDARY.md`](./docs/ARCHITECTURE_BOUNDARY.md) | **⭐ 权威架构边界（NORMATIVE / FROZEN）** |
| [`docs/ARCHITECTURE_MIGRATION_INVENTORY.md`](./docs/ARCHITECTURE_MIGRATION_INVENTORY.md) | **代码迁移清单（T41 生成）** |
| [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md) | 历史架构决策记录（部分内容已由 ARCHITECTURE_BOUNDARY 覆盖） |
| [`POST_MVP_PLAN.md`](./POST_MVP_PLAN.md) | 历史阶段进度与 backlog（V1.0 已完成） |
| [`client/README.md`](./client/README.md) | 桌面客户端启动方式 |
| [`docs/api.md`](./docs/api.md) | HTTP API 契约（含旧 /v1/jobs、/v1/files 标记） |
| [`docs/hongguo_setup.md`](./docs/hongguo_setup.md) / [`docs/fanqie_app_setup.md`](./docs/fanqie_app_setup.md) | 平台环境（服务端） |
| [`docs/deployment.md`](./docs/deployment.md) | 生产部署 |
| [`docs/release.md`](./docs/release.md) | 打包说明 |
| [`docs/release_gate.md`](./docs/release_gate.md) | 发版门禁（V1.0） |
| [`LICENSE_SERVICE_INTEGRATION_REPORT.md`](./LICENSE_SERVICE_INTEGRATION_REPORT.md) | **[Historical]** T06 License Service 接入报告 |

---

## 目录

```text
server/                 # 中转服务端
  app/                  # API / 鉴权 / License / Quota / 平台适配
  platforms/            # 平台适配（仅服务端）
  run.py
client/                 # 桌面客户端
  ui/                   # Web UI
  desktop/              # 桌面壳
vendor/hongguo/         # 上游（仅服务端，勿提交密钥）
scripts/                # smoke / e2e / build_exe / ops
docs/
data/                   # 运行时
```

---

## 快速开始

普通业务请求使用 Device Proof + ACTIVE License Context。API Key 仅用于运维边界，不能绕过 License。
Legacy User/JWT endpoints 为向后兼容 API，不是当前 Desktop 业务主链路。

### 1. 服务端（中转）

```powershell
cd server
pip install -r requirements.txt
python run.py
```

默认：`http://127.0.0.1:8000`，开发 Key：`X-API-Key: dev-key-change-me`。
生产请配置强随机 `api_key` / `jwt_secret` 以及 `LICENSE_SERVICE_*` RD Service Credential，见 `docs/production.env.example`。

### 2. 桌面客户端

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
python client/desktop/main.py
```

浏览器：`http://127.0.0.1:8000/ui/`

**本机一体演示（仅开发）**：

```powershell
$env:CLIENT_MODE = "embedded"
python client/desktop/main.py
```

### 3. 打包

```powershell
python scripts/build_exe.py --noconsole
# 产物：dist/ResourceDownloader.exe
```

### 4. 脚本验收（服务端）

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY  = "dev-key-change-me"
python scripts/smoke_health.py
python scripts/license_e2e.py
```

---

## 说明

- 平台私有协议、签名、Session 在服务端；Desktop Client 不贴源站 Cookie 作为主路径。
- 仅供个人学习研究，请遵守平台条款与版权法。
