# 商业发现与批量下载 UI：后续 API 契约

> 状态：规划稿（客户端 UI 已预留，服务端尚未实现）  
> 更新日期：2026-07-28  
> 原则：不阻塞当前 `GET /v1/discover`、搜索、详情和单任务下载接口；新增能力按优先级逐步交付。

## 1. UI 与接口映射

| UI 功能 | 所需接口 | 优先级 |
|---|---|---|
| 发现页分页、分类和真实热榜/上新 | 扩展 `GET /v1/discover` | P0 |
| 内容卡片批量加入队列 | `POST /v1/jobs/batch` | P0 |
| 批量链接/ID识别 | `POST /v1/batch/resolve` | P0 |
| 热度榜、飙升榜、新作榜 | `GET /v1/rankings` | P1 |
| 上线日历 | `GET /v1/calendar` | P1 |
| 收藏与追更订阅 | `/v1/subscriptions` CRUD | P1 |
| 自动检查、提醒或自动下载 | 订阅策略字段 + 服务端调度器 | P1 |
| 队列排序、暂停和批量重试 | `/v1/jobs/queue/*` | P1 |

所有接口沿用现有认证方式：

```http
Authorization: Bearer <access_token>
```

开发和运维模式可继续使用：

```http
X-API-Key: <api_key>
```

## 2. 通用内容摘要

发现、榜单、日历、批量识别统一返回 `ContentSummary`，避免客户端为不同页面维护多套字段。

```json
{
  "id": "content-id",
  "platform": "hongguo",
  "content_type": "short_drama",
  "title": "作品名称",
  "cover": "https://cdn.example/cover.jpg",
  "author": "作者或主演",
  "summary": "作品简介",
  "status": "serializing",
  "episode_count": 30,
  "latest_episode": 12,
  "score": 8.6,
  "heat": 99123,
  "rank": 1,
  "published_at": "2026-07-28T08:00:00+08:00",
  "updated_at": "2026-07-28T12:00:00+08:00",
  "badges": ["独播", "今日上新"],
  "is_favorite": false,
  "is_subscribed": false
}
```

字段约束：

- `platform`: `hongguo | fanqie`
- `content_type`: `short_drama | novel | comic_drama`
- 时间统一使用带时区的 ISO 8601。
- 数值未知时返回 `null`，不要用 `0` 冒充未知。
- `cover` 必须允许为空，客户端会显示本地占位图。

## 3. P0：扩展发现接口

### `GET /v1/discover`

保留当前响应兼容性，新增可选参数：

| 参数 | 示例 | 说明 |
|---|---|---|
| `platform` | `hongguo` | `hongguo | fanqie | all` |
| `kinds` | `hot,new` | `hot,new,recommended` |
| `category` | `都市` | 内容分类 |
| `date` | `2026-07-28` | 指定上新日期 |
| `cursor` | `opaque-token` | 游标分页 |
| `limit` | `24` | 建议范围 `1..50` |

建议响应：

```json
{
  "sections": [
    {
      "kind": "hot",
      "title": "热榜",
      "available": true,
      "items": [],
      "next_cursor": null,
      "platform_errors": {}
    }
  ],
  "platforms_queried": ["hongguo"],
  "data_mode": "live",
  "generated_at": "2026-07-28T13:30:00+08:00"
}
```

要求：

- 单个平台失败时返回其他平台结果，并写入 `platform_errors`。
- `data_mode` 使用 `live | cached | stub`。
- 缓存数据必须返回 `generated_at`，方便 UI 显示更新时间。

## 4. P0：批量识别

### `POST /v1/batch/resolve`

请求：

```json
{
  "inputs": [
    "https://example/content/1",
    "resource-id-2"
  ],
  "platform_hint": "all"
}
```

响应：

```json
{
  "items": [
    {
      "input": "https://example/content/1",
      "resolved": true,
      "content": {}
    }
  ],
  "errors": [
    {
      "input": "resource-id-2",
      "code": "NOT_FOUND",
      "message": "未找到对应资源"
    }
  ]
}
```

约束：

- 单次最多 100 条。
- 必须去重并返回原始输入对应关系。
- 单条失败不能使整批请求失败。

## 5. P0：批量创建下载任务

### `POST /v1/jobs/batch`

