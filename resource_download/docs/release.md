# 客户端打包与发布说明 (Release Manual)

> **T39 authoritative packaging contract:** `scripts/build_exe.py` builds only
> the thin desktop client. A releasable RD package must be built with
> `scripts/build_release_package.py`, which also builds `RDServer.exe` and
> assembles `server/app`, `server/platforms`, the curated Hongguo runtime,
> the Frida agent, safe templates, and deployment/rollback documentation.
> Production runs `RDServer.exe` as the standalone server and
> `ResourceDownloader.exe` in `CLIENT_MODE=thin`; the old embedded client path
> is development-only and is not a release topology.

本指南针对桌面壳打包。架构为 **方案 2：瘦客户端 + 中转服务端**（见 [`DEVELOPMENT_PLAN.md`](../DEVELOPMENT_PLAN.md) §0.1）。

- **生产推荐**：服务端独立部署 `server/run.py`；客户端 `CLIENT_MODE=thin` + `API_BASE`。  
- **本脚本产物**：桌面 EXE（可 embedded 嵌服务作演示，非唯一形态）。

**当前版本**：`1.0.0`（与 `pyproject.toml` / `server/app/version.py` 一致）  
**关联**：生产部署见 [`deployment.md`](./deployment.md)；门禁 DoD 见 [`release_gate.md`](./release_gate.md)；运维见 [`ops_runbook.md`](./ops_runbook.md)。

---

## 1. 软件环境与依赖需求

在执行打包前，请确保打包机已配置 Python 环境并安装了以下基础依赖库：

