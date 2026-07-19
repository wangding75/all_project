# 番茄小说 App 会话 (Fanqie App Session) 接入与配置指南

本文档介绍如何配置并使用番茄小说 App 会话模式拉取并解密付费/非公开章节。

---

## 1. 前置依赖与环境准备

### 1.1 模拟器与 App 环境

1. 安装 **MuMu 模拟器**（或兼容 Android 模拟器）。
2. 在模拟器中安装 **番茄小说 App** (`com.dragon.read`) 并正常打开运行一次。
3. 确保 ADB 调试工具能够连接模拟器端口（例如 `127.0.0.1:16384`）。

### 1.2 注入脚本部署

确认本地存在 Frida 解密预言机 JS 脚本：
- 路径：`tools/setup/fanqie_crypt_oracle.js`

---

## 2. 配置文件说明

在 `.env` 或 `server/app/config.py` 中确认默认 ADB 与 Frida 监听配置：

```env
ADB=D:\install\Netease\MuMu\nx_main\adb.exe
ADB_DEVICE=127.0.0.1:16384
FRIDA_HOST=127.0.0.1:27042
FANQIE_PKG=com.dragon.read
```

如需微调，可在 `.env` 中添加对应变量覆盖。

---

## 3. 端到端验收与验证 (E2E)

### 3.1 运行 Web SSR 模式 (默认模式)

```powershell
server\.venv\Scripts\python.exe scripts/e2e_fanqie.py --id "https://fanqienovel.com/page/<BOOK_ID>" --range 1-3
```

### 3.2 运行 App 解密模式

```powershell
server\.venv\Scripts\python.exe scripts/e2e_fanqie.py --id "<BOOK_ID>" --range 1-3 --options "{\"mode\":\"app\"}"
```

验收标准：
- Web 模式成功输出 Markdown 小说文件。
- App 模式成功通过 Frida Oracle 解密并输出原文 Markdown 文件。
