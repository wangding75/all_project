# 阶段 D — 商业化基础实施方案

> **状态**: D-0、D-1、D-2、D-4 ✅；**D-3** 待编码；全部完成后进入商业产品阶段  
> **关联**:  
> - [`POST_MVP_PLAN.md`](../POST_MVP_PLAN.md)  
> - [`COMMERCIAL_V1_PLAN.md`](./COMMERCIAL_V1_PLAN.md) ← **D 出口后的商业 V1.0（E0～E6）**  
> - [`business_landing_architecture.md`](../business_landing_architecture.md)  
> - 当前代码 `0.2.0`  
> **原则**: 先「用户 + VIP + 限流 + 签名池」技术底座，再全面商业产品化；**不 silent 破坏** dev e2e。

---

## 0. 目标与非目标

### 0.1 目标

1. 多用户身份（注册/登录），服务端可识别「谁在下」。  
2. VIP 时效由卡密核销延长；下载任务受 VIP（或明确免费额度）约束。  
3. 基础防刷：按用户/IP 限流 + 日配额。  
4. 数据落 SQLite，单机可跑；表结构兼容日后 PostgreSQL。

### 0.2 非目标（本阶段不做或后置）

| 不做 | 原因 |
|------|------|
| 完整支付网关 / 微信支付宝直连 | 用发卡网离线交付卡密即可 |
| 立刻废除 API Key | 开发/e2e/桌面本机仍需简单鉴权 |
| D-3 Redroid 多节点池与 D-1 并行大改 | 运维与产品风险叠加 |
| 多机 Job 调度 / Celery | 单机 JobManager 仍够用 |
| 复杂 RBAC / 后台运营台（可最小脚本发卡） | 控制范围 |

### 0.3 成功标准（编码后验收）

| ID | 标准 |
|----|------|
| A1 | `POST /v1/auth/register` + `login` 返回 JWT；错误不假成功 |
| A2 | 受保护路由：`Authorization: Bearer` **或** 开发旁路 `X-API-Key`（见 D-0） |
| A3 | 卡密核销事务安全：双请求同一码仅一人成功 |
| A4 | 非 VIP（且无免费额度）创建 job → **403**，文案明确 |
| A5 | 超配额 / 超频 → **429**，含 Retry-After 或剩余提示 |
| A6 | 现有 `scripts/e2e_*.py` 在 `AUTH_MODE=dev`（或默认开发配置）下仍可跑通 |
| A7 | 密钥：`JWT_SECRET` / 生产 `API_KEY` 禁止默认值上线（lifespan 警告或拒绝） |

---

## 1. 切片与推荐顺序

```text
D-0  鉴权并存与配置开关     ✅
D-1  SQLite + 用户 + JWT    ✅
D-2  卡密核销 + VIP 门闸    ✅
D-4  限流 + 日配额          ← 当前
D-3  Redroid / 签名池       ← D-4 后；独立里程碑
        ↓
阶段 E  商业产品 V1.0      → docs/COMMERCIAL_V1_PLAN.md
```

**不要**一次 PR 做完 D-1～D-4。每切片可独立合并、独立回滚。

---

## 2. D-0 — 鉴权并存（迁移策略）

### 2.1 问题

当前全局 `require_api_key`。若硬切 JWT，所有脚本、桌面默认配置、UI `localStorage` 同时失效。

### 2.2 策略（推荐）

引入配置（`.env`）：

```env
# dev | dual | jwt_only
AUTH_MODE=dev
JWT_SECRET=change-me-to-long-random
JWT_EXPIRE_MINUTES=10080
# dual/jwt_only 时: jobs/search/detail 需要 VIP 或免费额度
REQUIRE_VIP_FOR_JOBS=true
```

| AUTH_MODE | 行为 |
|-----------|------|
| **dev**（默认） | 仅 `X-API-Key`（与现网一致）；JWT 路由可存在但不强制；**e2e 零改** |
| **dual** | `X-API-Key` **或** 合法 JWT 二选一；Key 视为「本机运维/超级用户」免 VIP |
| **jwt_only** | 仅 JWT；废弃全局 Key（生产托管） |

### 2.3 依赖注入形状（方案 B 延续）

```text
require_identity  →  Identity(user | api_key_ops)
require_vip       →  基于 Identity.user.vip_expires_at（ops Key 跳过）
```

公开：`/health`、`/v1/auth/register`、`/v1/auth/login`、（可选）`/v1/version`。  
需登录：`/v1/auth/redeem`、`/v1/auth/me`。  
需 VIP 或 ops：`POST /v1/jobs`（及可选 search/detail 全开或半开，产品定）。

**产品默认建议（dual）**：

- `search` / `detail`：登录即可（或仍允许 Key）  
- `POST /v1/jobs` + 大文件下载：`require_vip` 或剩余免费次数  

### 2.4 UI / 脚本

