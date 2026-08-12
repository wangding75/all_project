# 多平台内容下载器 — 架构与计划定稿

> **⚠️ 本文档历史架构章节已由权威文档覆盖。**  
> **从 2026-08-12 起：[`docs/ARCHITECTURE_BOUNDARY.md`](./docs/ARCHITECTURE_BOUNDARY.md) 为 RD 架构最高优先级事实源（NORMATIVE / FROZEN）。**  
> **本文档与 ARCHITECTURE_BOUNDARY.md 冲突时，以 ARCHITECTURE_BOUNDARY.md 为准。**  
>
> **本文职责：锁定历史架构决策、非目标、API 原则记录。**  
> **阶段进度 / 剩余 backlog → [`POST_MVP_PLAN.md`](./POST_MVP_PLAN.md)。**  
> 旧版 `design_plan.md` 中与本文冲突的部分（本机一体化、全离线无签名等）以本文覆盖。

**定稿日期**：2026-07-18（客户端后置修订同日）  
**文档修订**：  
- 2026-07-27 — 进度以 POST_MVP_PLAN 为准（V1.0 主线已完成）  
- 2026-07-27 — **冻结 client/server 边界与目录组织（§0.1）**  
- 2026-08-12 — **[T41] 权威架构文档 ARCHITECTURE_BOUNDARY.md 纳入仓库，本文档向其对齐**

---

## 0. 已锁定决策

| 项 | 决策 |
|----|------|
| 总体架构 | **方案 2：完整本地下载产品（Desktop Client）+ 平台兼容中转服务端** |
| 红果 | **当前主路径**：复用 **`vendor/hongguo`**（不重写解密/取链） |
| 番茄 | **App 会话为主目标**；Web SSR 可作对照/免费章兜底，不作长期会员主路径 |
| 会话 | **服务端自养**；用户不贴 Cookie |
| 客户端 | **无平台适配**；完整本地下载产品（Download Manager、Local SQLite、History、Timer）|
| 验收方式 | **`scripts/e2e_hongguo.py` / `e2e_fanqie.py` 等** 打服务端 API |
| 产品优先级 | **服务端平台适配与 License 控制 → 客户端完整下载产品能力** |

### 0.1 客户端 / 服务端边界（冻结约定）

> **权威文件：[`docs/ARCHITECTURE_BOUNDARY.md`](./docs/ARCHITECTURE_BOUNDARY.md)（NORMATIVE / FROZEN）**  
> **本节为历史归档摘要。与权威文档冲突时，以权威文档为准。**

#### 目录组织（冻结）

```text
resource_download/
├── server/                 # 中转服务端（主战场）
│   ├── app/                # API / 鉴权 / License / Quota / 平台适配
│   ├── platforms/          # 番茄、红果等平台适配（Frida/签名仅此处）
│   └── run.py
├── client/                 # 完整本地下载产品
│   ├── ui/                 # Web UI：搜索/下载/历史/设置
│   ├── desktop/            # 桌面壳：Download Manager / Local SQLite / Timer
│   └── README.md
├── vendor/                 # 仅服务端依赖（如 hongguo），禁止打进桌面包
├── scripts/                # e2e / 运维 / 质量门禁
└── docs/
    ├── ARCHITECTURE_BOUNDARY.md       # ⭐ 权威架构边界
    └── ARCHITECTURE_MIGRATION_INVENTORY.md  # 代码迁移清单
```

#### 服务端（server/）— 允许

| 允许 | 说明 |
|------|------|
| 平台协议适配与热修 | App 更新后只改服务端 |
| 签名 / 解密 / Frida / 设备或签名池 | 履约能力 |
| 资源解析与 DownloadDescriptor | 平台私有信息转稳定契约 |
| 必要 Streaming Proxy（不落盘）| 当直接下载不可行时 |
| License / Quota / Idempotency | 可信控制面 |
| 搜索 / 详情 / 章节 / 排行榜 / 上新 / 发现 | 平台无关稳定 API |
| 挂载 `client/ui` 为静态 `/ui` | 便于同源部署 |

