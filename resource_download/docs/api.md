# Relay API

Base URL: `http://127.0.0.1:8000`

> 契约以本文件 + 运行中的 OpenAPI（`/docs`）为准。

> **[T41 2026-08-12] 架构基线冻结。**  
> **权威架构文件：[`../docs/ARCHITECTURE_BOUNDARY.md`](./ARCHITECTURE_BOUNDARY.md)（NORMATIVE / FROZEN）**  
>
> API 分类方针：
> - **KEEP_SERVER**：health / search / detail / discover / license / quota — 长期属于服务端
> - **REFACTOR_SERVER**：Download Resolve / Streaming Proxy — 目标形态，待实现
> - **DEPRECATE_API**：`/v1/jobs`、`/v1/files`、`/v1/automation/*` — 目标由 Client 承担，本轮不删除
>
> `DEPRECATED` 接口在迁移期可以暂时存在，必须标记 `DEPRECATED / MIGRATION_REQUIRED`。

## RD Desktop Client cutover：Device Proof V3

正式 Desktop Client 使用 License Service `LS-DEVICE-V3`，通过 RD Server
完成完整链路：`Desktop Client → RD Server → License Service`。客户端不直接
调用 License Service，也不持有 RD Service Credential 或 License Service
Credential。`API_BASE` 只指向 RD Server；客户端没有 `LICENSE_SERVICE_BASE_URL`。

首次启动生成的 `ED25519` private/public key 由当前 Windows 用户 DPAPI 持久化，
`device_id = dev_ + SHA256(canonical_public_key_bytes)`。重启必须复用同一
identity；损坏时 fail-closed 为 `DEVICE_IDENTITY_INVALID`，不能静默换设备。
用户确认执行 Reset 后会生成新设备身份，License Service 会要求重新激活且可能
占用新的 device slot。

### Activation

`POST /v1/auth/redeem` 仍是 RD 对外激活入口。Desktop Client native bridge
发送 `card_code`、`device_id`、`device_key_algorithm`、`device_public_key` 和
Activation Proof；Proof 使用正式 canonical bytes，`audience=rd`，每次使用新的
timestamp/nonce。客户端不会调用 License Service `/v1/activate`。

### License-Protected request scope

以下请求由 Desktop Client 的统一 native HTTP 层自动添加五个
`X-Device-*` headers，并用最终发送的 raw body bytes 计算 hash：

```text
POST /v1/jobs
POST /v1/jobs/batch
POST /v1/jobs/queue/bulk/retry
POST /v1/jobs/{job_id}/retry
PUT  /v1/automation/hongguo-new
POST /v1/automation/hongguo-new/scan
```

签名覆盖 `METHOD`、最终 `PATH + QUERY`、`SHA256(raw body)`、`audience=rd`、
时间戳和 fresh nonce。Retry 会重新签名。登录、注册、搜索、详情、普通 Job
查询、files 和 health 不因本轮变成受保护请求。Automation 的 verified device
由 RD Server 从 Proof 得到；客户端不在 body 手填授权 device id。

普通浏览器没有设备私钥。浏览器触发 redeem 或受保护操作时必须 fail-closed，
返回/提示 `DESKTOP_DEVICE_IDENTITY_REQUIRED`，不得把 private key 放入
`localStorage`、`sessionStorage` 或 JavaScript source。

---

## 认证与身份鉴权（D-1）

除 **`/health`**、**`/`**、**`/ui`**（及静态资源）外，业务接口依赖统一身份层 `require_identity`。

### 配置（`.env`）

| 变量 | 默认 | 说明 |
|------|------|------|
| `AUTH_MODE` | `dev` | `dev` \| `dual` \| `jwt_only` |
| `API_KEY` | `dev-key-change-me` | 与请求头 `X-API-Key` 比对（仅限开发默认值） |
| `JWT_SECRET` | `change-me-jwt-secret` | 签名密钥；**勿用于生产默认值** |
| `JWT_EXPIRE_MINUTES` | `10080` | 7 天 |

### 模式行为

| AUTH_MODE | 有效凭证 | 说明 |
|-----------|----------|------|
| **dev** | `X-API-Key: <API_KEY>` | RD 开发/运维身份；不能绕过 Device License；忽略 Bearer Token |
| **dual** | `X-API-Key` **或** `Authorization: Bearer <token>` | Key 匹配 → 运维身份 `is_ops=true`；Bearer → 用户身份 `is_ops=false` 并校验数据库状态 |
| **jwt_only** | 仅 `Authorization: Bearer <token>` | 仅验证 Bearer JWT；忽略 API Key |

