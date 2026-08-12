# ResourceDownloader 生产部署与发版指南 (Deployment Manual)

> **T39 release-package authority:** The supported package topology is
> `RDServer.exe` (standalone server) plus `ResourceDownloader.exe` (thin
> client). The package is extracted to an independent directory and must not
> use a source checkout, source virtual environment, or `PYTHONPATH`. The
> legacy desktop-auto-start and source-Uvicorn examples below describe the
> development/legacy topology only; for a release gate follow
> `docs/release_package_deployment.md` and
> `docs/release_package_rollback.md`.

> **[T41 2026-08-12] 架构基线冻结。**
> **权威架构文件：[`ARCHITECTURE_BOUNDARY.md`](./ARCHITECTURE_BOUNDARY.md)（NORMATIVE / FROZEN）**
>
> **Server Runtime 启动前置确认**（参见 ARCHITECTURE_BOUNDARY.md §14）：
> 1. ADB 可用
> 2. 存在一台可用 Android Device
> 3. Android Boot Completed
> 4. Fanqie 已安装（com.dragon.read）
> 5. Hongguo 已安装（com.phoenix.read）
> 6. Frida / Runtime 基础能力存在
> 7. RD Control Database 可用
> 8. License Service 可访问
>
> **历史固定端口 7555 / 16384 不得写成长期设备身份；ADB Port 可随模拟器重启变化。**
> **[Historical Evidence]：7555 / 16384 为早期开发备案记录，不得作为生产设备身份使用。**
>
> **`data/outputs/` 下载目录状态：[IMPLEMENTATION_MIGRATION_REQUIRED]**
> 当前服务端仍将下载文件落盘至 `data/outputs/`。根据架构边界，
> **目标文件只落在 Desktop Client 本地**；待 T42 迁移计划执行后消除服务端落盘路径。

**版本号**: `1.0.0`
**适用范围**: Windows 单机桌面应用与本地中转服务端部署
**编写时间**: 2026-07-24

---

## 一、 系统架构与部署边界

本项目的生产部署严格遵循以下架构边界：

1. **单进程单 Worker 约束**:
   - 服务端仅支持单 Python 进程运行。
   - Uvicorn 部署配置强约束为 `WORKERS = 1`。若环境变量或配置中设置 `WORKERS > 1`，应用启动阶段 `lifespan` 将抛出 `RuntimeError` 拒绝启动。
2. **轻量本地持久化**:
   - 数据库使用嵌入式 SQLite (`data/app.db`)，由 SQLAlchemy 统一映射。
   - 任务记录采用 `os.fsync` + `os.replace` 原子 JSON 写入（`data/jobs/*.json`）。
3. **License Service 外部依赖**:
   - RD 不直连 License PostgreSQL；通过固定 wheel 中的 `LicenseServerClient`
     访问 `rd` Tenant。RD 自己的用户、任务和 Quota 仍在 SQLite。
   - 本轮 `WORKERS=1` 约束继续保留，因此授权缓存使用 SDK `MemoryReplayStore`。

---

## 二、 环境准备与依赖安装

### 2.1 依赖安装分层