#### 服务端 — 禁止（边界）

| 禁止 | 说明 | 状态 |
|------|------|------|
| 下载文件落盘 | 文件只在客户端 | **FORBIDDEN** |
| 持久化 Download Job（用户队列）| 任务管理属于客户端 | **IMPLEMENTATION_MIGRATION_REQUIRED** |
| Server Download History | 历史记录属于客户端 | **FORBIDDEN** |
| Server Automation Scheduler | 定时查询属于客户端 Timer | **IMPLEMENTATION_MIGRATION_REQUIRED** |
| `/v1/files` 长期文件库 | 不是 Server 职责 | **DEPRECATE_API** |
| 把适配逻辑泄漏到 client 目录 | 不得在 client 下出现 platforms / frida 业务 | **FORBIDDEN** |

#### 客户端（client/）— 允许

| 允许 | 说明 |
|------|------|
| 登录 / 激活（Device Proof + License） | 通过 RD Server |
| DownloadTask / 下载队列 / 并发控制 | 完整 Download Manager |
| 下载进度 / 暂停 / 恢复 / 重试 / 断点续传 | 本地任务管理 |
| 本地文件存储 / 文件命名 / 下载目录 | 只落在客户端 |
| 本地 SQLite / 下载历史 / 文件索引 | 本地持久化 |
| Client Timer / 定时刷新 / 热榜轮询 / 上新轮询 | 代替 Server Automation |
| 搜索/详情/建任务/进度（经 API） | 调用服务端 API |
| **排行榜 / 热榜 / 上新** 等产品 UI | 数据来自服务端 API，轮询由 Client Timer 驱动 |
| 本地偏好、通知 | 无平台协议 |

#### 客户端 — 禁止（硬边界）

| 禁止 | 说明 |
|------|------|
| `platforms/*` 适配代码 | 不得出现在 client |
| Frida / 签名 / 解密 / 本机模拟器业务 | 履约仅服务端 |
| 依赖 `vendor/hongguo` 或设备侧 agent | |
| 以「用户本机 Frida」为生产主路径 | 开发机调试除外且不得进产品包 |

#### 数据流（含榜单类功能）

```text
# 热榜 / 上新 / 发现（Client Timer 驱动）
Client Timer
→ 客户端请求 RD Server API
→ 服务端实时获取 Hongguo / Fanqie 数据
→ Client 渲染

# 下载（首选 Direct）
Client DownloadManager
→ RD Server Resolve（License/Quota 校验）
← DownloadDescriptor
→ Upstream/CDN 直接下载
→ Client 本地文件 / SQLite

# 下载（Streaming Proxy fallback）
Client → RD Streaming Proxy → Upstream → Client → 本地文件
（Proxy 不落盘、不建 JobFile、不保存历史）
```

#### 启动约定

| 模式 | 命令 / 环境 | 用途 |
|------|-------------|------|
| 服务端 | `cd server ; python run.py` | 生产 / 开发中转 |
| 桌面客户端 | `API_BASE=http://host:8000` + `python client/desktop/main.py` | 用户侧 |
| 浏览器客户端 | 打开 `http://host:8000/ui/` | 同桌面客户端 |
| 本机一体演示 | `CLIENT_MODE=embedded` | **仅开发**，非生产分发形态 |

### 架构示意

```text
┌─────────────────────────────────┐         HTTPS API          ┌──────────────────────────────────┐
│  Desktop Client（完整下载产品）    │  搜索/详情/Resolve/Quota    │  server/（平台兼容服务端）          │
│  DownloadManager / SQLite        │ ────────────────────────► │  License / Quota / Idempotency    │
│  Queue/Retry/Progress/History    │ ◄── DownloadDescriptor ── │  platforms/* Frida/Sign/Session   │
│  Client Timer（定时轮询）         │                           │                                  │
│  无 Frida / 无 platforms         │                           └──────────────────────────────────┘
└─────────────────────────────────┘                                          │
                                                                    License Service (rd Tenant)
```

