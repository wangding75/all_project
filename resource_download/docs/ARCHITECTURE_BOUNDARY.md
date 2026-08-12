# RD Server / Desktop Client 权威架构边界

**文档状态：NORMATIVE / FROZEN**
**适用项目：Resource Download（RD）**
**生效日期：2026-08-12**
**文档目的：作为后续产品、架构、API、客户端、服务端和发布验收的唯一职责边界基线。**

---

## 1. 产品定位

Resource Download 由两部分组成：

1. **RD Server**：负责 Hongguo、Fanqie 平台适配、资源解析、必要请求转发，以及 License、Quota 等必须由服务端可信执行的管理能力。
2. **Desktop Client**：负责用户侧下载产品能力，包括下载任务、队列、进度、重试、断点续传、本地文件存储、下载历史、定时查询和本地状态管理。

核心原则：

> **服务端资源有限，能够安全、可靠地在客户端完成的能力，原则上全部放在客户端。**

RD Server 的核心价值不是“代替客户端下载文件”，而是：

> **集中承载 Hongguo / Fanqie App 升级、私有协议、Frida、Hook、签名、Session、Java Bridge 等平台兼容性问题，对客户端提供稳定 API。**

---

## 2. “瘦客户端”正式定义

“瘦客户端”不代表客户端功能少。

在 RD 项目中，“瘦客户端”仅表示：

> **Desktop Client 不直接承担 Hongguo / Fanqie 的平台私有兼容逻辑。**

以下能力不得进入客户端：

- Hongguo App 私有协议适配；
- Fanqie App 私有协议适配；
- Frida；
- Hook；
- Java Bridge；
- App 私有签名逻辑；
- App Session 抓取与恢复；
- 平台版本兼容 Patch；
- 平台私有 Runtime；
- 平台升级后的逆向兼容处理；
- 服务端私钥和平台长期敏感凭据。

以下能力应由客户端承担：

- 下载任务；
- 下载队列；
- 下载并发；
- 下载进度；
- 暂停；
- 恢复；
- 重试；
- 断点续传；
- 本地文件存储；
- 文件命名；
- 下载目录管理；
- 下载历史；
- 本地文件索引；
- 本地 SQLite；
- 打开文件；
- 打开目录；
- 删除本地记录；
- 本地任务管理；
- 定时刷新；
- 热榜轮询；
- 上新轮询；
- 客户端通知；
- UI 状态管理。

---

## 3. UI 冻结原则

本次架构调整是：

> **Server → Client 的能力归属迁移，不是 UI 重做。**

必须保持现有 Desktop UI 的：

- 视觉设计；
- 页面结构；
- 信息架构；
- 主要交互流程；
- 用户心智；
- 下载入口；
- 下载列表表现；
- 进度表现；
- 历史记录表现。

典型用户流程保持不变：

```text
搜索
→ 查看详情
→ 选择资源
→ 点击下载
→ 查看下载进度
→ 查看下载记录
→ 打开本地文件
```

允许修改的仅是 UI 背后的：

- ViewModel；
- Application 层；
- Data 层；
- Download Manager；
- Local Repository；
- Local SQLite；
- API 调用方式。

只有现有 UI 无法表达迁移后必须存在的业务状态时，才允许进行**最小功能性 UI 调整**。

禁止借本次架构迁移进行：

- UI 重设计；
- 页面重构；
- 视觉风格调整；
- 无关交互改版。

---

## 4. RD Server 正式职责

### 4.1 Hongguo / Fanqie 平台适配

RD Server 负责：

- Hongguo App 对接；
- Fanqie App 对接；
- Frida Runtime；
- Java Bridge；
- Hook；
- 签名；
- Session 获取与恢复；
- 平台请求构造；
- 平台响应解析；
- App 版本兼容；
- 平台异常映射；
- 私有协议变化适配。

客户端不得直接依赖这些实现。

### 4.2 稳定资源 API

RD Server 对 Client 暴露稳定、平台无关的业务接口，例如：