请求：

```json
{
  "items": [
    {
      "platform": "hongguo",
      "item_id": "content-id",
      "range_spec": "all",
      "quality": "1080p"
    }
  ],
  "queue_mode": "enqueue",
  "duplicate_policy": "skip_completed"
}
```

字段：

- `queue_mode`: `enqueue | start_immediately`
- `duplicate_policy`: `skip_completed | retry_failed | create_anyway`

响应：

```json
{
  "batch_id": "batch-uuid",
  "created": [
    {
      "item_id": "content-id",
      "job_id": "job-uuid"
    }
  ],
  "skipped": [],
  "errors": []
}
```

要求：

- 返回每个资源的处理结果。
- 批量操作必须幂等，建议支持 `Idempotency-Key`。
- VIP、配额和并发限制需在服务端逐项校验。

## 6. P1：排行榜

### `GET /v1/rankings`

```http
GET /v1/rankings?platform=hongguo&type=rising&period=day&limit=50
```

参数：

- `type`: `hot | rising | new`
- `period`: `day | week | month`
- 支持 `category`、`cursor`、`limit`

响应：

```json
{
  "type": "rising",
  "period": "day",
  "items": [],
  "next_cursor": null,
  "generated_at": "2026-07-28T13:30:00+08:00"
}
```

## 7. P1：上线日历

### `GET /v1/calendar`

```http
GET /v1/calendar?platform=all&from=2026-07-28&to=2026-08-03
```

响应：

```json
{
  "days": [
    {
      "date": "2026-07-28",
      "items": []
    }
  ],
  "timezone": "Asia/Shanghai"
}
```

日期范围建议限制在 31 天以内。

## 8. P1：追更订阅

### 接口列表

```http
GET    /v1/subscriptions
POST   /v1/subscriptions
PATCH  /v1/subscriptions/{subscription_id}
DELETE /v1/subscriptions/{subscription_id}
POST   /v1/subscriptions/check
```

创建请求：

```json
{
  "platform": "hongguo",
  "item_id": "content-id",
  "notify_on_update": true,
  "auto_download": false,
  "quality": "1080p",
  "range_policy": "new_only"
}
```

订阅响应至少包含：

```json
{
  "subscription_id": "subscription-uuid",
  "content": {},
  "enabled": true,
  "last_checked_at": null,
  "next_check_at": "2026-07-28T14:00:00+08:00",
  "last_seen_episode": 12,
  "last_error": null
}
```

服务端要求：

- 默认只通知，不默认自动下载。
- 自动下载必须受 VIP、每日配额、磁盘空间和并发上限约束。
- 同一用户、平台和资源只能存在一个有效订阅。
- 连续失败需退避，不得高频请求上游。

## 9. P1：队列操作

```http
GET  /v1/jobs/queue
POST /v1/jobs/queue/reorder
POST /v1/jobs/batch-actions
```

批量动作请求：

```json
{
  "job_ids": ["job-1", "job-2"],
  "action": "retry"
}
```

`action` 支持：

- `pause`
- `resume`
- `cancel`
- `retry`
- `remove_completed`

排序请求：

```json
{
  "job_ids_in_order": ["job-2", "job-1"]
}
```

## 10. 统一错误格式

新增接口建议统一返回：

```json
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "今日下载额度已用完",
    "retryable": false,
    "details": {}
  },
  "request_id": "request-uuid"
}
```

建议错误码：

- `UNAUTHORIZED`
- `VIP_REQUIRED`
- `QUOTA_EXCEEDED`
- `PLATFORM_UNAVAILABLE`
- `CONTENT_NOT_FOUND`
- `DUPLICATE_JOB`
- `INVALID_BATCH`
- `RATE_LIMITED`
- `INSUFFICIENT_STORAGE`

## 11. 验收顺序

1. 扩展 `GET /v1/discover`，让首页出现真实内容。
2. 实现 `POST /v1/jobs/batch`，打通多选加入队列。
3. 实现排行榜和日历。
4. 实现追更订阅及调度器。
5. 实现队列排序和批量动作。

每个接口完成后应补充：

- Pydantic 请求/响应模型
- OpenAPI 示例
- 权限与配额测试
- 单平台失败降级测试
- 客户端真实联调测试
