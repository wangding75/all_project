# Relay API

Base URL: `http://127.0.0.1:8000`  
鉴权：除 `/health`、`/`、`/ui` 外，请求头 `X-API-Key: <key>`（默认仅开发：`dev-key-change-me`）

> 契约以本文件 + 运行中的 OpenAPI（`/docs`）为准。  
> **已知缺口（2026-07-20）**：`GET /v1/files/{file_id}` 在代码中**尚未实现**，但 E2E 脚本已依赖；见 [`POST_MVP_PLAN.md`](../POST_MVP_PLAN.md) S-P0-0。

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

## GET /v1/jobs/{job_id}

任务状态：`pending` \| `running` \| `success` \| `failed` \| `cancelled`。  
成功时 `files[]` 含 `file_id`、`name`、`size`（`file_id` 多为相对 `outputs/` 的路径，可含 `/`）。

---

## GET /v1/jobs/summary

返回活跃/完成任务计数、磁盘剩余等。  
> 注意：当前实现中「下载速度」可能为占位字符串，勿当真实测速。

---

## GET /v1/files

本地产物列表（UI 资源库用）。  
> 注意：当前实现可能只扫描 `outputs/` 顶层，而真实文件多在 `outputs/{job_id}/` 下；修复见 POST_MVP_PLAN S-P0-3。

---

## GET /v1/files/{file_id}

**契约（E2E 依赖）**：下载产物二进制。  
`file_id` 为 job 返回的相对路径（可含 `/`，请求时需 URL 编码）。

> **实现状态：待恢复（S-P0-0）**。恢复前脚本末步会失败。

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

客户端检查更新用。当前为占位数据。

---

## POST /v1/auth/redeem

卡密兑换。**当前为商业化 Stub**，勿当作真实 VIP 核销。  
规划见 [`business_landing_architecture.md`](../business_landing_architecture.md)。

---

## 未实现但已规划

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/v1/jobs` | 分页列举任务 |
| DELETE | `/v1/jobs/{job_id}` | 取消任务 |

---

## 交互文档

服务启动后：`http://127.0.0.1:8000/docs`
