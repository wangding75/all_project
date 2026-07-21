# 当前迭代执行文档（Post-MVP）

> **文档层级**（勿与其它文档抢「唯一权威」）:
>
> | 文档 | 职责 |
> |------|------|
> | [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md) | **架构决策**（方案 2、非目标、API 契约原则）— 稳定少改 |
> | **本文 `POST_MVP_PLAN.md`** | **当前迭代 backlog**（问题清单、阶段顺序、本周任务）— 可随评审更新 |
> | [`DEV_ROADMAP.md`](./DEV_ROADMAP.md) | **历史执行记录**（MVP-H/F 已完成任务归档） |
> | [`docs/HANDOFF.md`](./docs/HANDOFF.md) | **逆向/运维知识**（签名、解密、设备坑）— 不写任务状态 |
> | [`docs/release.md`](./docs/release.md) | **打包与首次运行**（阶段 C） |
> | [`docs/STAGE_D_PLAN.md`](./docs/STAGE_D_PLAN.md) | **阶段 D 技术底座**（D-0～D-4 全部完成 ✅） |
> | [`docs/COMMERCIAL_V1_PLAN.md`](./docs/COMMERCIAL_V1_PLAN.md) | **商业产品 V1.0**（**D-4+D-3 出口之后**全面开发） |
> | [`business_landing_architecture.md`](./business_landing_architecture.md) | **商业化蓝图总览** |
>
> **生成 / 修订**: 2026-07-20（v1.5 衔接商业 V1.0 计划）  
> **代码版本**: `0.2.0`（服务端 `__version__`）

---

## 一、MVP / 迭代成果确认

### 里程碑

| 里程碑 | 范围 | 验收标准 | 状态 |
|--------|------|----------|------|
| **阶段 0（工程骨架）** | 契约 + 鉴权 + 任务状态机 | `smoke_health.py` | ✅ 完成 |
| **MVP-H** | 红果 vendor 复用 | job 出 MP4（环境就绪时） | ✅ 适配完成 |
| **MVP-F** | 番茄 Web + App | job 出 TXT（App 需设备） | ✅ 代码接入；运维见 HANDOFF |
| **阶段 0（Post-MVP 闭环）** | 恢复下载 API + 列表递归 + 文档 | E2E 可 `GET /v1/files/{id}` | ✅ 完成（`977a506`） |
| **阶段 A** | 服务端稳定化 | Job 恢复/上限/列表/取消/日志 | ✅ 完成 |
| **阶段 B** | UI 诚实闭环 | 无假成功、Jobs 轮询、设置 | ✅ 完成 |
| **阶段 C** | 打包与分发 | PyWebView 桌面壳 + `build_exe` + release | ✅ 完成（`826250b` 评审修复） |
| **阶段 D** | 商业化技术底座 | [`STAGE_D_PLAN.md`](./docs/STAGE_D_PLAN.md) | ✅ D-0～D-4 全部完成（阶段 D 技术出口） |
| **阶段 E** | 商业产品 V1.0 | [`COMMERCIAL_V1_PLAN.md`](./docs/COMMERCIAL_V1_PLAN.md) | 📋 **阶段 D 出口就绪，准备启动 E0** |

### 核心模块（当前）

```
server/
  app/*                 ✅ API / Job / require_identity(D-0) / 下载契约
  platforms/fanqie|hongguo  ✅
ui/                     ✅ 诚实错误 + Jobs/设置/本地库 + 无边框标题栏
desktop/main.py         ✅ PyWebView 桌面壳 + health 轮询 + js_api
scripts/build_exe.py    ✅ collect-all app/platforms/webview
docs/release.md         ✅ PyWebView 发行说明
docs/STAGE_D_PLAN.md    📋 D-0/D-1/D-2 已落地
scripts/e2e_*.py        ✅ GET /v1/files/{file_id}
```

---

## 二、已知问题清单（历史 — 0/A/B/C 已关闭）

> P0/P1 与阶段 C 桌面壳评审 Issue 1–10 已在 **0.2.0** / `826250b` 关闭。

### 🟡 P2 — 仍可选（不挡阶段 D）