主路径在 **服务端**平台适配；下载产品能力在 **客户端**。

---

## 1. 目标与非目标

### 1.0 MVP 分层（验收口径）

| 级别 | 范围 | 完成标准 |
|------|------|----------|
| **MVP-H（历史）** | relay + **复用 hongguo** + `e2e_hongguo` | 签名/config 就绪下，脚本出可播 **MP4** |
| **MVP-F（历史）** | 番茄 App 会话接入 | 脚本出书 |
| **V1.0（历史）** | 商业化 + License + UI 闭环 | release_gate 全勾 |
| **T41（当前）** | 权威架构文档落地 + 代码迁移清单 | ARCHITECTURE_BOUNDARY.md 生效 |

### 1.1 主里程碑

1. **服务端**可独立部署：HTTP API + DownloadDescriptor + Streaming Proxy。  
2. **番茄（MVP-F）**：URL/ID → 详情 → Resolve → DownloadDescriptor → 客户端下载 TXT。  
3. **红果（MVP-H）**：搜索/详情 → Resolve → 解密 **MP4** → 客户端下载。  
4. **`scripts/`** 覆盖上述端到端。

### 1.2 后置目标

5. **Client Download Manager**：本地任务 / Queue / Progress / Retry / Local SQLite。  
6. **Download Resolution API**：DownloadDescriptor / Streaming Proxy。  
7. **Server Job / Automation 退出**：按 ARCHITECTURE_MIGRATION_INVENTORY.md 执行。

### 1.3 非目标（架构层面）

- 重做 Desktop UI（UI 冻结，只改 ViewModel/Data 层）
- 把 Hongguo / Fanqie 私有逻辑迁到 Client
- 在 Server 建立新的文件存储 / 下载 Scheduler / 媒体数据库
- 让 Client 自行判定 License 是否有效

---

## 2. 仓库与模块结构（目标态）

```text
resource_download/
├── docs/
│   ├── ARCHITECTURE_BOUNDARY.md          # ⭐ 权威架构边界（NORMATIVE/FROZEN）
│   └── ARCHITECTURE_MIGRATION_INVENTORY.md  # 代码迁移清单
├── DEVELOPMENT_PLAN.md          # 本文：历史决策记录
├── server/                      # 中转服务端
│   ├── app/                     # API / 鉴权 / License / Quota
│   ├── platforms/               # fanqie | hongguo 适配（仅服务端）
│   └── run.py
├── client/                      # 完整本地下载产品
│   ├── ui/                      # Web UI：搜索/下载/历史
│   ├── desktop/                 # 桌面壳（Download Manager / SQLite / Timer）
│   └── README.md
├── scripts/                     # e2e / build / 运维 / quality_gate
├── docs/
├── vendor/
│   └── hongguo/                 # 仅服务端；勿进桌面包
└── data/                        # 运行时（gitignore）
```

---

## 3. 统一 API 契约（服务端对外）

> **当前目标 API 分类详见 [`docs/ARCHITECTURE_BOUNDARY.md`](./docs/ARCHITECTURE_BOUNDARY.md) §15。**