| 客户端 | 改动 |
|--------|------|
| `scripts/e2e_*` | dev 模式不变；文档增加 dual 下「先 login 拿 token」示例 |
| 桌面 UI | 设置页保留 API Key；增加登录态（token 存 localStorage）；卡密兑换带 Bearer |
| OpenAPI | 标明双认证 |

---

## 3. D-1 — 用户体系与 JWT

### 3.1 技术选型

| 项 | 选型 | 备注 |
|----|------|------|
| ORM | SQLAlchemy 2.x + 同步引擎 + `asyncio.to_thread` **或** aiosqlite | 与现有 Job 线程模型兼容优先简单 |
| DB 文件 | `{REPO_ROOT}/data/app.db` | 与 exe 旁 data 一致 |
| 密码 | `pwdlib` / `passlib[bcrypt]` 或 `bcrypt` 直调 | 禁止明文 |
| JWT | `PyJWT` HS256 | `JWT_SECRET` 环境变量，≥32 字节随机 |

### 3.2 表结构（在蓝图上微调）

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    hashed_password VARCHAR(256) NOT NULL,
    vip_expires_at TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_users_vip ON users(vip_expires_at);
```

（卡密表见 D-2。）

### 3.3 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/auth/register` | `{username, password}` → 201；弱密码/重名 400 |
| POST | `/v1/auth/login` | → `{access_token, token_type, expires_at, vip_expires_at}` |
| GET | `/v1/auth/me` | Bearer → 用户摘要 + VIP 状态 |

**不实现**刷新令牌（第一期）：过期重新登录即可。

### 3.4 模块落点（建议）

```text
server/app/
  db.py           # engine, session, init_db()
  models_db.py    # SQLAlchemy models（与 pydantic DTO 分离）
  auth.py         # 扩展：require_api_key / require_user / require_vip / create_token
  api/auth_router.py
  main.py         # lifespan: init_db()
```

`app/models.py` 继续放 **Pydantic API DTO**，避免与 ORM 混名。

### 3.5 风险与缓解

| 风险 | 缓解 |
|------|------|
| 注册滥用 | 限流（D-4）+ 可选关闭 register（`ALLOW_REGISTER=false`） |
| JWT 密钥默认 | lifespan 检测 `change-me` 警告；`jwt_only` 生产拒绝启动 |
| 时钟偏差 | VIP 比较一律 UTC |

---

## 4. D-2 — 真实卡密与 VIP 门闸

### 4.1 表

```sql
CREATE TABLE card_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(128) UNIQUE NOT NULL,
    duration_days INTEGER NOT NULL DEFAULT 30,
    batch_id VARCHAR(64) NULL,          -- 发卡批次，便于作废
    is_used BOOLEAN NOT NULL DEFAULT 0,
    used_by_user_id INTEGER NULL REFERENCES users(id),
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_card_unused ON card_keys(is_used);
```

### 4.2 核销

- 必须 **已登录**（JWT）；禁止匿名 redeem。  
- 事务 + `SELECT … FOR UPDATE`（SQLite 用 BEGIN IMMEDIATE 或等价串行）。  
- 逻辑与蓝图一致：`vip_expires_at = max(now, current) + duration_days`。  
- 响应：`success`, `message`, `vip_expires_at`；失败 **4xx**，勿 200+success false 混用（可统一：业务失败 400 + detail）。

### 4.3 发卡

- 管理脚本：`scripts/gen_card_keys.py --days 30 --count 100 --batch B20260720`  
- 输出仅一次；**不进 git**。  
- 第一期不做 HTTP 管理端。

### 4.4 VIP 门闸

```text
POST /v1/jobs:
  Identity 为 ops API Key → 放行
  Identity 为 user 且 vip_expires_at > now → 放行
  否则若 FREE_JOBS_PER_DAY > 0 且今日未超 → 放行并计数
  否则 403
```

文件下载 `GET /v1/files/{id}`：建议同样校验「任务归属」——第一期若无 job.user_id，可暂只校验登录/Key；**D-2.1** 给 `jobs` JSON 或 DB 表增加 `owner_user_id`。

### 4.5 UI

- 兑换成功仅当 HTTP 成功且 `success=true`（已有）并刷新 `/me` 展示到期日。  
- 非 VIP 点下载：展示引导购买/兑换，不假成功。

---

## 5. D-4 — 限流与配额（先于 D-3）

### 5.1 限流

| 维度 | 建议默认 | 技术 |
|------|----------|------|
| IP | 60 req/min | `slowapi` 或自研 token bucket |
| 注册/登录 | 5/min/IP | 防爆破 |
| 创建 Job | 10/min/用户 | 与活跃 Job≤5 叠加 |

超限：**429** + 明确文案。

### 5.2 配额

```text
FREE_JOBS_PER_DAY=1          # 非 VIP 每日可建任务数；0=禁止
VIP_JOBS_PER_DAY=50          # VIP 日上限；0=不限制（仍受并发 5 约束）
```

