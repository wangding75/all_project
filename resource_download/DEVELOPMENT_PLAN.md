# 多平台内容下载器 — 开发计划（已定稿）

> 基于方案讨论结论。实现以本文为准；旧版 `design_plan.md` 中与本文冲突的部分（本机一体化、全离线无签名等）以本文覆盖。

**定稿日期**：2026-07-18（客户端后置修订同日）

---

## 0. 已锁定决策

| 项 | 决策 |
|----|------|
| 总体架构 | **方案 2：瘦客户端 + 中转服务端（托管订阅向）** |
| 红果 | **当前主路径**：复用 **`vendor/hongguo`**（不重写解密/取链） |
| 番茄 | 后置；**App 会话**（不做 Web 主路径） |
| 会话 | **服务端自养**；用户不贴 Cookie |
| 客户端 | **最后做**；脚本验收 |
| 验收方式 | **`scripts/e2e_hongguo.py` 等** 打 API |
| 产品优先级 | **红果复用打通 → 运维/签名稳 → 番茄 App → 客户端** |

### 架构示意

```text
┌──────────────────┐                      ┌────────────────────────────┐
│  验收客户端       │  curl / Python 脚本   │  中转服务端                  │
│  scripts/*.py    │ ───────────────────► │  统一 API · 任务队列 · 鉴权   │
│  （后期：桌面 UI） │                      │  fanqie | hongguo adapters  │
└──────────────────┘                      └────────────────────────────┘
```

主路径在 **服务端 + 脚本**；桌面 UI 仅为外壳，可整段后置。

---

## 1. 目标与非目标

### 1.0 MVP 分层（验收口径）

| 级别 | 范围 | 完成标准 |
|------|------|----------|
| **MVP-H（当前）** | relay + **复用 hongguo** + `e2e_hongguo` | 签名/config 就绪下，脚本出可播 **MP4** |
| **MVP-F** | 番茄 App 会话接入 | 脚本出书 |
| **之后** | 瘦客户端 UI、配额/订阅、硬化 | |

### 1.1 主里程碑（无桌面 UI 即可宣告链路打通）

1. **服务端**可独立部署：HTTP API + 任务进度 + 产物下载。  
2. **番茄（MVP-1）**：URL/ID → 详情 → job → **TXT** → 脚本拉取文件，正文可读。  
3. **红果（MVP-2）**：搜索/详情 → job → 解密 **MP4** → 脚本拉取。  
4. **`scripts/`** 覆盖上述端到端。

### 1.2 后置目标

5. **瘦客户端 UI**：平台切换、搜索/详情、队列、设置。

### 1.3 非目标（MVP-1/2）

- 任何桌面 UI  
- 番茄官方 Argus/Ladon  
- 客户端本机 Frida / spade  
- 公开多租户设备池  
- 绑定第三方中转域名  

---

## 2. 仓库与模块结构（目标态）

```text
resource_download/
├── DEVELOPMENT_PLAN.md
├── design_plan.md
├── server/                      # 中转服务端（主战场）
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── auth.py
│   │   ├── jobs/
│   │   └── models.py
│   ├── platforms/
│   │   ├── base.py
│   │   ├── fanqie/
│   │   └── hongguo/
│   ├── storage/
│   └── requirements.txt
├── scripts/                     # 链路验收（替代早期客户端）
│   ├── e2e_fanqie.py            # 番茄：detail → job → poll → download
│   ├── e2e_hongguo.py           # 红果：同上
│   ├── smoke_health.py
│   └── README.md                # 环境变量、示例命令
├── client/                      # 最后再做；此前可空或不建
├── download.py                  # 迁入 fanqie 前保留
└── README.md
```

---

## 3. 统一 API 契约（服务端对外）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/v1/search` | `platform`, `q`, `page` |
| GET | `/v1/detail` | `platform`, `id` |
| POST | `/v1/jobs` | `platform`, `id`, `range`, `options` |
| GET | `/v1/jobs/{job_id}` | 状态、进度、错误、产物 |
| GET | `/v1/files/{file_id}` | 下载产物 |

公共头：`X-API-Key`。

脚本验收最小闭环：

```text
health → detail → create job → poll until success|failed → GET file → 本地打开检查
```

---

## 4. 分阶段计划

### 阶段 0 — 工程骨架与契约（约 1～2 天）

**交付**

- `server/` FastAPI 空壳、`/health`、鉴权、统一错误体  
- `BasePlatform` + 假 platform  
- 任务状态机：`pending | running | success | failed | cancelled`  
- `data/jobs/`、`data/outputs/`  
- `scripts/smoke_health.py`  
- 简短 `docs/api.md` 或 OpenAPI  

**验收**

- 脚本能 health；假 job 能跑完并下载占位文件  

---

### 阶段 1 — 番茄服务端 MVP（约 3～5 天）【优先】

**交付**

- `platforms/fanqie/`：自 `download.py` 迁移  
  - URL/ID、`__INITIAL_STATE__`、目录、章节、字体解密、限速/重试、锁章标记  