| # | 问题 | 修复方案 |
|---|------|---------|
| S-P2-1 | 字体解析失败静默 | `logging.warning` |
| S-P2-2 | `extract_initial_state` 括号匹配 | `raw_decode` |
| S-P2-3 | fanqie `_run` 拆分 | 私有方法 |
| S-P2-4 | format_bytes 提取 | 工具函数 |
| S-P2-6 | 残余 `print` | 统一 logger |
| S-P2-9 | 历史 Job 内存上限 | 淘汰策略 |
| U-P2-1 | 选集分页 | 每页 20 |
| U-P2-4～7 | user-select / nav border / 内联 style / warning 色 | CSS |
| C-nit | `HOST=0.0.0.0` 时端口/health 探测应用 `127.0.0.1` | desktop 小改 |

---

## 三、阶段规划与勾选

> **原则**：服务端以**脚本 E2E** 为准。顺序：0 → A → B → C → **D（设计后编码）**。

### 阶段 0 — 恢复验收闭环 ✅

- [x] **S-P0-0** `GET /v1/files/{file_id:path}`
- [x] **S-P0-3** `list_files` 递归 outputs
- [x] 更新 `scripts/README.md` 双平台示例
- [x] 同步 `docs/api.md`
- [ ] 环境具备时实跑双平台 e2e 至落盘（**运维验收，持续**）

### 阶段 A — 服务端稳定化 ✅

- [x] Job 恢复 / 上限 429 / 进度线程安全
- [x] `GET /v1/jobs`、`DELETE /v1/jobs/{id}`、`summary()`
- [x] logging、`.env` 路径、Stub redeem、persist 异步、explorer 安全

### 阶段 B — 客户端诚实闭环 ✅

- [x] 假成功清除、XSS、modal CSS
- [x] Jobs 轮询、设置、health 色、本地库、路径编码

### 阶段 C — 打包与分发 ✅

- [x] `desktop/main.py`：PyWebView 无边框窗 + 后台 uvicorn
- [x] `js_api` 规范挂载、health 轮询、端口冲突探测、closed → 退出
- [x] 拖拽 / no-drag CSS；标题栏版本 `v0.2.0`
- [x] `scripts/build_exe.py`：collect-all app/platforms/webview；失败非零退出
- [x] `docs/release.md` 与产物口径（约 60–70MB）对齐
- [x] 本机打包 + 冒烟（health `0.2.0`、窗体拉起）
- [x] 评审修复提交 `826250b`
- [ ] （可选）`INCLUDE_VENDOR=1`、noconsole + 日志文件、安装器、CI

### 阶段 D — 商业化技术底座 🔄 D-0～D-2/D-4 完成

> **实施方案**: [`docs/STAGE_D_PLAN.md`](./docs/STAGE_D_PLAN.md)  
> **D 全部完成后的商业产品开发**: [`docs/COMMERCIAL_V1_PLAN.md`](./docs/COMMERCIAL_V1_PLAN.md)（E0～E6）  
> **业务蓝图**: [`business_landing_architecture.md`](./business_landing_architecture.md)

| 切片 | 内容 | 状态 |
|------|------|------|
| **D-0** | `AUTH_MODE` + `Identity` / `require_identity` | ✅ 完成 |
| **D-1** | SQLite + 用户注册/登录 + JWT | ✅ 完成 |
| **D-2** | 真实卡密核销 + VIP 门闸（jobs） | ✅ 完成 |
| **D-4** | 限流 + 下载配额（先于 D-3） | ✅ 完成 |
| **D-3** | Redroid / 签名池 | ⏳ D-4 之后 |

### 阶段 E — 商业产品 V1.0 📋 排期锁定（D 出口后开工）

> **唯一权威**：[docs/COMMERCIAL_V1_PLAN.md](./docs/COMMERCIAL_V1_PLAN.md)  
> **前提**：D-4 ✅ 且 D-3 ✅（见该文档 §1 出口标准 X1～X5）  
> **目标**：可试售、可运营的商业产品，而非 Demo。

| 切片 | 内容 | 状态 |
|------|------|------|
| **E0** | 发布门禁与履约质量（双平台 e2e 门禁） | 📋 待 D 出口 |
| **E1** | 多用户 Job/文件隔离 | 📋 |
| **E2** | 客户端登录/兑卡/VIP 闭环 | 📋 |
| **E3** | 生产安全默认（禁默认密钥上公网） | 📋 |
| **E4** | 最小运营（封禁/废卡批次） | 📋 |
| **E5** | 可观测性与备份 | 📋 |
| **E6** | 正式发行与 `v1.0.0` 清单 | 📋 |

**D-0 交付**

