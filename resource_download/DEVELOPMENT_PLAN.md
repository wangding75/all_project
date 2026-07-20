# 多平台内容下载器 — 架构与计划定稿

> **本文职责：锁定架构决策、非目标、API 原则。**  
> **当前迭代 backlog / 已知 Bug / 阶段顺序 → [`POST_MVP_PLAN.md`](./POST_MVP_PLAN.md)。**  
> 旧版 `design_plan.md` 中与本文冲突的部分（本机一体化、全离线无签名等）以本文覆盖。

**定稿日期**：2026-07-18（客户端后置修订同日）  
**文档修订**：2026-07-20 — 标明与 POST_MVP_PLAN 的分工；进度以 POST_MVP_PLAN 为准

---


## 0. 已锁定决策

| 项 | 决策 |
|----|------|
| 总体架构 | **方案 2：瘦客户端 + 中转服务端（托管订阅向）** |
| 红果 | **当前主路径**：复用 **`vendor/hongguo`**（不重写解密/取链） |
| 番茄 | **App 会话为主目标**；Web SSR 可作对照/免费章兜底，不作长期会员主路径 |
| 会话 | **服务端自养**；用户不贴 Cookie |
| 客户端 | **脚本验收优先**；`ui/` 为实验壳，达标前不以 UI 为完成标准 |
| 验收方式 | **`scripts/e2e_hongguo.py` / `e2e_fanqie.py` 等** 打 API |
| 产品优先级 | **红果复用 → 运维/签名稳 → 番茄 App → 服务端稳定 → 客户端诚实闭环** |

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

## 4. 分阶段计划（历史摘要 + 当前指针）

> 细任务只维护在 [`POST_MVP_PLAN.md`](./POST_MVP_PLAN.md)。

### 阶段回顾（完成状态以 POST_MVP_PLAN / DEV_ROADMAP 为准）

| 原阶段 | 内容 | 备注 |
|--------|------|------|
| 0 | 骨架 + 契约 + smoke | 已完成 |
| 1～2 | 番茄 Web + E2E 脚本 | 已接入；App 模式另需设备 |
| 3 | 红果 vendor 适配 + E2E | 主路径；注意文件下载契约缺口 |
| 4 | 双平台脚本回归 | 文档与 API 对齐仍在 POST_MVP 阶段 0 |
| 5 | 瘦客户端 | `ui/` 已有实验实现，**未达标** |
| 6 | 硬化 / 商业化 | 见 POST_MVP 阶段 C/D 与 business 蓝图 |

**当前执行顺序**（摘要，细节只维护在 POST_MVP_PLAN）：

1. 恢复 `GET /v1/files/{file_id}`，跑通双平台 E2E 至文件落盘  
2. 服务端稳定化（Job 恢复、并发上限、日志、Stub 诚实）  
3. UI 去掉假成功，Jobs/设置闭环  
4. 打包分发 → 商业化  

---

## 5. 技术选型

| 层 | 选型 | 备注 |
|----|------|------|
| 服务端 | FastAPI + uvicorn | |
| 任务 | 进程内队列 + JSON 文件（商业化再换） | |
| 番茄 | fonttools + brotli；App 路径 Frida 进程内解密 | |
| 红果 | pycryptodome + vendor/hongguo；签名外置 | |
| 验收 | **Python scripts + httpx** | 主验收面 |
| 桌面/Web UI | `ui/` 静态页挂载；完整桌面壳后置 | 不新增服务端能力 |

---

## 6. 质量门槛

1. 每平台至少 1 条 **脚本可跑的 E2E**（非仅单元测试）。  
2. 红果 spade 真值测试保留。  
3. 密钥/token/Cookie 不入库。  
4. README / `scripts/README` 中的命令与真实行为一致。  
5. **不以「客户端做好了」为服务端完成标准**；以脚本 E2E 为准。  
6. **禁止用假成功掩盖 API 失败**。  

---

## 7. 决策备忘

| 问题 | 结论 |
|------|------|
| 客户端何时做？ | 脚本 E2E 优先；UI 不挡服务端完成判定 |
| 如何验收下载？ | **`scripts/` 请求 API** |
| 番茄中转模式 | 架构同红果；Web 对照，App 会话为主目标 |
| 红果 Cookie | 用户不要；服务端要会话+签名 |
| 迭代任务写哪？ | **POST_MVP_PLAN.md**，本文只锁架构 |

---

## 8. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-18 | 初版：方案 2、番茄优先、红果对齐 hongguo |
| 2026-07-18 | **客户端后置**；主验收改为 scripts E2E；阶段重排 |
| 2026-07-18 | 标明 **MVP-1 / MVP-2**；落地 `server/` + `scripts/` 脚手架 |
| 2026-07-18 | **主路径改为红果**；`vendor/hongguo` 复用 + `platforms/hongguo` 适配 |
| 2026-07-20 | 与 POST_MVP_PLAN 分工；阶段详情归档；补质量门槛第 6 条 |