- 搜索；
- 详情；
- 章节；
- 剧集；
- 今日热榜；
- 排行榜；
- 最新；
- 上新；
- 推荐；
- 下载资源解析。

客户端只依赖 RD 的稳定 API Contract，不直接感知 Hongguo / Fanqie App 内部接口变化。

### 4.3 License / Entitlement / Quota

RD Server 负责：

- Device Proof 校验；
- 调用 License Service；
- License 状态判定；
- Entitlement 获取；
- RD 业务额度解释；
- Quota 权威计量；
- 幂等控制；
- 最终业务放行。

商业使用量以 `license_id` 为主体。

License Service 仍是 License 状态唯一事实源。

RD Server 不得直接访问 License Service PostgreSQL。

### 4.4 必要的请求转发

下载链路优先采用：

```text
Client
→ RD Server 解析
← DownloadDescriptor
Client
→ Upstream/CDN
→ Client 本地文件
```

当以下情况导致客户端无法安全直接访问上游时：

- 需要服务端 Session；
- 需要服务端临时签名；
- 需要私有 Header；
- 不允许向客户端暴露 Cookie / Token；
- 请求与 App Runtime 强绑定；
- 直接访问会暴露平台私有兼容实现；

允许采用：

```text
Client
→ RD Server Streaming Proxy
→ Upstream
→ RD Server Streaming Proxy
→ Client
```

Streaming Proxy 必须满足：

- 边读取边转发；
- 不保存完整文件；
- 不建立永久缓存；
- 不写入服务端下载目录；
- 不创建服务端文件记录；
- Client 断开后及时释放上游连接；
- 设置合理 Timeout；
- 支持 Backpressure；
- 上游支持时尽量透传 HTTP Range。

---

## 5. RD Server 明确禁止职责

RD Server 不负责：

- 下载文件落盘；
- 下载结果永久存储；
- 服务端文件库；
- `JobFile`；
- 服务端下载目录；
- `/v1/files` 型文件管理；
- 客户端本地路径；
- 客户端下载历史；
- 客户端下载进度；
- 下载队列；
- 下载暂停；
- 下载恢复；
- 断点续传状态；
- 下载完成后的文件索引；
- 本地文件打开；
- 本地文件删除；
- 持久化 Download Job 管理；
- 自动追更任务；
- 自动下载任务；
- 定时热榜任务；
- 定时上新任务；
- 服务端 Automation Scheduler；
- 服务端后台轮询；
- 服务端长期媒体缓存。

现有代码中如果仍存在上述职责，统一视为：

`IMPLEMENTATION_MIGRATION_REQUIRED`

---

## 6. Desktop Client 正式职责

Desktop Client 是完整的本地下载产品。

### 6.1 Download Manager

Client 负责：

- 创建本地下载任务；
- 下载队列；
- 并发控制；
- 下载进度；
- 暂停；
- 恢复；
- 重试；
- 断点续传；
- 超时；
- 失败状态；
- 本地文件校验；
- 本地文件命名；
- 下载目录选择。

### 6.2 本地持久化

Client 本地数据库负责：

- 下载任务；
- 下载历史；
- 本地文件路径；
- 文件名；
- 文件大小；
- 下载状态；
- 进度；
- 创建时间；
- 完成时间；
- 重试次数；
- 错误信息；
- 用户本地历史状态。

推荐使用本地 SQLite。

### 6.3 定时查询

例如：

- 今日热榜；
- 排行榜；
- 最新；
- 上新；
- 推荐；
- 用户关注内容刷新。

采用：

```text
Client Timer
→ RD Server API
→ Hongguo / Fanqie 实时数据
→ Client
```

Server 不建立对应后台 Scheduler。

Client 根据产品需求按分钟、小时或用户操作周期主动查询。

---

## 7. 下载数据流

### 7.1 Direct Download

首选模式：

