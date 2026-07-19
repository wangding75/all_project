# 红果短剧平台 (Hongguo) 接入与部署指南

本文档提供红果短剧平台的独立部署与调试指引。

---

## 1. 环境与依赖准备

### 1.1 克隆上游算法库

项目依赖 `vendor/hongguo` 算法库。在仓库根目录下运行：

```powershell
git clone --depth 1 https://github.com/zhangbaio/hongguo.git vendor/hongguo
```

确认文件 `vendor/hongguo/hongguo.py` 及 `vendor/hongguo/offline_dl.py` 正常存在。

### 1.2 设备与 Token 配置

从手机/模拟器中提取红果 App 的设备信息与 Session Token，生成配置文件：
- 默认路径：`data/config/hongguo_config.json`（或 `vendor/hongguo/config.json`）

配置示例格式参见 `vendor/hongguo/config.example.json`。

---

## 2. 签名后端准备

红果 API 请求依赖移动端签名算法。支持以下几种签名模式：

1. **Unidbg 签名服务**：
   运行 `vendor/hongguo/unidbg-sign` 服务（推荐服务端部署）。
2. **Frida Oracle 预言机**：
   通过 Android 模拟器（如 MuMu 模拟器）挂载运行中的红果 App 实时签名。

---

## 3. 服务端接入与验证

### 3.1 启动服务端

```powershell
server\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3.2 运行健康检查

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY  = "dev-key-change-me"

server\.venv\Scripts\python.exe scripts/smoke_health.py
```

预期响应中包含 `hongguo` 平台。

### 3.3 运行端到端验收脚本 (E2E)

```powershell
server\.venv\Scripts\python.exe scripts/e2e_hongguo.py --search "剧名" --range 1-1
```

验收标准：脚本执行完毕并在 `data/outputs` 目录下输出大小大于 0 字节且可播放的 `.mp4` 文件。
