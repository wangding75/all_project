# client — 瘦客户端（方案 2）

**职责**：产品壳。登录 / 激活 / VIP、连中转服务端下载、以后排行榜 / 热榜 / 上新等纯客户端功能。

**禁止**：平台适配、Frida、签名解密、`vendor`、本机模拟器业务逻辑。  
边界见仓库根目录 [`DEVELOPMENT_PLAN.md`](../DEVELOPMENT_PLAN.md) §0.1 冻结约定。

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
