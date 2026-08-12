# RD 架构迁移清单（Architecture Migration Inventory）

**文档版本**：T41 初版
**生成日期**：2026-08-12
**依据**：[`ARCHITECTURE_BOUNDARY.md`](./ARCHITECTURE_BOUNDARY.md)（NORMATIVE / FROZEN）
**范围**：只读代码审计；本轮 **不执行** 任何 Action
**下一步**：T42 IMPLEMENTATION MIGRATION PLAN

---

## 0. 说明

本清单通过对 `resource_download/server/` 和 `resource_download/client/` 代码的只读扫描生成。
每项的 `Action` 描述目标方向，**本轮 T41 不执行这些 Action**。

### Action 定义

| Action | 含义 |
|--------|------|
| `KEEP_SERVER` | 能力留在 RD Server，无需迁移 |
| `KEEP_CLIENT` | 能力留在 Desktop Client，无需迁移 |
| `MOVE_TO_CLIENT` | 能力应迁移到 Desktop Client |
| `REFACTOR_SERVER` | 服务端需要重构以符合目标架构 |
| `REMOVE` | 目标是最终删除（不是当前操作） |
| `DEPRECATE_API` | API 标记为废弃，等待 Client 侧替代建立后删除 |
| `ADD_CLIENT` | 客户端需要新增该能力（当前缺失） |
| `NEEDS_REVIEW` | 需进一步分析后决策 |

---

## 1. 服务端组件审计

### 1.1 Job 管理

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| S-001 | `server/app/jobs/manager.py` `JobManager` | 进程内 Download Job 创建、队列管理、状态机、JSON 持久化 | Desktop Client | `MOVE_TO_CLIENT` | client/desktop, local SQLite | 高：当前 UI 依赖 `/v1/jobs` API |
| S-002 | `server/app/jobs/manager.py` `JobRecord` dataclass | Server-side Job 数据结构（包含 `files[]`, `owner_user_id`, `progress` 等）| Desktop Client | `MOVE_TO_CLIENT` | S-001 | 高：同上 |
| S-003 | `data/jobs/*.json` | Server 端 Job 持久化文件（下载任务 JSON 落盘）| Desktop Client SQLite | `MOVE_TO_CLIENT` | S-001 | 中：迁移时需数据对齐 |
| S-004 | `data/outputs/` 目录 | Server 端下载文件落盘目录（MP4/TXT 文件）| Desktop Client 本地文件系统 | `MOVE_TO_CLIENT` | S-001, 平台 download() | 高：文件存储位置根本变化 |
| S-005 | `server/app/api/router.py` `POST /v1/jobs` | Server Job 创建 API | DEPRECATE（替代：`/v1/resolve`）| `DEPRECATE_API` | Client DownloadManager | 高：当前主要业务 API |
| S-006 | `server/app/api/router.py` `GET /v1/jobs` | Server Job 列表 API | Client 本地任务列表 | `DEPRECATE_API` | Client SQLite | 高 |
| S-007 | `server/app/api/router.py` `GET /v1/jobs/{job_id}` | Server Job 状态 API | Client 本地任务状态 | `DEPRECATE_API` | Client SQLite | 高 |
| S-008 | `server/app/api/router.py` `DELETE /v1/jobs/{job_id}` | Server Job 取消 API | Client 本地任务管理 | `DEPRECATE_API` | Client DownloadManager | 高 |
| S-009 | `server/app/api/router.py` `/v1/jobs/queue/*` | Server Queue 管理 API（pause/resume/reorder）| Client Queue 管理 | `DEPRECATE_API` | Client DownloadManager | 高 |
| S-010 | `server/app/api/router.py` `POST /v1/jobs/{job_id}/retry` | Server Job 重试 API | Client 本地重试 | `DEPRECATE_API` | Client DownloadManager | 高 |
| S-011 | `server/app/api/router.py` `POST /v1/jobs/batch` | 批量创建 Server Job | Client 批量加入本地队列 | `DEPRECATE_API` | Client DownloadManager | 高 |