| 方法 | 路径 | 分类 | 说明 |
|------|------|------|------|
| GET | `/health` | KEEP_SERVER | 健康检查 |
| GET | `/v1/search` | KEEP_SERVER | 搜索 |
| GET | `/v1/detail` | KEEP_SERVER | 详情 |
| GET | `/v1/discover` | KEEP_SERVER | 发现/热榜/上新 |
| POST | `/v1/resolve` | REFACTOR_SERVER | Download Resolve（目标） |
| GET/POST | `/v1/proxy/*` | REFACTOR_SERVER | Streaming Proxy（目标） |
| POST | `/v1/jobs` | DEPRECATE_API | **[MIGRATION_REQUIRED]** Server Job 创建，当前仍在；目标由 Client 管理 |
| GET | `/v1/jobs/{job_id}` | DEPRECATE_API | **[MIGRATION_REQUIRED]** Server Job 状态 |
| GET | `/v1/files/{file_id}` | DEPRECATE_API | **[MIGRATION_REQUIRED]** Server 文件下载 |
| */v1/automation/* | DEPRECATE_API | **[MIGRATION_REQUIRED]** Server Automation Scheduler |

---

## 4. 分阶段计划（历史摘要 + 当前指针）

> 细任务维护在 [`POST_MVP_PLAN.md`](./POST_MVP_PLAN.md)。  
> T41 之后进入 T42 IMPLEMENTATION MIGRATION PLAN。

### 阶段回顾（完成状态）

| 原阶段 | 内容 | 备注 |
|--------|------|------|
| 0 | 骨架 + 契约 + smoke | 已完成 |
| 1～2 | 番茄 Web + E2E 脚本 | 已接入；App 模式另需设备 |
| 3 | 红果 vendor 适配 + E2E | 已完成 |
| 4 | 双平台脚本回归 | 已完成 |
| 5 | 客户端 V1.0 商业化 | 已完成（Login/License/UI 闭环）|
| D-E | License / Quota / 签名池 | 已完成 |
| T41 | 权威架构文档落地 | **当前** |
| T42 | IMPLEMENTATION MIGRATION PLAN | **下一步** |

---

## 5. 技术选型

| 层 | 选型 | 备注 |
|----|------|------|
| 服务端 | FastAPI + uvicorn | |
| 服务端 Job（当前实现） | 进程内队列 + JSON 文件 | IMPLEMENTATION_MIGRATION_REQUIRED；目标迁移到 Client |
| 番茄 | fonttools + brotli；App 路径 Frida 进程内解密 | |
| 红果 | pycryptodome + vendor/hongguo；签名外置 | |
| 验收 | **Python scripts + httpx** | 主验收面 |
| 桌面/Web UI | `ui/` 静态页挂载；桌面壳 PyWebView | UI 不变，改 ViewModel/Data/Download Manager |

---

## 6. 质量门槛

1. 每平台至少 1 条 **脚本可跑的 E2E**（非仅单元测试）。  
2. 红果 spade 真值测试保留。  
3. 密钥/token/Cookie 不入库。  
4. README / `scripts/README` 中的命令与真实行为一致。  
5. **不以「客户端做好了」为服务端完成标准**；以脚本 E2E 为准。  
6. **禁止用假成功掩盖 API 失败**。  

---

## 7. 决策备忘

| 问题 | 结论 |
|------|------|
| 客户端下载何时迁移？ | T42 IMPLEMENTATION MIGRATION PLAN；本轮（T41）只建清单 |
| 如何验收下载？ | **`scripts/` 请求 API**；Client Direct 链路待 T42 建立 |
| Server Job API 何时废弃？ | 待 Client Download Manager 建立后逐步切换（见 ARCHITECTURE_MIGRATION_INVENTORY） |
| 迭代任务写哪？ | **POST_MVP_PLAN.md**，本文只锁架构 |

---

## 8. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-18 | 初版：方案 2、番茄优先、红果对齐 hongguo |
| 2026-07-18 | **客户端后置**；主验收改为 scripts E2E；阶段重排 |
| 2026-07-18 | 标明 **MVP-1 / MVP-2**；落地 `server/` + `scripts/` 脚手架 |
| 2026-07-18 | **主路径改为红果**；`vendor/hongguo` 复用 + `platforms/hongguo` 适配 |
| 2026-07-27 | **冻结 §0.1**：client/server 目录与职责边界；`ui`/`desktop` → `client/` |
| 2026-07-27 | 与 POST_MVP_PLAN 分工；阶段详情归档；补质量门槛第 6 条 |
| 2026-08-12 | **[T41] ARCHITECTURE_BOUNDARY.md 纳入仓库**；本文历史 §0.1 向权威文档对齐；标记 Server Job/Automation/File API 为 DEPRECATE_API；明确 Client 拥有 Download Manager / SQLite / Timer |
