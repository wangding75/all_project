# Relay API（MVP-1）

Base URL: `http://127.0.0.1:8000`  
鉴权：除 `/health`、`/` 外，请求头 `X-API-Key: <key>`（默认 `dev-key-change-me`）

## GET /health

无需鉴权。返回 `status`、`version`、`platforms`。

## GET /v1/search

| 参数 | 说明 |
|------|------|
| platform | `fanqie`（MVP-1） |
| q | 关键词；MVP-1 仅当 URL/纯数字 ID 时可解析 |
| page | 页码，默认 1 |

## GET /v1/detail

| 参数 | 说明 |
|------|------|
| platform | `fanqie` |
| id | book_id 或 `fanqienovel.com/page|reader/...` URL |

## POST /v1/jobs

```json
{
  "platform": "fanqie",
  "id": "书ID或URL",
  "range": "1-3",
  "options": { "cookie": "", "delay": 1.0 }
}
```

`range`: `all` | `1-10` | `1,3,5`

## GET /v1/jobs/{job_id}

任务状态：`pending|running|success|failed|cancelled`，含 `files[]`。

## GET /v1/files/{file_id}

`file_id` 为 job 返回的相对路径（可含 `/`）。

## 交互文档

服务启动后：`http://127.0.0.1:8000/docs`