```text
Desktop Client
    │
    │ Device Proof + Resource Request
    ▼
RD Server
    │
    ├─ License Check
    ├─ Quota
    ├─ Hongguo / Fanqie Adapter
    ├─ Resolve
    └─ Sign
    │
    ▼
DownloadDescriptor
    │
    ▼
Desktop Download Manager
    │
    ▼
Upstream / CDN
    │
    ▼
Local File System
    │
    ▼
Client SQLite
```

### 7.2 Streaming Proxy

仅在必要时：

```text
Desktop Client
    ↓
RD Streaming Proxy
    ↓
Upstream
    ↓
RD Streaming Proxy
    ↓
Desktop Client
    ↓
Local File System
```

即使经过 RD Server：

> **文件最终仍只落在客户端。**

---

## 8. DownloadDescriptor

RD Server 负责把平台私有下载信息转换成稳定的 `DownloadDescriptor`。

建议表达：

- `platform`
- `resource_id`
- `title`
- `media_type`
- `suggested_filename`
- `expires_at`
- `download_mode`

`download_mode`：

- `direct`
- `proxy`

Direct 模式可携带：

- URL；
- HTTP Method；
- 可安全返回客户端的临时 Header。

Proxy 模式返回：

- RD Proxy URL；
- 短期 Ticket / Request Token。

禁止返回客户端：

- Hongguo / Fanqie 长期私有 Cookie；
- App Session Secret；
- Frida Runtime Secret；
- RD Server Private Key；
- License Service Private Credential；
- 其他长期敏感平台凭据。

---

## 9. 下载任务归属

Server 不再拥有持久化 Download Job。

Client 拥有本地 `DownloadTask`。

建议字段：

```text
task_id
platform
resource_id
title
local_path
status
progress
total_bytes
downloaded_bytes
created_at
completed_at
retry_count
error
```

如果服务端内部为了完成一次解析请求需要短生命周期 Request Context，可以存在于请求生命周期或短期缓存中，但不得演化成：

- 用户下载队列；
- 长期 Job；
- 下载历史；
- 文件记录。

---

## 10. 下载记录归属

下载记录：

> **只保存在 Desktop Client。**

RD Server 不保存：

- `local_path`
- `filename`
- `downloaded_bytes`
- `download_progress`
- `completed_at`
- 文件打开记录
- 文件删除记录
- 用户本地文件列表
- Client 下载历史

---

## 11. Quota 规则

Quota 属于 RD Server 可信控制面。

商业主体：

```text
license_id
```

客户端最终是否真的将文件写入本地，不是服务端可信计费依据。

原则：

> **一次合法资源下载授权成功签发时进行服务端额度计量。**

必须具备：

- Idempotency；
- 重试不重复扣额度；
- 同一逻辑请求重复提交不重复计量；
- 并发安全；
- License 状态变化后 Fail-Closed。

具体计费时点以最终 API 契约和代码迁移设计为准，但不得由 Client 自报使用量。

---

## 12. Server 数据持久化边界

RD Server 仅允许保存必须由服务端可信维护的控制面数据，例如：

- Quota Usage；
- Idempotency；
- 必要安全状态；
- 必要审计状态；
- Schema / Migration Metadata；
- 必要的短期平台 Runtime Metadata。

禁止保存：

- 下载文件；
- JobFile；
- 下载历史；
- Client 文件路径；
- Client 下载队列；
- Client 下载进度；
- Client Automation 状态；
- Client 本地任务状态。

---

## 13. License Service 边界

固定链路：

```text
Desktop Client
    │ Device Proof
    ▼
RD Server
    │ Service Auth
    ▼
License Service
```

License Service 负责：

- Plan；
- Plan Version；
- Activation Code；
- License；
- Device Binding；
- `max_devices`；
- Expiry；
- Revoke；
- Entitlement。

RD Server 负责：

- 调用 License Service；
- RD Entitlement 解释；
- RD Quota；
- 最终业务放行。

Client 不具有最终授权裁决权。

---

## 14. Server Runtime 环境

生产部署只考虑：

> **一台 Android 模拟器。**

不建立多模拟器调度系统。

