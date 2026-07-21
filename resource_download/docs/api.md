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

---

## GET /health

无需鉴权。

返回：`status`、`version`、`platforms`（如 `hongguo`、`fanqie`）。

---

## GET /v1/search

| 参数 | 说明 |
|------|------|
| platform | `hongguo` \| `fanqie` |
| q | 关键词。红果：剧名搜索。番茄：MVP 仅当 URL 或纯数字 book_id 时可解析 |
| page | 页码，默认 1（红果上游暂可能忽略分页） |

---

## GET /v1/detail

| 参数 | 说明 |
|------|------|
| platform | `hongguo` \| `fanqie` |
| id | 剧/书 ID，或番茄 `fanqienovel.com/page|reader/...` URL |

返回：`title`、`segments[]`（集/章）、`extra` 等。红果 `extra.qualities` 可能含 `1080p`/`720p`。

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
| options.quality | 红果清晰度（如 `best` / `1080p`） |
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