- **打包机编译环境**:
  - Python >= 3.8 (推荐使用与开发环境一致的 Python 版本)
  - `PyInstaller` (打包核心工具)
  - `pywebview` (桌面客户端窗口外壳容器，基于 C# WebView2 后端)
  - `pydantic-settings` (配置解析)
  - `fastapi` & `uvicorn` (后端 Web 服务端)
  - `fonttools` & `brotli` (小说字体混淆解密)
  - `pycryptodome` (红果加解密依赖)
  - `requests` & `httpx`

- **运行机环境需求（红果/番茄 App 会话功能可用前置）**:
  - 本地具备可用的 MuMu 实例 `RD测试`；ADB endpoint 由 MuMuManager 动态发现。
  - 配置了与 `frida-server` 连通的 Frida 调试端口（针对番茄 App 解混淆）。
  - 在 EXE 同级下安装或放置 `vendor/hongguo`。
  - Windows 系统需要安装有 WebView2 运行时（现代 Win10/Win11 已默认内置）。

---

## 2. 编译打包指令

使用项目根目录下优化后的自动化打包脚本进行编译。该脚本会将前端 `ui` 目录、FastAPI `app` 目录、各平台的 `platforms` 适配模块以及 `webview` 自身框架依赖自动内嵌到独立可执行程序中：

```powershell
# 1. 进入仓库根目录
cd d:/github/all_project/resource_download

# 2. 执行打包脚本 (默认不内嵌 vendor，在 dist/ 下输出 ResourceDownloader.exe)
python scripts/build_exe.py

# 3. 商业正式发版打包 (开启 --noconsole 隐藏控制台，日志自动落盘至 logs/desktop.log)
python scripts/build_exe.py --noconsole
```

> **可选高级选项**:
> - 如需在生成的 EXE 中直接固化并集成 `vendor` 源码目录（全内嵌分发版本），可通过环境变量驱动：
>   ```powershell
>   $env:INCLUDE_VENDOR = "1"
>   python scripts/build_exe.py --noconsole
>   ```

---

## 6. 商业产品 v1.0.0 部署与发版专章

### 1. 商业发布包无控制台打标
在正式向客户发布时，必须使用 `--noconsole` 命令行参数构建无黑框产物：
```powershell
python scripts/build_exe.py --noconsole
```
构建成功后，EXE 启动时将不在桌面弹出 CMD 黑框，所有控制台与 Backend 日志将自动异步落盘记录到安装根目录下的 `logs/desktop.log` 中。

### 2. 生产环境安全与排查 Checklist
- **版本号对齐**: 确认服务端 `app.__init__.__version__`、桌面标题栏与 `/health` 探活返回版本号均为 `1.0.0`。
- **免责与风控声明**: 产品仅用于合规的抓取中继与个人备份。涉及番茄/红果平台的数据解密及设备池操作必须遵守目标平台 ToS 及法律法规。
- **Release Gate 表**: 发版前必须查阅并核对 [release_gate.md](file:///d:/github/all_project/resource_download/docs/release_gate.md) 中 C1~C10 全部检查项通过。


---

## 3. 首次运行与系统配置

双击启动 `dist/ResourceDownloader.exe` 后，程序将执行以下流程：

1. **配置生成**:
   - 程序会自动检测同级目录下是否存在 `.env` 配置文件。
   - 若缺失，会自动生成包含以下默认参数的 `.env`：
     ```ini
     # 服务端密钥鉴权配置
     API_KEY=dev-key-change-me
     HOST=127.0.0.1
     PORT=8000
     ```
2. **初始化存储**:
   - 自动在 EXE 同级目录下创建 `data/` 存储区，包含 `data/jobs/` 任务状态与 `data/outputs/` 下载产物目录。数据存储目录不再依赖开发时仓库路径。
3. **桌面窗口启动**:
   - 后台 uvicorn 服务开启后，程序会进行动态健康轮询（超时 15s），检测到 `/health` 返回 200 后，自动拉起一个独立的桌面窗口承载前端网页（无需用户手动打开浏览器）。
   - 窗口为**无边框样式**，完美融入了 Obsidian 风格的主题设计。

---

## 4. 商业 dual 模式与客户端闭环

桌面客户端保留 RD 用户登录与旧兑换 UI，但 T06 服务端已切换为统一
License Service Device License。当前发布状态为 **RD LICENSE INTEGRATION PASS /
CLIENT CUTOVER COMPLETE**：正式客户端已经使用 Device Proof V3。

1. **商业默认路径 (AUTH_MODE=dual / jwt_only)**:
   - 用户打开客户端后，在侧边栏或设置页面点击「登录 / 注册」。
   - **注册**: `POST /v1/auth/register`，提交用户名与密码。
   - **登录**: `POST /v1/auth/login`，成功后获取 JWT `access_token` 并保存在 `localStorage` 中。
   - **身份拉取**: 客户端发起后续 API 请求均自动携带 `Authorization: Bearer <token>`；启动或登录后调用 `GET /v1/auth/me` 刷出当前用户身份与 `vip_expires_at`。
2. **Activation Proxy**:
   - `POST /v1/auth/redeem` 仍保留兼容 path，但必须携带 Device identity 与
     `LS-DEVICE-V3` activation proof；旧客户端会收到 `DEVICE_PROOF_REQUIRED`。
   - `vip_expires_at` 仅为 deprecated display alias，不再是授权事实。
3. **License / 403 / 503 / 429 诚实提示**:
   - `POST /v1/jobs` 必须携带绑定当前请求的 Device Proof；`INACTIVE` 返回
     403，License Service 不可用返回 503，RD Quota 仍返回 429。
   - 当任务创建受每日配额限制时返回 429（detail 区分「配额用尽」与「请求频繁」），客户端进行明细区分提示，杜绝假成功。
4. **开发 / 运维旁路 (AUTH_MODE=dev + API Key)**:
   - 在设置 ->「高级/运维模式」中保留 `API Key` 配置项。仅当未存储 Access Token 时，`apiFetch` 会退化为发送 `X-API-Key` 标头，用于 CI/E2E 自动化测试与 ops 运维调测。

---

## 5. 生产环境安全指引

- **覆盖默认 API Key**:
  - 打包生成默认的 `dev-key-change-me` 仅供本地快速测试，防止启动报错。
  - 在正式部署或多人网络访问前，**请务必手动修改 `.env` 中的 `API_KEY` 为强密钥**。
  - 若服务端检测到使用的仍是默认配置密钥，启动控制台将会输出明显的醒目警告警告。
- **防止敏感数据外泄**:
  - `data/config/` 中的番茄 App 抓包 Token 及红果会话数据属于高度敏感凭证。**切勿将整个包含 data/config/ 的目录压缩发给非受信人员**。

---

## 5. 验收测试表 (Release Checklist)

发布新版本客户端时，应按如下步骤完成冒烟测试以确认功能健康度：

- [ ] **1. 打包无异常**: 运行 `python scripts/build_exe.py` 成功输出 EXE，体积约为 60~70MB 左右（因为打包了 webview 及 pythonnet 依赖）。
- [ ] **2. 静默初始化**: 首次双击 `ResourceDownloader.exe`，正确在同级生成 `.env` 与 `data/` 目录，没有提示文件缺失。
- [ ] **3. 独立窗体正常拉起**: 桌面窗体成功弹出且没有报错提示，左下角显示 `服务正常 (1.0.0)`（或当前 `__version__`），连通灯呈**绿色**。
- [ ] **4. 窗口拖动与控制按钮功能**:
  - 拖拽顶部标题栏空白区域，确认窗体可以正常在桌面上移动。
  - 点击右上角的 `—` 确认窗口可以最小化。
  - 点击右上角的 `□` 确认窗口可以最大化与恢复窗口大小。
  - 点击右上角的 `✕` 确认窗口可以完全退出，且控制台进程完全释放关闭。
- [ ] **5. 默认 API Key 报警**: 命令行窗口有黄色警告：`⚠️ 当前使用的是默认开发 API Key`。
- [ ] **6. 检索与详情拉取**: 在搜索框输入测试书号/剧名，正常拉取封面、章节目录，无假成功 Toast 弹窗。
- [ ] **7. 任务建立与 429 限流**:
  - 创建 1 个任务，在「下载任务」页面可见任务进度处于 `running` 或 `pending` 轮询状态。
  - 快速建立第 6 个任务，确认界面能诚实弹出失败 Toast 提示：`429 active job count limit reached`。
- [ ] **8. 重启恢复验证**: 在任务执行中途直接关闭桌面窗口。重新双击启动，在任务列表中原进行中任务的进度已变为 `failed`（状态标志为 `服务重启，任务已被中断`）。
- [ ] **9. 本地产物目录定位**: 点击下载任务或设置页的「打开下载目录」按钮，系统能正常唤起资源管理器定位至本机的 outputs 目录中。
