# 签名节点池 (Sign Pool) 说明与部署指南

> **阶段**: D-3 ✅ （阶段 D 技术出口）  
> **功能**: 将单机 Frida / 模拟器依赖解耦为可配置的 HTTP 签名节点池。支持多节点注册、并发容量控制、租约与轮询调度、自动健康检查与故障隔离、全挂 503 明确文案（无假成功）。

---

## 1. 配置说明

在 `.env` 或环境变量中可配置以下项：

```env
# 签名池开关 (默认 false；关闭时完全走现网本机 Frida 逻辑，保 e2e)
SIGN_POOL_ENABLED=false

# 配置文件相对路径 (默认 relative to REPO_ROOT)
SIGN_POOL_CONFIG=data/sign_pool.json

# 备用 URL 列表（逗号分隔；当 JSON 文件不存在时生效）
# SIGN_POOL_URLS=http://127.0.0.1:19101,http://127.0.0.1:19102

# 健康检查间隔（秒）
SIGN_POOL_HEALTH_INTERVAL_SEC=30

# 单次签名租约时长（秒）
SIGN_POOL_LEASE_SEC=120

# 节点最大连续失败次数（达到后标记 unhealthy 摘除）
SIGN_POOL_MAX_FAILS=3
```

---

## 2. 节点配置文件 (`data/sign_pool.json`)

节点配置格式示例（可参考 `data/sign_pool.example.json`）：

```json
{
  "nodes": [
    {
      "id": "node-1",
      "base_url": "http://127.0.0.1:19101",
      "labels": ["fanqie_sign"],
      "capacity": 2,
      "enabled": true
    },
    {
      "id": "node-2",
      "base_url": "http://127.0.0.1:19102",
      "labels": ["fanqie_sign", "hongguo_sign"],
      "capacity": 2,
      "enabled": true
    }
  ]
}
```

---

## 3. 节点 HTTP 契约（写死死契约）

任何加入签名池的节点服务（包含 Redroid 实例、Unidbg 服务或 Mock 节点）必须暴露以下标准接口：

### 3.1 健康探针

- **请求**: `GET {base_url}/health`
- **响应 HTTP 状态**: `200 OK`
- **Body**: `{"status": "ok"}`

### 3.2 签名接口

- **请求**: `POST {base_url}/sign`
- **Request JSON**:
  ```json
  {
    "url": "https://api5-normal-sinfonlinea.fqnovel.com/...",
    "headers": {
      "user-agent": "...",
      "x-ss-stub": "..."
    }
  }
  ```
- **Response 200 JSON**:
  ```json
  {
    "headers": {
      "x-argus": "...",
      "x-gorgon": "...",
      "x-khronos": "..."
    }
  }
  ```

---

## 4. 本地 Mock 签名节点

仓库内置轻量级 Mock 签名节点服务（供 pytest 与本地测试使用）：

```bash
# 启动单节点测试
python -m app.sign_pool.mock_node --port 19101
```

---

## 5. Ops 运维与诊断接口

系统提供专用的 Ops 管理接口用于查看当前节点池运行状态：

- **请求**: `GET /v1/admin/sign-pool`
- **鉴权**: 仅 API Key (`X-API-Key`) 运维身份可访问，非 ops 返回 **HTTP 403**。
- **响应示例**:
  ```json
  {
    "total_nodes": 2,
    "enabled_nodes": 2,
    "healthy_nodes": 2,
    "total_in_use": 1,
    "nodes": [
      {
        "id": "node-1",
        "base_url": "http://127.0.0.1:19101",
        "labels": ["fanqie_sign"],
        "capacity": 2,
        "enabled": true,
        "healthy": true,
        "fail_count": 0,
        "in_use": 1,
        "active_leases": 1,
        "last_check": 1784600000.0
      }
    ]
  }
  ```

---

## 6. 全挂与不可用处理 (503)

当签名池无可用健康节点、或者所有节点重试后均失败时，系统将阻断业务并统一抛出 **HTTP 503**：

```json
{
  "detail": "签名节点繁忙或不可用，请稍后重试"
}
```

客户端可捕获 503 提示用户稍后重试，无假成功现象。