- Cookie 可选配置  
- 导出 **TXT**  
- jobs + files API  

**验收（仅脚本，无 UI）**

```text
python scripts/e2e_fanqie.py --url "https://fanqienovel.com/page/..." 
→ job success → 本地 TXT 可读、无大面积乱码
```

---

### 阶段 2 — 番茄脚本工具化与稳定（约 1～2 天）

**交付**

- 完善 `scripts/e2e_fanqie.py`：轮询、超时、退出码、保存路径参数  
- 可选：`scripts/job_status.py`、批量 book_id 列表  
- README 写清：启动 server、环境变量 `API_BASE` / `API_KEY`、一条复制即跑命令  

**验收**

- 他人（或未来的你）只按 README 即可复现番茄下载，不依赖 GUI  

---

### 阶段 3 — 红果服务端（约 5～10 天）

**交付**

- 对齐 `zhangbaio/hongguo`：可插拔签名、spade 自测、CTR 解密、默认 1080p  
- `platforms/hongguo` 接入同一 jobs API  
- 签名宕机时错误明确，不影响番茄  

**验收（仅脚本）**

```text
python scripts/e2e_hongguo.py --series-id ... --range 1-2
→ MP4 可播
```

---

### 阶段 4 — 双平台脚本回归（约 1 天）

**交付**

- 番茄 + 红果各至少 1 条固定样例写进 `scripts/README.md`  
- 简单回归：先 fanqie smoke，再 hongguo smoke  

**验收**

- 两平台链路文档化、可重复  

---

### 阶段 5 — 瘦客户端（最后，约 3～7 天）

**前提**：阶段 1～4 脚本链路已稳定。

**交付**

- 桌面薄壳：只调已有 API（`API_BASE` + `API_KEY`）  
- 番茄 + 红果：搜索/详情/队列/设置  
- 技术栈开工时二选一锁死（PyWebView 或 PySide6）  

**验收**

- UI 不新增服务端能力；仅复现脚本已能完成的操作  

---

### 阶段 6 — 硬化与发布（持续）

日志、清理、EPUB 可选、Docker/启动脚本、打包客户端、免责声明等。

---

## 5. 排期总览

| 阶段 | 内容 | 估计 |
|------|------|------|
| 0 | 骨架 + 契约 + smoke 脚本 | 1～2 天 |
| 1 | 番茄服务端 | 3～5 天 |
| 2 | 番茄 E2E 脚本与文档 | 1～2 天 |
| 3 | 红果服务端 | 5～10 天 |
| 4 | 双平台脚本回归 | ~1 天 |
| **—** | **主链路打通（可无 UI）** | **约 2～4 周** |
| 5 | 瘦客户端（后置） | 3～7 天 |
| 6 | 硬化发布 | 持续 |

---

## 6. 技术选型

| 层 | 选型 | 备注 |
|----|------|------|
| 服务端 | FastAPI + uvicorn | |
| 任务 | 进程内队列 + SQLite/JSON | |
| 番茄 | fonttools + brotli | |
| 红果 | pycryptodome + hongguo；签名外置 | |
| 验收 | **Python scripts + requests/httpx** | 主「客户端」直至阶段 5 |
| 桌面 UI | 阶段 5 再定 | 不提前开工 |

---

## 7. 质量门槛

1. 每平台至少 1 条 **脚本可跑的 E2E**（非仅单元测试）。  
2. 红果 spade 真值测试保留。  
3. 密钥/token/Cookie 不入库。  
4. README 中的脚本命令与真实行为一致。  
5. **不以「客户端做好了」为服务端完成标准**；以脚本 E2E 为准。  

---

## 8. 立即执行顺序（MVP-1）

1. ~~阶段 0 脚手架~~：**已生成**（`server/` + `scripts/`）  
2. 安装依赖、启动 `python server/run.py`，跑 `scripts/smoke_health.py`  
3. 用真实书 ID 跑 `scripts/e2e_fanqie.py --range 1-2`，修字体/限流问题  
4. MVP-1 验收通过后再开 MVP-2（红果）  
5. 双平台脚本稳定后再开 `client/`  

---

## 9. 决策备忘

| 问题 | 结论 |
|------|------|
| 客户端何时做？ | **最后**；不挡主链路 |
| 如何验收下载？ | **`scripts/` 请求 API** |
| 番茄中转模式 | 架构同红果，协议 Web 自有 |
| 红果 Cookie | 用户不要；服务端要会话+签名 |
| MVP-1 是否含红果/UI？ | **否** |

---

## 10. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-18 | 初版：方案 2、番茄优先、红果对齐 hongguo |
| 2026-07-18 | **客户端后置**；主验收改为 scripts E2E；阶段重排 |
| 2026-07-18 | 标明 **MVP-1 / MVP-2**；落地 `server/` + `scripts/` 脚手架 |
| 2026-07-18 | **主路径改为红果**；`vendor/hongguo` 复用 + `platforms/hongguo` 适配 |