根据 [pyproject.toml](file:///d:/github/all_project/resource_download/pyproject.toml)，项目的依赖已完成标准化分层：

* **生产运行依赖 (`requirements.txt`)**:
  包含服务端与客户端生产运行所需的最小核心依赖集：
  ```bash
  pip install -r requirements.txt
  ```
   *(包含: fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, httpx, pyjwt, fonttools, brotli 以及固定 License Service SDK wheel)*

* **开发测试与打包依赖 (`requirements-dev.txt`)**:
  用于代码质量门禁、单元测试及 PyInstaller 编译打包：
  ```bash
  pip install -r requirements-dev.txt
  ```
  *(包含: pytest, pytest-asyncio, ruff, pyinstaller, pywebview)*

---

## 三、 部署方式一：Windows 单机桌面应用部署 (推荐)

### 3.1 生产构建编译

使用商业无黑框模式命令编译生产可执行程序：

```powershell
# 1. 确保在仓库根目录
cd d:/github/all_project/resource_download

# 2. 执行无黑框生产打包
python scripts/build_exe.py --noconsole
```

打包完成后，产物将生成在 `dist/ResourceDownloader.exe`（单文件可执行程序，体积约 60MB~70MB）。

### 3.2 运行目录结构

发布给终极用户或部署到客户机时，标准的运行目录如下：

```text
ResourceDownloader/
├── ResourceDownloader.exe   # 编译出的独立桌面应用
├── .env                     # 生产配置文件 (首次运行自动生成)
├── logs/
│   └── desktop.log          # 运行日志异步落盘文件
└── data/
    ├── app.db               # SQLite 数据库
    ├── jobs/                # 任务 JSON 原子持久化目录
    └── outputs/             # 媒体资源与小说最终下载产物
```

### 3.3 首次启动初始化

双击 `ResourceDownloader.exe` 后，程序将自动完成以下初始化：
1. 若根目录缺少 `.env`，自动创建包含默认参数的 `.env`。
2. 创建 `data/jobs/` 与 `data/outputs/` 目录。
3. 后台起起 Uvicorn 单进程服务（端口默认 8000），自动轮询探活。
4. 探活成功后拉起基于 WebView2 的原生应用窗口。所有控制台日志将静默写入 `logs/desktop.log`。

---

## 四、 部署方式二：Headless 服务端部署 (Windows Service / Linux 后台)

如需作为纯后端中转 API 服务运行（供远程客户端或脚本接入）：

### 4.1 命令行直接启动

```bash
# 必须设置 WORKERS=1
$env:PYTHONPATH="server"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### 4.2 生产环境变量配置 (.env 硬化)

生产环境部署时，必须在 `.env` 中修改默认敏感密钥：

```ini
# 服务监听 (强约束 WORKERS=1)
HOST=0.0.0.0
PORT=8000
WORKERS=1

# 安全鉴权硬化
API_KEY=PROD-SecretKey-ChangeMe-MustBeLong
AUTH_MODE=dual
JWT_SECRET=PROD-SuperJWTSecretKey-32BytesMinimumLength!
JWT_EXPIRE_MINUTES=10080

# License Service（生产必填；从 Secret 注入，禁止提交私钥）
LICENSE_SERVICE_BASE_URL=https://license.example.internal
LICENSE_SERVICE_KEY_ID=<RD service_key_id>
LICENSE_SERVICE_PRIVATE_KEY=<RD service_private_key>
LICENSE_SERVICE_AUDIENCE=rd
LICENSE_CACHE_TTL_SECONDS=30
LICENSE_SERVICE_TIMEOUT=3.0
LICENSE_SERVICE_VERIFY=true
# LICENSE_SERVICE_CA_BUNDLE=/etc/rd/license-ca.pem
# LICENSE_SERVICE_CLIENT_CERT=/etc/rd/license-client.crt
# LICENSE_SERVICE_CLIENT_KEY=/etc/rd/license-client.key

# 限流与每日配额
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_AUTH_PER_MINUTE=10
FREE_JOBS_PER_DAY=0
VIP_JOBS_PER_DAY=100

# 外部设备与平台 (可选)
ADB_PATH=adb
ADB_DEVICE=
MUMU_INSTANCE_NAME=RD测试
```

> [!CAUTION]
> 绝对不要在生产环境使用默认的 `dev-key-change-me` 或 `change-me-jwt-secret`！如果服务端在生产环境检测到默认 Key，控制台与日志中将抛出醒目安全警告。

---

## 五、 运维、监控与数据热备份 SOP

### 5.1 服务端健康检查与指标监控

* **应用探活 (`GET /health`)**:
  ```bash
  curl http://127.0.0.1:8000/health
  ```
  返回结构：
  ```json
  {
    "status": "ok",
    "version": "1.0.0",
    "platforms": ["hongguo", "fanqie"]
  }
  ```

* **深度运维健康度检查 (`GET /v1/admin/health`)**:
  *需求标头*: `X-API-Key: <PROD_API_KEY>`
  包含 SQLite 连通性、剩余磁盘空间字节数 (`disk_free_human`)、活跃任务数、签名池 summary，以及不泄露 Secret 的 `license_service_configured`、`license_service_reachable` 和缓存 TTL。

* **运行指标导出 (`GET /v1/admin/metrics`)**:
  *需求标头*: `X-API-Key: <PROD_API_KEY>`
  导出系统累计请求数、各平台任务创建/成功/失败计数。

### 5.2 SQLite 在线无锁热备份

系统内置 native 在线热备份工具，无需停机即可完成全量安全备份：

* **执行在线热备份**:
  ```powershell
  python scripts/backup_db.py backup --backup-dir backups/
  ```
  *(自动使用 `sqlite3.connect().backup()` 生成带时间戳的 `app_backup_YYYYMMDD_HHMMSS.db`，并完成只读 Integrity Check)*

* **灾难恢复**:
  ```powershell
  python scripts/backup_db.py restore backups/app_backup_20260724_100000.db
  ```

### 5.3 运营命令行工具 (CLI)

运维人员可通过 [scripts/ops_admin.py](file:///d:/github/all_project/resource_download/scripts/ops_admin.py) 管理 RD 用户与历史 CardKey 数据：

```powershell
# 封禁恶意用户 (使其 JWT 立即失效)
python scripts/ops_admin.py ban-user 1001 --reason "频繁刷接口"

# 解封用户
python scripts/ops_admin.py unban-user 1001

# 批量维护历史 RD CardKey 批次（不影响 License Service，不是 License revoke）
python scripts/ops_admin.py invalidate-batch BATCH-20260720
```

`scripts/gen_card_keys.py` 默认返回 `LEGACY_LOCAL_CARD_KEYS_DISABLED`。只有历史
迁移场景才允许显式添加 `--legacy-migration-only`；新的生产 License Key 必须由
License Service 管理面生成。

---

## 六、 发版前一键质量门禁校验

在将产物打包或推送到生产服务器前，**必须执行质量门禁脚本** 确保全项合格：

```powershell
python scripts/quality_gate.py
```

门禁脚本会自动校验：
1. Python 语法编译 (`py_compile`)
2. 权威版本源一致性 (`pyproject.toml`, `app/version.py`, `__version__` 统一为 `1.0.0`)
3. `WORKERS=1` 运行约束
4. 依赖分层配置文件存在性
5. 75 项 pytest 自动化测试回归全绿

出现任何 FAILED 提示时，必须先定位并修复，严禁带病发版。

---

## 七、 常见故障排查手册 (Troubleshooting)

| 故障现象 | 可能原因 | 解决步骤 |
| :--- | :--- | :--- |
| **启动时抛出 `RuntimeError: 本服务端仅支持单进程/单 Worker`** | `.env` 或启动命令配置了 `WORKERS > 1` | 检查并修改配置为 `WORKERS=1` 或 `workers: 1`。 |
| **客户端界面弹窗提示 `403 用户已被封禁`** | 运营人员调用了 `ban_user` 或该账号状态不正常 | 查阅 `logs/desktop.log` 或使用 `ops_admin.py unban-user <id>` 解封。 |
| **启动后加载某 Job 提示 `.json.corrupted`** | 该 Job JSON 文件曾遭受强行关机断电，格式破损 | 系统的损坏隔离机制已自动将其重命名归档，不影响系统运行。可在 `data/jobs/` 下审查该损坏文件。 |
| **客户端打不开任何网页，提示 WebView2 缺失** | 目标 Windows 机器缺乏 WebView2 运行时 | 在 Microsoft 官网下载并安装 `Microsoft Edge WebView2 Runtime`。 |