### 1.2 文件 API

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| S-020 | `server/app/api/router.py` `GET /v1/files` | Server 文件列表（扫描 outputs/ 目录）| Client 本地文件索引 | `DEPRECATE_API` | Client Local File Manager | 中 |
| S-021 | `server/app/api/router.py` `GET /v1/files/{file_id}` | Server 文件下载（E2E 当前依赖）| Client 本地直接打开 | `DEPRECATE_API` | Client Local File Manager | 高：E2E 脚本当前依赖 |
| S-022 | `server/app/api/router.py` `POST /v1/files/{file_id}/open` | Server 端打开文件（在服务端本机）| Client 本地打开 | `DEPRECATE_API` | Client Local File Manager | 低：仅调试用 |

### 1.3 Automation Scheduler

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| S-030 | `server/app/automation/hongguo_monitor.py` `HongguoMonitorService` | 红果上新 Server Automation Scheduler（后台轮询、自动入队）| Desktop Client Timer | `MOVE_TO_CLIENT` | Client Timer, RD Discover API | 中：功能逻辑复杂 |
| S-031 | `server/app/automation/hongguo_monitor.py` `_run_loop()` | Server 后台轮询 asyncio Task | Client Timer | `MOVE_TO_CLIENT` | S-030 | 中 |
| S-032 | `data/automation/hongguo_monitors.json` | Server 端 Automation 策略持久化 | Client 本地配置/SQLite | `MOVE_TO_CLIENT` | S-030 | 低 |
| S-033 | `server/app/api/router.py` `GET/PUT /v1/automation/hongguo-new` | Server Automation 配置 API | Client 本地 Automation 配置 | `DEPRECATE_API` | Client Timer Config | 中 |
| S-034 | `server/app/api/router.py` `POST /v1/automation/hongguo-new/scan` | Server 触发扫描 API | Client 主动 Discover 调用 | `DEPRECATE_API` | Client Timer | 中 |

### 1.4 Media Cache（封面代理）

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| S-040 | `server/app/media_cache.py` `materialize_cover()` | 封面图片服务端代理（临时 JPEG 转换）| **KEEP_SERVER** | `KEEP_SERVER` | 上游 CDN | 低：符合 Streaming Proxy 边界（不永久缓存媒体内容） |
| S-041 | `data/cache/covers/` | 封面 JPEG 缓存（短期）| **KEEP_SERVER（需添加 TTL/清理）** | `REFACTOR_SERVER` | media_cache.py | 低：需要添加过期清理机制 |

### 1.5 ORM 数据模型

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| S-050 | `server/app/models_orm.py` `User` | Server 端用户注册/登录实体（`username`, `hashed_password`, `vip_expires_at`）| **KEEP_SERVER（Legacy Compat）** | `KEEP_SERVER` | auth_router, JWT | 低：兼容旧 User/JWT 路径 |
| S-051 | `server/app/models_orm.py` `User.vip_expires_at` | 旧 VIP 过期时间（已不是授权事实源）| **KEEP_SERVER（Legacy Only）** | `NEEDS_REVIEW` | License Service | 低：代码中已注释为 legacy/display only |
| S-052 | `server/app/models_orm.py` `CardKey` | 本地卡密库（Legacy；新激活走 License Service）| **KEEP_SERVER（Historical）** | `NEEDS_REVIEW` | License Service | 低：新激活不依赖此表 |
| S-053 | `server/app/models_orm.py` `UsageDaily` | RD 每日任务配额计数 | **KEEP_SERVER** | `KEEP_SERVER` | Quota 机制 | 低：服务端 Quota 属于可信控制面 |

### 1.6 Platform 适配（保留在服务端）

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| S-060 | `server/platforms/fanqie/` | 番茄 App 私有协议适配、Frida、签名、正文解密 | **KEEP_SERVER** | `KEEP_SERVER` | Android 模拟器、Frida | 低 |
| S-061 | `server/platforms/hongguo/` | 红果 App 私有协议适配、媒体解密 | **KEEP_SERVER** | `KEEP_SERVER` | vendor/hongguo, Frida | 低 |
| S-062 | `server/platforms/device_discovery.py` | ADB 动态设备发现（T40 验证能力）| **KEEP_SERVER** | `KEEP_SERVER` | ADB | 低：符合单模拟器动态发现模型 |
| S-063 | `server/platforms/readiness.py` | Server 启动 Preflight 检查 | **KEEP_SERVER** | `KEEP_SERVER` | ADB, Frida | 低 |