计数存储：SQLite 表 `usage_daily(user_id, day, job_count)` 或 Redis（第一期 SQLite 足够）。

### 5.3 与现有 `max_active=5`

并发上限保留；配额是「日累计」，不替代并发闸。

---

## 6. D-3 — Redroid / 签名池（后置里程碑）

> 仅边界设计，不纳入 D-1/D-2 首 PR。

### 6.1 问题

番茄/红果签名与解密绑定设备进程；单机 Frida 无法支撑多租户并发。

### 6.2 目标架构（摘要）

```text
JobManager → SignPoolClient → [节点健康检查] → Redroid/模拟器 worker
                              → 队列 + 超时 + 失败重试
```

### 6.3 交付物（未来）

- 节点注册：base_url、容量、标签（fanqie_sign / hongguo_sign）  
- 租约：任务占用节点 N 分钟  
- 健康：周期性 `/health` 或 frida ping  
- 与 VIP 无关：任何付费用户共享池；可对 VIP 提高优先级（更后）

### 6.4 依赖

- Docker / 云主机预算  
- 镜像与 frida-server 版本钉扎（见 HANDOFF）  
- 单独 `docs/STAGE_D3_POOL.md` 再开

---

## 7. 数据与兼容

| 现有 | D 期策略 |
|------|----------|
| `data/jobs/*.json` | 保留；可选增加 `owner` 字段 |
| `X-API-Key` | D-0 并存 |
| Stub redeem | D-2 替换为真逻辑；删除假 VIP 文案 |
| 桌面 EXE | 仍可用 Key；UI 逐步加登录 |

---

## 8. 安全清单

1. `JWT_SECRET`、`API_KEY` 不进仓库；示例仅占位。  
2. 密码哈希；日志禁止打印密码/完整 token。  
3. 卡密熵足够（如 `secrets.token_urlsafe(16)` + 前缀）。  
4. CORS：若仅 PyWebView/本机，保持默认即可；公网部署再收紧。  
5. 管理脚本发卡需本机文件权限，无 HTTP 裸奔。  
6. SQLite 备份：`data/app.db` 进运维备份，不进 git。

---

## 9. PR / 工作量切分（预估）

| PR | 内容 | 预估 |
|----|------|------|
| D0 | `AUTH_MODE` + `require_identity` 重构，行为默认=现网 | 0.5–1 天 |
| D1 | DB + register/login/me + JWT | 1–2 天 |
| D2 | card_keys + redeem + VIP on jobs + gen 脚本 | 1–2 天 |
| D4 | slowapi + daily quota | 1 天 |
| UI | 登录页/态、兑换接真 API、VIP 展示 | 1–2 天 |
| D3 | 另立项 | 1–2 周+ |

---

## 10. 明确不做的错误路径

1. **未做 D-0 就 jwt_only** → e2e 全挂。  
2. **redeem 仍 200 假成功** → 违反质量门槛。  
3. **VIP 只藏按钮不拦 API** → 可绕过。  
4. **D-1 与 D-3 同一大 PR** → 无法评审与回滚。  
5. **把用户密码/JWT 写进 Job JSON 明文**。

---

## 11. 编码启动检查表

### D-0（已完成骨架）

- [x] 默认 `AUTH_MODE=dev`  
- [x] `require_identity` + `Identity`；路由切换  
- [x] `docs/api.md` 认证章节  
- [x] `.env.example` 字段  
- [x] 本机 `smoke_health` +（可选）e2e 回归确认  

### D-1 开工前

- [x] 确认 SQLite 路径与 frozen `REPO_ROOT`  
- [x] 依赖写入 `server/requirements.txt`（SQLAlchemy、PyJWT、bcrypt…）  
- [x] 至少 1 个 pytest：register → login → me  
- [x] e2e 在 dev 下回归 smoke  

### D-2 开工前

- [x] CardKey 表 ORM 与 SQLite 自动创建
- [x] `require_vip` 逻辑定义，ops / API Key 绕过
- [x] 真 `/v1/auth/redeem` 逻辑替换 Stub
- [x] `gen_card_keys` 批量生成脚本
- [x] test_auth_d2.py 测试覆盖且全绿

### D-4 开工前

- [x] UsageDaily 表 ORM 与 SQLite 自动创建
- [x] config 与 .env.example 新增限流及配额参数
- [x] in-memory 固定窗口 1 分钟 rate limiter
- [x] `UsageDaily` 日用配额校验层
- [x] global 及 auth 路由限流与 quota 日配额逻辑接入
- [x] test_quota_d4.py 测试覆盖且全绿 (共 22 条用例通过)

---

## 12. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 初稿：D-0 并存、D-1/D-2/D-4 优先、D-3 后置；对齐现网 API Key + JobManager |
| 2026-07-20 | D-0 编码落地：config / auth / router / api.md / .env.example |
| 2026-07-20 | 衔接 COMMERCIAL_V1_PLAN：D-4→D-3 出口后进入 E0～E6 商业产品开发 |
