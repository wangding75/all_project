# client — 瘦客户端（方案 2）

**职责**：产品壳。登录 / 激活 / VIP、连中转服务端下载、以后排行榜 / 热榜 / 上新等纯客户端功能。

**禁止**：平台适配、Frida、签名解密、`vendor`、本机模拟器业务逻辑。  
边界见仓库根目录 [`DEVELOPMENT_PLAN.md`](../DEVELOPMENT_PLAN.md) §0.1 冻结约定。

## Device Proof V3（正式桌面路径）

Windows Desktop Client 使用 License Service 固定的 `LS-DEVICE-V3` 和 rc3
Python helper，当前算法为 `ED25519`。首次启动生成一对设备密钥；
`device_id` 始终由 32-byte raw public key 的 SHA-256 派生为
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

- `POST /v1/jobs`
- `POST /v1/jobs/batch`
- `POST /v1/jobs/queue/bulk/retry`
- `POST /v1/jobs/{job_id}/retry`
- `PUT /v1/automation/hongguo-new`
- `POST /v1/automation/hongguo-new/scan`

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
`vendor/license_service_client-1.0.0rc3-py3-none-any.whl`（SHA-256
`30EC6E2FFA86627A7F1E6DD2E9AE7F2A07FE44161495AFD864D9090CBBF43A53`）及其
`cryptography` 依赖。生产 Desktop EXE 默认不包含 `server/app`、平台适配或
`vendor` 目录。
