# client — Desktop 客户端（方案 2）

> **[T41 2026-08-12] 架构基线冻结。**
> **权威架构文件：[`../docs/ARCHITECTURE_BOUNDARY.md`](../docs/ARCHITECTURE_BOUNDARY.md)（NORMATIVE / FROZEN）**

**责任**：完整本地下载产品。包括：

- 登录 / 激活 / VIP、连中转服务端下载
- **DownloadTask / 下载队列 / 并发控制 / 进度 / 暂停 / 恢复 / 重试 / 断点续传**
- **本地文件存储 / 文件命名 / 下载目录管理**
- **本地 SQLite / 下载历史 / 本地文件索引**
- **Client Timer / 定时刷新 / 热榜轮询 / 上新轮询**（代替 Server Automation）
- 以后排行榜/热榜/上新等纯产品功能

**禁止**：平台适配、Frida、签名解密、`vendor`、本机模拟器业务逻辑。
边界见仓库根目录 [`docs/ARCHITECTURE_BOUNDARY.md`](../docs/ARCHITECTURE_BOUNDARY.md) （覆盖旧 DEVELOPMENT_PLAN.md §0.1）。

> Server Automation Scheduler 已移除；发现轮询、去重和自动入队由 Client Timer 完成。

T42–T43 已落地的本地能力位于 `desktop/download_manager.py`、
`desktop/download_repository.py`、`desktop/download_transport.py` 和
`desktop/client_timer.py`。SQLite 数据库默认位于当前 Windows 用户的
`%LOCALAPPDATA%\ResourceDownloader\downloads.sqlite3`；下载中的文件使用
`.part` 后缀，完成后才原子改名。重启会把 `running` 任务恢复为 `pending`，并
保留 `.part` 以便在上游支持 Range 时续传。

## Device Proof V3（正式桌面路径）

Windows Desktop Client 使用 License Service 固定的 `LS-DEVICE-V3` 和 rc4
`dev_<64 lowercase hex>`，不会使用 UUID、MAC、MachineGuid、用户名或硬盘序列号。

private key 只保存在当前 Windows 用户的 DPAPI 安全存储中：
`%LOCALAPPDATA%\ResourceDownloader\device_identity.dpapi`。它不写入项目目录、
Git、日志、JavaScript、`localStorage` 或 `sessionStorage`，也不会上传到 RD
Server 或 License Service。重新启动会验证并复用同一 identity；损坏时返回
`DEVICE_IDENTITY_INVALID`，不会静默生成替代设备。设置页的“重置设备身份”是
明确的用户操作，重置后 License Service 会视为新设备，必须重新激活，并可能占用新的设备槽位。

客户端只通过 PyWebView 的 native bridge 生成 Activation Proof 和业务 Request
Proof。`POST /v1/auth/redeem` 的 body proof 覆盖 `rd`、激活码、device id、公钥、
时间戳和新 nonce；受保护请求的 headers 覆盖最终 method、path + query、最终
raw body 的 SHA-256、时间戳和新 nonce。HTTP retry 会重新生成 Proof，不重放旧 nonce。

当前自动签名范围严格为：

- `POST /v1/resolve`
- `GET /v1/downloads/proxy/{ticket}`
- Client Discovery Timer：本地持久化 hot/new 轮询状态、非重入、错误 backoff 和可选自动入队；只调用受保护的 `/v1/discover`，不依赖 Server Scheduler。

客户端只知道 RD `API_BASE`，不会直接调用 License Service，也不包含 RD Service
Credential、License Service Credential、私钥、Admin API 或 Server SDK。

普通浏览器可以继续使用登录、搜索、详情和普通查询；浏览器没有 Desktop Device
Private Key，因此 redeem 与上述受保护操作会 fail-closed，并提示
`DESKTOP_DEVICE_IDENTITY_REQUIRED`。任何 key 都不会通过浏览器存储绕过这一边界。

## 目录

```text
client/
  ui/           # Web UI（由服务端挂载为 /ui，或经桌面壳打开）
  desktop/      # 可选 PyWebView 壳
```

## 启动

### 1. 服务端先起（另开终端）

```powershell
cd server
python run.py
# http://127.0.0.1:8000
```

### 2. 瘦客户端（默认）

```powershell
# 可选：指定服务端
$env:API_BASE = "http://127.0.0.1:8000"
$env:CLIENT_MODE = "thin"   # 默认即可省略
python client/desktop/main.py
```

浏览器也可直接：

```text
http://127.0.0.1:8000/ui/
```

### 3. 本机一体演示（仅开发）

```powershell
$env:CLIENT_MODE = "embedded"
python client/desktop/main.py
```

`embedded` 会在本机嵌 uvicorn，**不是**生产分发形态。

## 打包

当前 `scripts/build_exe.py` 仍打「桌面壳 + 可选嵌服务」产物；生产目标为：

- 服务端：独立部署 `server/`
- 客户端：本目录 UI + 桌面壳，只连 `API_BASE`

打包前必须安装仓库固定的
`vendor/license_service_client-1.0.0rc4-py3-none-any.whl`（SHA-256
`62E502DC2BAB6F925DACB4A51E92D4D39F9CD459E7C209C618C8FB46CC5C29C9`）及其
`cryptography` 依赖。生产 Desktop EXE 默认不包含 `server/app`、平台适配或
`vendor` 目录。