### 1.7 License / Quota / Security（保留在服务端）

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| S-070 | `server/app/license_gateway.py` `LicenseGateway` | Device 授权查询（调用 License Service SDK）| **KEEP_SERVER** | `KEEP_SERVER` | License Service | 低 |
| S-071 | `server/app/license_guard.py` `require_active_device_license` | License 门卫（API 级别 Device Proof 校验）| **KEEP_SERVER** | `KEEP_SERVER` | license_gateway | 低 |
| S-072 | `server/app/quota.py` | RD 每日任务配额检查/递增/释放 | **KEEP_SERVER** | `KEEP_SERVER` | UsageDaily ORM | 低 |
| S-073 | `server/app/idempotency.py` | 请求幂等控制 | **KEEP_SERVER** | `KEEP_SERVER` | 内存 store | 低 |
| S-074 | `server/app/auth.py` `require_identity` | 统一身份鉴权（API Key / JWT / Device Proof）| **KEEP_SERVER** | `KEEP_SERVER` | LICENSE_SERVICE | 低 |
| S-075 | `server/app/security_boot.py` | 生产安全检查（防默认密钥启动）| **KEEP_SERVER** | `KEEP_SERVER` | config | 低 |
| S-076 | `server/app/sign_pool/` | 签名节点池管理 | **KEEP_SERVER** | `KEEP_SERVER` | 模拟器节点 | 低 |

### 1.8 稳定资源 API（保留在服务端）

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| S-080 | `GET /health` | 健康检查 | **KEEP_SERVER** | `KEEP_SERVER` | - | 低 |
| S-081 | `GET /v1/search` | 搜索 API | **KEEP_SERVER** | `KEEP_SERVER` | platforms | 低 |
| S-082 | `GET /v1/detail` | 详情 API | **KEEP_SERVER** | `KEEP_SERVER` | platforms | 低 |
| S-083 | `GET /v1/discover` | 发现/热榜/上新 API（实时拉取）| **KEEP_SERVER** | `KEEP_SERVER` | platforms | 低 |
| S-084 | `POST /v1/batch/resolve` | 批量资源识别 | **KEEP_SERVER** | `KEEP_SERVER` | platforms | 低 |
| S-085 | `GET /v1/version` | 客户端更新检查 | **KEEP_SERVER** | `KEEP_SERVER` | - | 低 |

### 1.9 下载解析（需新建）

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| S-090 | **不存在** | Download Resolve API（返回 DownloadDescriptor）| **RD Server（新建）** | `REFACTOR_SERVER` | platforms, License, Quota | 高：核心新能力 |
| S-091 | **不存在** | Streaming Proxy API（必要时转发，不落盘）| **RD Server（新建）** | `REFACTOR_SERVER` | platforms | 中 |

---

## 2. 客户端组件审计

### 2.1 当前已具备

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| C-001 | `client/desktop/main.py` `WindowApi.api_request` | 统一 HTTP 请求（带 Device Proof 签名）| **KEEP_CLIENT** | `KEEP_CLIENT` | device_proof.py | 低 |
| C-002 | `client/desktop/device_identity.py` | Device Identity 生命周期（DPAPI ED25519）| **KEEP_CLIENT** | `KEEP_CLIENT` | Windows DPAPI | 低 |
| C-003 | `client/desktop/device_proof.py` | LS-DEVICE-V3 Proof 生成 | **KEEP_CLIENT** | `KEEP_CLIENT` | license_service_client wheel | 低 |
| C-004 | `client/desktop/main.py` `WindowApi.download_file` | `GET /v1/files/{id}` 文件下载（当前依赖 Server）| **CLIENT（迁移中）** | `MOVE_TO_CLIENT` | S-090 DownloadDescriptor | 高 |
| C-005 | `client/ui/app.js` `apiFetch` | 统一 UI API 调用（search/detail/jobs/files/automation）| **KEEP_CLIENT（部分需更新端点）** | `NEEDS_REVIEW` | 下游端点变化 | 中 |

