# Relay API

Base URL: `http://127.0.0.1:8000`

> 契约以本文件 + 运行中的 OpenAPI（`/docs`）为准。

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
| **dev** | `X-API-Key: <API_KEY>` | 与历史一致；脚本 e2e **零改**；忽略 Bearer Token |
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

- `kind=api_key`，`is_ops=true`：运维/本机 Key，VIP 门闸可放行
- `kind=user`：已登录用户，填充 `user_id` / `username`

### 频率限制与每日配额（D-4）

为保障服务稳定性，系统对 API 请求进行限流与每日额度配额控制：

- **全站 IP 限流**：按客户端 IP 限制，默认最大 `60` 次每分钟。超过限制返回 **429 Too Many Requests**，携带提示 `{"detail": "请求过于频繁"}`。探活接口 `/health` 及 `/` 豁免限流。
- **注册/登录限流**：针对 `/v1/auth/register` 与 `/v1/auth/login` 进行更严格的速率限制，默认最大 `10` 次每分钟。超过限制返回 **429 Too Many Requests**。
- **VIP 每日任务配额**：非 ops 的普通 VIP 用户每日可建任务数（`POST /v1/jobs`）受 `VIP_JOBS_PER_DAY`（默认 `50`）限制，超过日配额将返回 **429 Too Many Requests**，返回细节为 `{"detail": "今日下载配额已用尽"}`。
- **管理员 (ops / X-API-Key) 豁免**：使用有效 API Key 发起的请求完全不受每日配额计数及配额限制的影响。

### 多租户资源隔离与防探测（E1）

多用户环境下，系统按用户身份对 Job 记录与产物文件实施归属隔离：

- **Job 记录归属**：`POST /v1/jobs` 会将当前请求身份的 `owner_user_id` 与 `owner_kind` 写入任务记录。普通用户（`kind=user`）仅可查看、列表、取消属于自己的 Job 记录；`extra` 字段返回对应的归属信息。
- **产物文件归属**：文件接口（`GET /v1/files`、`GET /v1/files/{id}`、`POST /v1/files/{id}/open`）优先根据文件路径中的 `job_id` 前缀校验 Job 归属。用户只能访问属于自己 Job 的产物文件。
- **防探测 (404 Semantics)**：无权限访问他人 Job 或文件时统一返回 **404 Not Found**，防止非法枚举与探测（IDOR 防御）。
- **运维 (ops / X-API-Key) 权限**：使用 `X-API-Key` 鉴权时（`is_ops=true`）可访问与管理全量 Job 和磁盘文件。
- **历史 Job 兼容**：未关联 owner 的历史 Job 或磁盘孤立文件仅 ops 可见，对普通用户隐藏。

---

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
| status | 可选状态过滤：`pending` \| `running` \| `success` \| `failed` \| `cancelled` |
| page | 页码，默认 1 |
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

本地产物列表（UI 资源库用）。递归扫描 `outputs/` 目录下的 `.mp4`, `.txt`, `.m4a` 文件。

---

## GET /v1/files/{file_id}

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

客户端检查更新用。当前返回占位版本数据。

---

## POST /v1/auth/redeem

依赖用户身份鉴权（`Authorization: Bearer <token>`）。

兑换卡密以延长用户的 VIP 有效期。

### 请求体

```json
{
  "card_code": "RD-DECBE35422D12CB7DE18B834"
}
```

### 响应 (200 OK)

```json
{
  "success": true,
  "message": "卡密兑换成功",
  "vip_expires_at": "2026-08-20T18:14:56.123456"
}
```

- 仅使用 `X-API-Key` 访问时返回 **403 Forbidden**（请使用用户登录后兑换）。
- 卡密序列号不存在或已被使用返回 **400 Bad Request**（"卡密不存在" 或 "卡密已被使用"）。
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