### 请求头示例

```http
# 开发 / 脚本（推荐）
X-API-Key: dev-key-change-me

# 用户登录后
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

身份语义（服务端内部）：

- `kind=api_key`，`is_ops=true`：运维/本机 Key，仍必须提供 Device Proof 才能访问 License-Protected 业务
- `kind=user`：已登录用户，填充 `user_id` / `username`

### 统一 License Service 配置

RD 使用固定版本 `license-service-client==1.0.0rc4` wheel，Service code 与
Device Proof audience 固定为 `rd`。生产必须配置：

| 变量 | 说明 |
|------|------|
| `LICENSE_SERVICE_BASE_URL` | License Service base URL，不含 `/v1` |
| `LICENSE_SERVICE_KEY_ID` | RD Service Credential 的 key id |
| `LICENSE_SERVICE_PRIVATE_KEY` | RD Service private key，仅部署 Secret 注入，不进 Git/日志/客户端 |
| `LICENSE_SERVICE_AUDIENCE` | 固定 `rd` |
| `LICENSE_CACHE_TTL_SECONDS` | `0..300`，默认 `30`；单 worker 使用 `MemoryReplayStore` |
| `LICENSE_SERVICE_TIMEOUT` | SDK HTTP timeout，默认 `3.0` 秒 |

### Device Proof V3 transport

受保护请求必须同时携带以下 RD headers，并绑定当前真实 HTTP method、path +
query 与 raw body SHA-256：

```http
X-Device-Id: dev_<64 lowercase hex>
X-Device-Key-Algorithm: ED25519
X-Device-Proof-Timestamp: <unix seconds>
X-Device-Proof-Nonce: <fresh nonce>
X-Device-Proof-Signature: <base64url-no-padding>
```

`device_id` 不是凭证；客户端必须使用真实 Device private key 生成
`LS-DEVICE-V3` proof。缺少字段返回 `403 DEVICE_PROOF_REQUIRED`。

当前实际迁移的 License-Protected endpoint（保持现有 `require_vip` 范围）：

- `POST /v1/jobs`
- `POST /v1/jobs/batch`
- `POST /v1/jobs/queue/bulk/retry`
- `POST /v1/jobs/{job_id}/retry`
- `PUT /v1/automation/hongguo-new`
- `POST /v1/automation/hongguo-new/scan`

search/detail、Job list/status/files、register/login、health 与 admin 不因本轮
接入被新增 License Guard；它们保留原有身份、owner 或运维边界。

### 频率限制与每日配额（D-4）

为保障服务稳定性，系统对 API 请求进行限流与每日额度配额控制：

- **全站 IP 限流**：按客户端 IP 限制，默认最大 `60` 次每分钟。超过限制返回 **429 Too Many Requests**，携带提示 `{"detail": "请求过于频繁"}`。探活接口 `/health` 及 `/` 豁免限流。
- **注册/登录限流**：针对 `/v1/auth/register` 与 `/v1/auth/login` 进行更严格的速率限制，默认最大 `10` 次每分钟。超过限制返回 **429 Too Many Requests**。
- **RD 每日任务配额**：只有 License decision 为 `ACTIVE` 后，RD 才执行普通用户每日任务数（`POST /v1/jobs`）的 `VIP_JOBS_PER_DAY`（默认 `50`）限制，超过日配额返回 **429 Too Many Requests**。Quota 不迁移到 License Service。
- **管理员 (ops / X-API-Key) 豁免**：使用有效 API Key 发起的请求完全不受每日配额计数及配额限制的影响。

### 多租户资源隔离与防探测（E1）

多用户环境下，系统按用户身份对 Job 记录与产物文件实施归属隔离：

- **Job 记录归属**：`POST /v1/jobs` 会将当前请求身份的 `owner_user_id` 与 `owner_kind` 写入任务记录。普通用户（`kind=user`）仅可查看、列表、取消属于自己的 Job 记录；`extra` 字段返回对应的归属信息。
- **产物文件归属**：文件接口（`GET /v1/files`、`GET /v1/files/{id}`、`POST /v1/files/{id}/open`）优先根据文件路径中的 `job_id` 前缀校验 Job 归属。用户只能访问属于自己 Job 的产物文件。
- **防探测 (404 Semantics)**：无权限访问他人 Job 或文件时统一返回 **404 Not Found**，防止非法枚举与探测（IDOR 防御）。
- **运维 (ops / X-API-Key) 权限**：使用 `X-API-Key` 鉴权时（`is_ops=true`）可访问与管理全量 Job 和磁盘文件。
- **历史 Job 兼容**：未关联 owner 的历史 Job 或磁盘孤立文件仅 ops 可见，对普通用户隐藏。

---

## T27 business authorization note

All ordinary business endpoints (content discovery, search/detail, jobs, queue,
files, and automation) require Device Proof and an ACTIVE License Context.
Legacy register/login/me/redeem endpoints remain deprecated compatibility APIs;
Desktop business requests do not require User/JWT authentication. API keys do
not bypass the License Guard.

## GET /health

无需鉴权。

返回：`status`（`ok` / `degraded`）、`version`、`platforms`、`summary`、`checks[]`（配置与设备依赖列表）、`dependencies`（兼容旧结构）。

---

## GET /v1/search

| 参数 | 说明 |
|------|------|
| platform | `hongguo` \| `fanqie` \| `all`（可选，默认 `all` 聚合双平台） |
| q | 关键词。红果：剧名搜索。番茄：书名关键词 / URL / book_id |
| page | 页码，默认 1（红果上游暂可能忽略分页） |

返回 `SearchResponse`：

```json
{
  "items": [
    {
      "id": "...",
      "title": "...",
      "platform": "fanqie",
      "source_label": "番茄小说",
      "cover": null,
      "author": null,
      "desc": null,
      "extra": {}
    }
  ],
  "platforms_queried": ["fanqie", "hongguo"],
  "platform_errors": {},
  "total": 1
}
```

聚合时某平台失败仍返回其它平台结果，错误写入 `platform_errors`。

---

## GET /v1/discover

首页发现：聚合真实热榜 / 今日上新；单个平台失败时仍返回其他平台结果。

| 参数 | 说明 |
|------|------|
| platform | `hongguo` \| `fanqie` \| `all`（默认 all） |
| kinds | 逗号分隔：`hot,new`（默认） |
| limit | 每个平台每个分区数量，`1..50`（默认 24） |

返回：

```json
{
  "sections": [
    {
      "kind": "hot",
      "title": "🔥 热榜",
      "items": [
        {
          "rank": 1,
          "id": "7660841866979445784",
          "title": "作品名称",
          "platform": "hongguo",
          "source_label": "红果短剧",
          "badge": "热",
          "extra": {
            "episode_count": 72,
            "score": "8.3",
            "play_count": 74876768
          }
        }
      ],
      "available": true,
      "message": "",
      "platform_errors": {}
    }
  ],
  "platforms_queried": ["fanqie", "hongguo"],
  "data_mode": "live",
  "note": "红果短剧发现内容已更新"
}
```

当前红果短剧已接入真实热榜与今日上新；不支持发现数据的平台会写入
`platform_errors`，不会阻断已成功平台。

---

## POST /v1/batch/resolve

批量识别链接或资源 ID，最多 100 条，单条失败不影响整批。

```json
{
  "inputs": ["https://fanqienovel.com/page/123", "7660841866979445784"],
  "platform_hint": "all"
}
```

返回 `items[]`（成功识别的 `SearchItem`）与 `errors[]`。

---

## POST /v1/jobs/batch

批量加入下载队列，最多 100 条：

```json
{
  "items": [
    {
      "platform": "hongguo",
      "id": "7660841866979445784",
      "range": "all",
      "options": {"title": "作品名称"}
    }
  ],
  "queue_mode": "enqueue",
  "duplicate_policy": "skip_completed"
}
```

响应逐项返回 `created`、`skipped`、`errors`。任务管理器默认最多并发执行
`MAX_CONCURRENT_JOBS=5` 个任务，其余任务保持 `pending` 排队。
`queue_mode=start_immediately` 会把本批任务放到等待队列前部。

---

## GET /v1/detail

| 参数 | 说明 |
|------|------|
| platform | `hongguo` \| `fanqie` |
| id | 剧/书 ID，或番茄 `fanqienovel.com/page|reader/...` URL |

返回：`title`、`segments[]`（集/章）、`extra` 等。红果当前仅在
`extra.qualities` 暴露 `1080p`；360p/480p/540p/720p 为平台私有
ByteVC2 编码，只用于诊断，不作为通用播放器可播放下载。

---

## POST /v1/jobs

> **[DEPRECATED / MIGRATION_REQUIRED]**  
> 当前实现由服务端创建和管理 Download Job。根据 [`ARCHITECTURE_BOUNDARY.md`](./ARCHITECTURE_BOUNDARY.md) 架构边界，
> **服务端不应持久化 Download Job**；目标由 Desktop Client DownloadManager 承担。  
> 本 API 在迁移期保留，待 Client Download Manager 建立后按计划废弃。

放行条件为：RD User/JWT 身份、Device License `ACTIVE`、RD Quota 通过。License
状态 `INACTIVE` 返回 **403**，License Service 不可用/超时/非 2xx 返回 **503**；
任何情况下都不会回退到 `vip_expires_at`、CardKey 或 API Key bypass。

```json
{
  "platform": "hongguo",
  "id": "SERIES_ID_或_书ID",
  "range": "1-1",
  "options": {
    "quality": "best",
    "concurrency": 1,
    "mode": "web",
    "cookie": "",
    "delay": 1.0
  }
}
```

| 字段 | 说明 |
|------|------|
| range | `all` \| `1-10` \| `1,3,5` |
| options.quality | 红果可播放清晰度，当前使用 `1080p` |
| options.mode | 番茄：`web`（默认）或 `app`（需 Frida + 设备会话） |
| options.cookie | 番茄 Web 可选 Cookie |
| options.delay | 番茄章节间隔（秒） |

返回：`JobResponse`（`job_id`、`status`、`progress`、`files` 等）。

---

## GET /v1/jobs

分页列举所有 Job。

| 参数 | 说明 |
|------|------|
| status | 可选状态过滤：`pending` \| `paused` \| `running` \| `success` \| `failed` \| `cancelled` |
| page | 页码，默认 1 |

---

## 下载队列管理

```http
GET  /v1/jobs/queue
POST /v1/jobs/queue/pause
POST /v1/jobs/queue/resume
POST /v1/jobs/queue/reorder
POST /v1/jobs/{job_id}/retry
```

暂停只影响尚未开始的任务，不中断运行中的下载；恢复后按
`queue_position` 继续调度。重排请求：

```json
{"job_ids": ["job-2", "job-1"]}
```

失败或已取消任务可通过 `retry` 重新进入队列，并再次接受 Device License 与 RD 每日配额校验。

---

## 红果上新识别与自动入队

> **[DEPRECATED / MIGRATION_REQUIRED]** — Server Automation Scheduler  
> 根据 [`ARCHITECTURE_BOUNDARY.md`](./ARCHITECTURE_BOUNDARY.md) 架构边界，  
> **RD Server 不负责 Automation Scheduler、自动追更、定时热榜、定时上新。**  
> 目标模式：Client Timer → RD API → 实时获取 → Client。  
> 本 API 组在迁移期保留，待 Client Timer 建立后标记退出服务端长期职责。

```http
GET  /v1/automation/hongguo-new
PUT  /v1/automation/hongguo-new
POST /v1/automation/hongguo-new/scan
```

配置示例：

```json
{
  "enabled": true,
  "auto_enqueue": true,
  "interval_seconds": 60,
  "scan_limit": 50,
  "quality": "1080p",
  "concurrency": 2,
  "download_cover": true,
  "download_desc": true
}
```

策略按用户持久化。首次扫描只建立红果当前“今日上新”ID 基线，不会把
已有条目误加入队列；后续扫描仅识别新出现的资源。自动入队仍受 VIP、
每日配额、队列容量、去重和 1080p 可播放格式限制，失败条目会在后续扫描重试。
| page_size | 每页数量，默认 20 (最大 100) |

---

## GET /v1/jobs/{job_id}

任务状态：`pending` \| `running` \| `success` \| `failed` \| `cancelled`。  
成功时 `files[]` 含 `file_id`、`name`、`size`（`file_id` 多为相对 `outputs/` 的路径，可含 `/`）。

---

## DELETE /v1/jobs/{job_id}

取消指定的 `pending` 或 `running` Job。

---

## GET /v1/jobs/summary

返回活跃/完成任务计数、磁盘剩余等。

---

## GET /v1/files

> **[DEPRECATED / MIGRATION_REQUIRED]**  
> 服务端不应有文件库。根据 [`ARCHITECTURE_BOUNDARY.md`](./ARCHITECTURE_BOUNDARY.md) 架构边界，
> **文件只属于 Desktop Client 本地**。本 API 在迁移期保留。

本地产物列表（UI 资源库用）。递归扫描 `outputs/` 目录下的 `.mp4`, `.txt`, `.m4a` 文件。

---

## GET /v1/files/{file_id}

> **[DEPRECATED / MIGRATION_REQUIRED]**  
> 目标文件只在 Client 本地；服务端不应永久保存下载文件。本 API 在迁移期保留。

**契约（E2E 依赖）**：下载产物二进制。  
`file_id` 为 job 返回的相对路径（支持带 `/` 路径，如 `job_id/video.mp4`）。

---

## POST /v1/files/{file_id}/open

在**运行服务端的本机**打开文件或资源管理器定位。

```json
{ "action": "play" }
```

| action | 行为 |
|--------|------|
| `play`（默认） | 系统默认程序打开 |
| `folder` | `explorer /select` 定位文件（Windows） |

---

## GET /v1/version

客户端检查更新用。支持 `current_version` 和稳定灰度用的 `install_id` 查询参数。

```json
{
  "version": "1.0.0",
  "update_check_enabled": true,
  "latest_version": "1.1.0",
  "has_update": true,
  "download_url": "https://download.example.com/ResourceDownloader-1.1.0-Setup.exe",
  "sha256": "64位SHA-256",
  "mandatory": false,
  "minimum_supported_version": "1.0.0",
  "rollout_percentage": 20,
  "release_notes": "本次更新内容"
}
```

未配置 `CLIENT_UPDATE_URL` 时更新检查关闭。桌面客户端只接受 HTTPS
安装包，并在启动安装程序前严格校验 SHA-256。

---

## POST /v1/auth/redeem

依赖用户身份鉴权（`Authorization: Bearer <token>`）。

保留旧 path 的 Activation Proxy。`card_code` 只是兼容字段名，会作为
`license_key` 转发到 License Service；RD 不查询/消费本地 CardKey，也不写入
`User.vip_expires_at`。

### 请求体

```json
{
  "card_code": "LIC-...",
  "device_id": "dev_<64 lowercase hex>",
  "device_key_algorithm": "ED25519",
  "device_public_key": "<base64url-no-padding>",
  "proof": {
    "timestamp": 0,
    "nonce": "<fresh nonce>",
    "signature": "<base64url-no-padding>"
  }
}
```

### 响应 (200 OK)

```json
{
  "success": true,
  "message": "ACTIVATED",
  "reason": "ACTIVATED",
  "license_expires_at": "2099-01-01T00:00:00+00:00",
  "max_devices": 2,
  "active_devices": 1,
  "vip_expires_at": "2099-01-01T00:00:00+00:00"
}
```

- 仅使用 `X-API-Key` 访问时返回 **403 Forbidden**（请使用用户登录后兑换）。
- Device Proof 缺失返回 **403 `DEVICE_PROOF_REQUIRED`**。
- License Service 业务拒绝返回 **403**，不可用/超时/非 2xx 返回 **503**。
- `vip_expires_at` 是 deprecated display alias，不再是授权事实；License truth 以
  License Service 返回为准。
- 凭证失效或过期返回 **401 Unauthorized**。

---

## POST /v1/auth/register

无需鉴权。注册新用户。

### 请求体

```json
{
  "username": "user123",
  "password": "password123"
}
```

### 响应 (201 Created)

```json
{
  "id": 1,
  "username": "user123",
  "is_active": true,
  "created_at": "2026-07-20T17:18:46Z",
  "updated_at": "2026-07-20T17:18:46Z",
  "vip_expires_at": null
}
```

- 重名、验证失败、密码长度少于 8 或大于 72 字节均返回 **400 Bad Request**。

---

## POST /v1/auth/login

无需鉴权。校验密码并签发 JWT token。

### 请求体

```json
{
  "username": "user123",
  "password": "password123"
}
```

### 响应 (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800,
  "vip_expires_at": null
}
```

- 凭证错误或用户不存在返回 **401 Unauthorized**。

---

## GET /v1/auth/me

依赖统一身份鉴权（`Authorization: Bearer <token>`）。

### 响应 (200 OK)

```json
{
  "id": 1,
  "username": "user123",
  "is_active": true,
  "created_at": "2026-07-20T17:18:46Z",
  "updated_at": "2026-07-20T17:18:46Z",
  "vip_expires_at": null
}
```

- 凭证无效或过期返回 **401 Unauthorized**。

---

## GET /v1/admin/sign-pool（D-3）

依赖运维身份鉴权（`X-API-Key`）。非 Ops 权限访问返回 **403 Forbidden**。

获取当前签名节点池的状态摘要（节点数、健康数、容量、租约与探活记录）。

---

## 异常说明：503 签名节点不可用（D-3）

在开启签名节点池（`SIGN_POOL_ENABLED=true`）后，若节点池中没有可用健康节点或所有节点重试失败，业务操作（搜索/详情/任务签名）将统一返回 **503 Service Unavailable**：

```json
{
  "detail": "签名节点繁忙或不可用，请稍后重试"
}
```

---

## 交互文档

服务启动后：`http://127.0.0.1:8000/docs`