- [x] `config`: `auth_mode` / `jwt_secret` / `jwt_expire_minutes`
- [x] `auth.py`: `Identity`、`require_identity`、`require_api_key` 别名
- [x] 受保护路由改为 `Depends(require_identity)`；`/health` 公开
- [x] `docs/api.md` 认证章节、`.env.example`
- [x] 模式矩阵单测：dev/dual/jwt_only → 200 路径 / 401 / 501

**D-1 交付**

- [x] SQLite 用户表存储与 ORM 设计
- [x] `/v1/auth/register`, `/v1/auth/login`, `/v1/auth/me` 接口逻辑实现
- [x] 真 JWT 签发与校验（HS256），移除 D-0 501 占位
- [x] `require_identity` 模式矩阵集成及 `dev` 模式下忽略 Bearer token
- [x] pytest 自动化覆盖 12 个关键用例全绿

**D-2 交付**

- [x] SQLite 卡密表 (card_keys) 定义与 lifespan 自动建表
- [x] `/v1/auth/redeem` 替换 Stub 为真数据库事务安全兑换逻辑
- [x] `/v1/jobs` 挂载 `require_vip` 校验，支持 X-API-Key/ops 管理员直接绕过
- [x] `gen_card_keys.py` 命令行卡密生成工具，修复 Windows Unicode 编码异常
- [x] pytest 全绿覆盖，含 5 条 D-2 新增验证用例 (总 17 条测试通过)

**D-4 交付**

- [x] SQLite 每日配额表 (usage_daily) 定义与 lifespan 自动建表
- [x] config.py 和 .env.example 暴露限流与配额配置
- [x] 线程安全的进程内内存 IP 频率限流器 (1 分钟固定窗口)，豁免 /health 及探活
- [x] `/v1/auth/register` 与 `/v1/auth/login` 单独计入严格限流，global 排除双计
- [x] VIP 每日创建任务配额校验，ops/API Key 豁免
- [x] pytest 全绿覆盖，包含 6 条新增集成测试用例 (总 22 条测试通过)



---

## 四、技术债确认

| 债项 | 当前状态 | 何时还 |
|------|----------|--------|
| 进程内 `JobManager` | 单机可接受 | D 后期 / Celery |
| JSON Job 文件 | ✅ 恢复 + 中断写回 | 可选迁 SQLite |
| 单并发 Frida | 上限 + 文档 | D-3 签名池 |
| 全局 API Key | 本机/单租户 | D-1 过渡后弱化 |
| 无单元测试 | 技术债 | D-1 起补 auth 测试 |
| EXE 不内嵌 vendor | 有意 | release 外置说明 |

---

## 五、质量门槛（不可妥协）

1. **每平台至少 1 条脚本可跑的 E2E**，写进 `scripts/README.md`
2. **密钥 / token / Cookie 不提交 git**
3. **生产 API Key / JWT 密钥必须覆盖默认值**
4. **服务端完成以脚本 E2E 为准**，不以 UI 为准
5. **敏感路径走配置 / 环境变量**
6. **禁止用假成功掩盖 API 失败**
7. **对外版本号与 `__version__` / release.md 一致，禁止商业完整版虚标**
8. **阶段 D 编码前须对照 STAGE_D_PLAN；鉴权变更不得 silent break e2e（保留 dev 旁路）**

---

## 六、执行优先级总览

```
已完成
  0 / A / B / C
  D-0 鉴权并存 · D-1 用户 JWT · D-2 卡密与 VIP 门闸 · D-4 限流与日配额

当前
  D-3 签名/设备池     ← 待编码/待设计

D 出口后（全面商业产品开发）
  阶段 E = docs/COMMERCIAL_V1_PLAN.md
  E0 履约门禁 → E1 隔离 → E2 客户端闭环
  → E3 生产安全 → E4 运营 → E5 可观测 → E6 发 v1.0.0

可选穿插
  P2 体验债（不挡 D/E 主线）
```

---

## 七、修订记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-20 | v1.0 | MVP 结束初稿 |
| 2026-07-20 | v1.1 | 全库评审：P0 下载缺口、阶段顺序、文档层级 |
| 2026-07-20 | v1.2 | 勾选 0/A/B；启动阶段 C；版本 0.2.0 |
| 2026-07-20 | v1.3 | 阶段 C ✅；起草 STAGE_D_PLAN |
| 2026-07-20 | v1.4 | D-0 落地 |
| 2026-07-20 | v1.5 | D-1/D-2 完成态；**新增 COMMERCIAL_V1_PLAN（E0～E6）**；明确 D-4→D-3→阶段 E |