### 2.2 当前缺失（需新增）

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| C-010 | **缺失** | 本地 DownloadTask 数据结构和创建逻辑 | Desktop Client | `ADD_CLIENT` | C-015 SQLite | 高 |
| C-011 | **缺失** | 下载队列（Queue）本地实现 | Desktop Client | `ADD_CLIENT` | C-010 | 高 |
| C-012 | **缺失** | 下载进度（Progress）本地跟踪 | Desktop Client | `ADD_CLIENT` | C-010 | 高 |
| C-013 | **缺失** | 下载暂停/恢复（Pause/Resume）本地实现 | Desktop Client | `ADD_CLIENT` | C-010 | 高 |
| C-014 | **缺失** | 下载重试（Retry）本地实现 | Desktop Client | `ADD_CLIENT` | C-010 | 高 |
| C-015 | **缺失** | 本地 SQLite（DownloadTask / History）| Desktop Client | `ADD_CLIENT` | - | 高 |
| C-016 | **缺失** | 下载历史（Download History）本地持久化 | Desktop Client | `ADD_CLIENT` | C-015 | 高 |
| C-017 | **缺失** | 断点续传（Range 续传）本地实现 | Desktop Client | `ADD_CLIENT` | C-010 | 中 |
| C-018 | **缺失** | 本地文件命名 / 下载目录管理 | Desktop Client | `ADD_CLIENT` | C-010 | 中 |
| C-019 | **缺失** | 本地文件索引（已完成文件列表）| Desktop Client | `ADD_CLIENT` | C-015 | 中 |
| C-020 | **缺失** | Client Timer / 热榜轮询 / 上新轮询 | Desktop Client | `ADD_CLIENT` | `GET /v1/discover` | 中：代替 Server Automation |
| C-021 | **缺失** | Client Notification（下载完成通知）| Desktop Client | `ADD_CLIENT` | C-010 | 低 |

### 2.3 当前 UI 绑定（不修改视觉，只调整 ViewModel）

| ID | Current Component | Current Responsibility | Target Owner | Action | Dependencies | Risk |
|----|-------------------|------------------------|--------------|--------|--------------|------|
| C-030 | `client/ui/app.js` Jobs 轮询 | 轮询 `GET /v1/jobs/{id}` Server 端状态 | Client 本地任务状态 | `MOVE_TO_CLIENT` | C-015, C-012 | 高：UI 依赖当前 Server API |
| C-031 | `client/ui/app.js` Files 列表 | 调用 `GET /v1/files` Server 文件列表 | Client 本地文件索引 | `MOVE_TO_CLIENT` | C-019 | 高 |
| C-032 | `client/ui/app.js` 下载触发 | 调用 `POST /v1/jobs` 创建 Server Job | Client DownloadManager + RD Resolve | `MOVE_TO_CLIENT` | S-090, C-010 | 高 |
| C-033 | `client/ui/app.js` Automation UI | 调用 `/v1/automation/hongguo-new` Server Scheduler | Client Timer 配置 | `MOVE_TO_CLIENT` | C-020 | 中 |

---

## 3. 汇总统计

以下计数通过对全部 65 个有 ID 编号的条目（S-xxx、C-xxx）逐行统计 Action 列得出。

| Action | 数量 | 主要组件 |
|--------|------|----------|
| `KEEP_SERVER` | 23 | platforms/, license, quota, sign_pool, search/detail/discover API, media_cache, ORM |
| `KEEP_CLIENT` | 3 | api_request, device_identity, device_proof |
| `MOVE_TO_CLIENT` | 12 | JobManager, JobRecord, job JSON, outputs/, HongguoMonitorService, run_loop, automation JSON, download_file, Jobs 轮询, Files 列表, 下载触发, Automation UI |
| `REFACTOR_SERVER` | 2 | Download Resolve API, Streaming Proxy |
| `REMOVE` | 0 | — |
| `DEPRECATE_API` | 12 | /v1/jobs(POST/GET/DELETE/retry/batch/queue), /v1/files(list/download/open), /v1/automation |
| `ADD_CLIENT` | 12 | DownloadTask, Queue, Progress, Pause/Resume, Retry, SQLite, History, 断点续传, 文件命名, 文件索引, Client Timer, Notification |
| `NEEDS_REVIEW` | 1 | apiFetch endpoint binding |
| **合计** | **65** | |

> 校验：23+3+12+2+0+12+12+1 = **65** ✅

---

## 4. 风险等级汇总

