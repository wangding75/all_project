# 商业产品 V1.0 运维与客服标准操作手册 (Ops Runbook)

> **版本**: `v1.0` (Stage E4)  
> **适用对象**: 客服、系统管理员与运维人员  
> **安全警示**: 请勿将真实卡密、数据库备份文件及生产 `API_KEY` / `JWT_SECRET` 提交至代码仓库！

---

## 一、卡密管理 (发卡与作废)

### 1. 批量生成与分发卡密

在服务器或运维环境下，通过 `scripts/gen_card_keys.py` 脚本批量生成指定有效天数和批次的卡密：

```powershell
# 开启服务路径环境
$env:PYTHONPATH="server"

# 生成 30 天 VIP 卡密 50 张，批次为 B20260723
python scripts/gen_card_keys.py --days 30 --count 50 --batch B20260723
```

生成的卡密将自动写入 SQLite 数据库 (`app.db`)。复制控制台输出的卡密列表并录入销售/卡密平台即可。

### 2. 批量作废非法/未核销卡密 (黑产/作弊处理)

当发生坏账、刷卡或卡密泄漏事件时，可通过 API 或 CLI 批量作废指定批次下**所有未被核销**的卡密：

#### 途径 A: 命令行 CLI 工具（推荐）
```powershell
python scripts/ops_admin.py invalidate-batch --batch-id B20260723
```

#### 途径 B: REST API 接口
请求管理端受保护接口（需携带 `X-API-Key` 运维 Key）：
```http
POST /v1/admin/card-keys/invalidate-batch
Content-Type: application/json
X-API-Key: <YOUR_OPS_API_KEY>

{
  "batch_id": "B20260723"
}
```

*注意：已被用户兑换的卡密不会受批次作废影响；未兑换的卡密在作废后用户再次尝试兑换将提示 "卡密已作废或不存在"。*

---

## 二、账号管理 (封禁、解封与排查)

### 1. 违规账号一键封禁

当发现某账号存在滥用、爆破或违规抓取行为时：

```powershell
# 按用户名封禁
python scripts/ops_admin.py ban-user --username bad_user_01

# 或按用户 ID 封禁
python scripts/ops_admin.py ban-user --user-id 1024
```

或调用 API：
```http
POST /v1/admin/users/1024/status
Content-Type: application/json
X-API-Key: <YOUR_OPS_API_KEY>

{
  "is_active": false
}
```

**封禁即时生效规则**：
被封禁的用户 (`is_active = False`) 持有的 JWT Token 将在接下来的每一次 API 调用中被 `require_identity` 熔断拦截，并返回 `401 Unauthorized ("Invalid or expired token")`。

### 2. 解封用户

```powershell
python scripts/ops_admin.py unban-user --username bad_user_01
```

---

## 三、客服查询与排查

当用户反馈 "VIP 未生效"、"无法创建任务" 时，客服人员可通过 CLI 或接口查询用户明细与今日配额：

```powershell
# 查询指定用户明细
python scripts/ops_admin.py inspect-user --username client_user_01

# 分页列出所有用户
python scripts/ops_admin.py list-users --skip 0 --limit 20
```

输出示例：
```text
--- 用户状态明细 ---
用户 ID:        12
用户名:         client_user_01
账号启用状态:   启用
注册时间:       2026-07-20 10:00:00
VIP 到期时间:   2026-08-20 10:00:00
VIP 状态:       VIP 会员
今日创建任务数: 5
```

---

## 四、常见紧急故障处置 SOP

| 故障现象 | 排查步骤 | 处置措施 |
| :--- | :--- | :--- |
| **全员收到 401 报错** | 检查服务端 `.env` 中 `AUTH_MODE` | 若为 `jwt_only` 或 `dual`，确认 `JWT_SECRET` 是否改变导致全员 token 失效 |
| **单用户提示 403 VIP 需要兑换** | 查询 `inspect-user` | 检查 `vip_expires_at` 是否已过期，指导用户重新兑换新卡密 |
| **单用户提示 429 配额用尽** | 检查今日任务创建数 | VIP 默认每日有额度限制 (如 50 次/天)，可于次日 UTC 0:00 自动重置 |
| **密钥泄漏风控** | 立即修改 `.env` 中的 `API_KEY` 与 `JWT_SECRET` | 重启 `server/app/main.py`；由于 `JWT_SECRET` 修改，全员旧 token 将安全失效并需重新登录 |

---

## 五、数据备份与灾难恢复 SOP (Stage E5)

### 1. 数据库在线热备份

系统采用 SQLite 在线热备份 API (`sqlite3.backup`)，**无须停止 FastAPI 服务** 即可安全完成数据备份：

```powershell
$env:PYTHONPATH="server"

# 1. 执行热备份（自动备份 app.db 及配置文件）
python scripts/backup_db.py backup

# 2. 查看历史备份文件列表
python scripts/backup_db.py list
```

生成的备份文件自动存放于 `data/backups/app_backup_YYYYMMDD_HHMMSS.db`。推荐通过 Windows 计划任务或 Linux crontab 每日自动执行该命令。

### 2. 灾难恢复 (数据库还原)

当发生数据库文件损坏或误删数据时，可以从最近的备份中快速还原：

```powershell
# 还原指定备份文件到 app.db
python scripts/backup_db.py restore --file data/backups/app_backup_20260723_160000.db
```

*注意：在还原数据库前，建议先停止 `main.py` 服务进程，还原完成后再重新启动服务。*