不使用历史固定端口作为设备身份。

Server Startup Preflight 至少确认：

- ADB 可用；
- 存在一台可用 Android Device；
- Android Boot Completed；
- Fanqie 已安装；
- Hongguo 已安装；
- Frida / Runtime 基础能力存在；
- RD Control Database 可用；
- License Service 可访问。

ADB Port 可以随模拟器重启变化。

禁止将：

- `7555`
- `16384`

写成长期设备身份。

---

## 15. API 分类

RD Server API 应逐步收敛为以下类别。

### 15.1 Control API

- Health
- Ready
- License
- Quota

### 15.2 Platform Resource API

- Search
- Detail
- Chapters / Episodes
- Ranking
- Latest
- Discovery
- Recommendation

### 15.3 Download Resolution API

- Resolve
- Direct Download Descriptor
- Streaming Proxy

以下类型 API 应退出服务端长期职责：

- Server Download Job API
- Server File API
- Server Download History API
- Server Automation API
- Server Scheduler API

旧 API 在迁移期可以暂时存在，但必须标记：

`DEPRECATED / MIGRATION_REQUIRED`

---

## 16. 当前实现迁移原则

现有代码中属于服务端的以下能力：

- Download Job；
- JobFile；
- Server Download Worker；
- File API；
- Server Output Directory；
- Media Cache；
- Automation；
- Scheduler；
- Download History；

不能简单删除。

迁移规则：

1. 先识别当前 UI 和业务依赖；
2. 在 Client Application / Data 层建立等价能力；
3. 保持现有 UI Contract；
4. 完成 Client 侧功能；
5. 切换 API；
6. 验证行为等价；
7. 再移除 Server 旧实现。

禁止为了快速“瘦服务端”导致：

- UI 功能缺失；
- 下载历史丢失；
- 下载进度缺失；
- Retry / Resume 被删除；
- 用户流程退化。

这是**职责迁移**，不是功能删减。

---

## 17. 迁移后的目标结构

```text
Desktop Client
├─ Existing UI
├─ ViewModel / Application
├─ Resource API Client
├─ Download Manager
├─ Queue / Concurrency
├─ Retry / Resume
├─ Progress
├─ Local SQLite
├─ Download History
├─ Local File Manager
└─ Polling / Timer

RD Server
├─ API
├─ License Gateway
├─ Quota
├─ Idempotency
├─ Platform Abstraction
│  ├─ Hongguo
│  └─ Fanqie
├─ Frida / Hook / Bridge
├─ Sign / Session Runtime
├─ Resource Resolver
└─ Streaming Proxy

License Service
├─ Plan
├─ Activation Code
├─ License
├─ Device Binding
├─ Entitlement
└─ PostgreSQL
```

---

## 18. 服务端资源原则

服务端资源优先用于：

- Hongguo / Fanqie App Runtime；
- Frida；
- Hook；
- Java Bridge；
- 平台签名；
- 平台协议适配；
- 实时查询；
- 资源解析；
- 必要 Streaming Proxy；
- License；
- Quota；
- Security。

能由 Desktop Client 完成的长期状态和计算，原则上不占用 Server：

- 磁盘；
- 长期内存；
- 后台 Scheduler；
- 文件库；
- 用户下载历史；
- 下载任务数据库。

---

## 19. 非目标

本架构调整明确不包括：

- 重做 Desktop UI；
- 改变现有视觉设计；
- 改变主要用户流程；
- 把 Hongguo / Fanqie 私有逻辑迁到 Client；
- 在 Server 建立新的文件存储系统；
- 在 Server 建立新的下载 Scheduler；
- 在 Server 建立新的媒体文件数据库；
- 让 Client 自行判定 License 是否有效。

---

## 20. 变更优先级

后续实现按以下顺序执行：

### Phase A — 契约与现状审计
- 盘点旧 Job / File / Automation / Media Cache；
- 明确 UI 对旧 API 的依赖；
- 定义新 DownloadDescriptor；
- 定义 Client Local DownloadTask。