| 风险 | 项目 | 说明 |
|------|------|------|
| 🔴 高 | S-001, S-005~S-011, S-030~S-034, S-090, C-004, C-010~C-016, C-030~C-033 | UI 当前依赖 Server Job/File API；迁移需等价替代建立后才能切换 |
| 🟡 中 | S-031, S-041, S-090, S-091, C-017~C-018, C-020 | 功能复杂或当前缺失，需新建 |
| 🟢 低 | S-040, S-050~S-076, S-080~S-085, C-001~C-003 | 已明确保留或仅兼容性 |

---

## 5. 代码迁移原则（引自 ARCHITECTURE_BOUNDARY.md §16）

> 1. 先识别当前 UI 和业务依赖；
> 2. 在 Client Application / Data 层建立等价能力；
> 3. 保持现有 UI Contract（视觉不变）；
> 4. 完成 Client 侧功能；
> 5. 切换 API；
> 6. 验证行为等价；
> 7. 再移除 Server 旧实现。
>
> 禁止为了快速"瘦服务端"导致 UI 功能缺失、下载历史丢失或用户流程退化。

---

## 6. 主要架构漂移发现

本次只读审计发现的主要与 ARCHITECTURE_BOUNDARY.md 冲突点：

| # | 漂移描述 | 受影响组件 | 标记 |
|---|----------|-----------|------|
| D-01 | Server 持久化用户 Download Job（`data/jobs/*.json`）| `server/app/jobs/manager.py` | IMPLEMENTATION_MIGRATION_REQUIRED |
| D-02 | Server 将下载文件落盘至 `data/outputs/`（MP4/TXT）| 所有 platform download() | IMPLEMENTATION_MIGRATION_REQUIRED |
| D-03 | Server Automation Scheduler 在后台轮询红果上新 | `server/app/automation/hongguo_monitor.py` | IMPLEMENTATION_MIGRATION_REQUIRED |
| D-04 | `/v1/files` API 暴露 Server 文件库 | `server/app/api/router.py` | DEPRECATE_API |
| D-05 | Client 当前无本地 DownloadManager / SQLite / History | `client/desktop/` | ADD_CLIENT（缺失） |
| D-06 | Client 当前通过 `/v1/jobs` 创建 Server Job 而非本地任务 | `client/ui/app.js` | MOVE_TO_CLIENT |
| D-07 | Client 当前无 Client Timer，热榜/上新由 Server Automation 驱动 | `server/app/automation/` | IMPLEMENTATION_MIGRATION_REQUIRED |

---

## 7. 下一步（T42）

T42 IMPLEMENTATION MIGRATION PLAN 将基于本清单制定：

1. **Phase A（契约与现状审计）**：定义 DownloadDescriptor API，明确 UI 对旧 API 的依赖清单
2. **Phase B（Client Download Manager）**：本地任务 / Queue / Progress / Retry / SQLite / History
3. **Phase C（Server Download Resolution）**：Resolve API / Streaming Proxy / Quota/Idempotency
4. **Phase D（API 切换）**：ViewModel 改接新能力；旧 `/jobs`/`/files`/Automation 进入 Deprecated
5. **Phase E（移除旧 Server 职责）**：Server Download Worker / JobFile / Server Automation / History

---

*本文档随迁移执行更新。本轮 T41 不修改任何业务代码。*

## 8. 连续迁移执行状态

| Task | Status | Delivered |
| T44 execution note | PASS | Client UI and native bridge now use the Client DownloadManager/SQLite path; legacy Server Job/File responsibilities remain deferred to later migration tasks |
| T45 execution note | PASS | Client Discovery Timer now owns persisted hot/new polling, non-reentrant backoff, local baseline/deduplication and optional Client Resolve auto-enqueue; Server Automation Scheduler is no longer used by Desktop UI |
|------|--------|-----------|
| T42 | PASS | DownloadDescriptor、受保护 `/v1/resolve`、短生命周期 Streaming Proxy ticket、Client SQLite/Repository/Download Manager 基础设施；旧 Job/File/Automation 暂保留 |
| T43 | PASS | Client queue/concurrency, progress, pause/resume, retry, cancel, restart recovery, SQLite history, local file validation/index, Client Timer foundation and UI compatibility bridge |
| T44 | PENDING | — |
| T45 | PENDING | — |
| T46 | PENDING | — |
| T47 | PENDING | — |