### Phase B — Client Download Manager
- 本地任务；
- Queue；
- Progress；
- Retry；
- Resume；
- Local SQLite；
- History。

### Phase C — Server Download Resolution
- Resolve API；
- Direct Descriptor；
- Streaming Proxy；
- Quota / Idempotency。

### Phase D — API 切换
- UI 保持不变；
- ViewModel / Application 改接新能力；
- 旧 `/jobs`、`/files`、Automation API 进入 Deprecated。

### Phase E — 移除旧 Server 职责
- Server Download Worker；
- JobFile；
- Server File Storage；
- Automation；
- Scheduler；
- Download History。

### Phase F — 真实平台验收
- Fanqie；
- Hongguo；
- Direct Download；
- Streaming Proxy；
- Restart；
- App Upgrade Compatibility；
- License / Quota。

---

## 21. 架构判定规则

后续任何新增功能使用以下规则判断归属：

### 放 Client

如果该能力：

- 只影响当前用户本机；
- 不需要可信服务端裁决；
- 不依赖 Hongguo / Fanqie 私有兼容实现；
- 能安全由本地执行；
- 会长期消耗 Server CPU / 内存 / 磁盘；

则优先放 Client。

### 放 Server

如果该能力：

- 依赖 Hongguo / Fanqie 私有协议；
- 依赖 App Runtime；
- 依赖 Frida / Hook / Sign；
- 涉及敏感平台凭据；
- 涉及 License / Quota；
- 必须作为可信控制面；
- 必须集中处理版本兼容；

则放 RD Server。

---

## 22. 最终冻结结论

### RD Server

> **平台兼容与可信控制服务。**

主要职责：

- Hongguo / Fanqie 对接；
- 实时资源解析；
- 必要请求转发；
- Streaming Proxy；
- License；
- Quota；
- Idempotency；
- 安全控制。

### Desktop Client

> **完整本地下载产品。**

主要职责：

- 保持现有 UI；
- 下载任务；
- 队列；
- 进度；
- 重试；
- 断点续传；
- 文件存储；
- 下载历史；
- 本地数据库；
- 定时查询；
- 本地通知。

### 最终原则

> **平台兼容集中到 Server。**

> **用户本地能力尽量留在 Client。**

> **Server 不存下载文件，不管理用户下载任务，不做自动化 Scheduler。**

> **Client UI 保持现状，迁移的是 UI 后面的能力归属。**

---

**本文件为 RD 后续架构、开发、Review、迁移和 Release Gate 的权威基线。任何实现、README、API 文档、开发计划和测试规范与本文件冲突时，应先修正文档或实现，使其与本文件一致。**

---

## 17. 关联文档（T41 落地）

| 文档 | 职责 |
|------|------|
| **本文（NORMATIVE / FROZEN）** | 权威架构边界 |
| [`ARCHITECTURE_MIGRATION_INVENTORY.md`](./ARCHITECTURE_MIGRATION_INVENTORY.md) | **T41 生成的代码迁移清单**（只读审计；T42 执行） |
| [`../README.md`](../README.md) | 项目入口（已向本文对齐） |
| [`../DEVELOPMENT_PLAN.md`](../DEVELOPMENT_PLAN.md) | 历史架构决策记录（已向本文对齐） |
| [`../POST_MVP_PLAN.md`](../POST_MVP_PLAN.md) | 阶段进度与 backlog（已向本文对齐） |
| [`../business_landing_architecture.md`](../business_landing_architecture.md) | Historical/Legacy Evidence（旧 User/JWT/CardKey 架构） |
| [`api.md`](./api.md) | API 契约（`/v1/jobs`、`/v1/files`、`/v1/automation/*` 已标记 DEPRECATED） |
| [`../client/README.md`](../client/README.md) | 客户端职责（已更新为 DownloadManager/SQLite/Timer） |

**T41 落地状态**：2026-08-12 ✅ 文档对齐完成；代码迁移待 T42。
