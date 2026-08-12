# 阶段进度与 backlog（Post-MVP）

> **[T41 2026-08-12] 架构基线已冻结。**  
> **权威架构文档：[`docs/ARCHITECTURE_BOUNDARY.md`](./docs/ARCHITECTURE_BOUNDARY.md)（NORMATIVE / FROZEN）**  
> 本文档与 ARCHITECTURE_BOUNDARY.md 冲突时，以 ARCHITECTURE_BOUNDARY.md 为准。  
> Server 下载 Job、Server Automation Scheduler、Server 文件库等条目统一标记为  
> `IMPLEMENTATION_MIGRATION_REQUIRED`，详见 [`docs/ARCHITECTURE_MIGRATION_INVENTORY.md`](./docs/ARCHITECTURE_MIGRATION_INVENTORY.md)。

> **文档层级**（勿与其它文档抢「唯一权威」）:
>
> | 文档 | 职责 |
> |------|------|
> | [`docs/ARCHITECTURE_BOUNDARY.md`](./docs/ARCHITECTURE_BOUNDARY.md) | **⭐ 权威架构边界（NORMATIVE / FROZEN）** |
> | [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md) | **历史架构决策**（方案 2、非目标、API 契约原则）— 已向 ARCHITECTURE_BOUNDARY 对齐 |
> | **本文 `POST_MVP_PLAN.md`** | **阶段进度总览 + 剩余 backlog** — 随评审更新 |
> | [`DEV_ROADMAP.md`](./DEV_ROADMAP.md) | **历史执行记录**（MVP-H/F 已完成任务归档） |
> | [`docs/HANDOFF.md`](./docs/HANDOFF.md) | **逆向/运维知识**（签名、解密、设备坑）— 不写工程排期 |
> | [`docs/release.md`](./docs/release.md) / [`docs/deployment.md`](./docs/deployment.md) | **打包与生产部署** |
> | [`docs/release_gate.md`](./docs/release_gate.md) | **商业 V1.0 发版门禁 DoD** |
> | [`docs/STAGE_D_PLAN.md`](./docs/STAGE_D_PLAN.md) | **[Historical] 阶段 D 技术底座**（D-0～D-4 全部完成 ✅） |
> | [`docs/COMMERCIAL_V1_PLAN.md`](./docs/COMMERCIAL_V1_PLAN.md) | **[Historical] 商业产品 V1.0**（E0～E6 全部完成 ✅） |
> | [`business_landing_architecture.md`](./business_landing_architecture.md) | **[Historical] 商业化蓝图总览**（旧 User/JWT/VIP 架构；以 ARCHITECTURE_BOUNDARY 为准） |
> | [`docs/ARCHITECTURE_MIGRATION_INVENTORY.md`](./docs/ARCHITECTURE_MIGRATION_INVENTORY.md) | **代码迁移清单（T41 生成）** |
>
> **修订**: 2026-07-27（v2.0）；2026-08-12（T41 对齐架构基线）  
> **代码版本**: `1.0.0`（`pyproject.toml` / `server/app/version.py`）

---

## 一、当前状态（一句话）

> **工程与商业 V1.0 主线已完成**（阶段 0～C、D-0～D-4、E0～E6、CQ-01～06）。  
> 剩余工作以 **运维实跑、设备侧稳定性、文档/体验债、V1.1+ 外延** 为主，不再有未编码的 D/E 主切片。

---

## 二、里程碑总表

| 里程碑 | 范围 | 验收标准 | 状态 |
|--------|------|----------|------|
| **阶段 0（工程骨架）** | 契约 + 鉴权 + 任务状态机 | `smoke_health.py` | ✅ |
| **MVP-H** | 红果 vendor 复用 | job 出 MP4（环境就绪时） | ✅ 适配完成 |
| **MVP-F** | 番茄 Web + App | job 出 TXT（App 需设备） | ✅ 代码接入；运维见 HANDOFF |
| **阶段 0（Post-MVP 闭环）** | 下载 API + 列表递归 + 文档 | E2E 可 `GET /v1/files/{id}` | ✅ |
| **阶段 A** | 服务端稳定化 | Job 恢复/上限/列表/取消/日志 | ✅ |
| **阶段 B** | UI 诚实闭环 | 无假成功、Jobs 轮询、设置 | ✅ |
| **阶段 C** | 打包与分发 | PyWebView + `build_exe` + release | ✅ |
| **阶段 D** | 商业化技术底座 | [`STAGE_D_PLAN.md`](./docs/STAGE_D_PLAN.md) | ✅ D-0～D-4 |
| **阶段 E** | 商业产品 V1.0 | [`COMMERCIAL_V1_PLAN.md`](./docs/COMMERCIAL_V1_PLAN.md) | ✅ E0～E6 |
| **CQ-01～06** | 代码质量修正 | 任务书 + `test_cq0*.py` / `quality_gate` | ✅ |

### 核心模块（当前）

```
server/
  app/*                 ✅ API / Job / Identity / 配额 / 签名池 / admin / 安全启动
  platforms/fanqie|hongguo  ✅
client/ui/              ✅ 登录/兑卡/VIP + Jobs/设置（瘦客户端，无平台适配）
client/desktop/main.py  ✅ 默认 thin 连 API；embedded 仅开发
scripts/                ✅ e2e / build_exe / ops_admin / backup / quality_gate
docs/release_gate.md    ✅ V1.0 DoD 全勾
docs/deployment.md      ✅ 生产部署
docs/ops_runbook.md     ✅ 运营手册
docs/sign_pool.md       ✅ 签名池
```

---

## 三、阶段勾选明细

### 阶段 0 — 恢复验收闭环 ✅

- [x] **S-P0-0** `GET /v1/files/{file_id:path}`
- [x] **S-P0-3** `list_files` 递归 outputs
- [x] 更新 `scripts/README.md` 双平台示例
- [x] 同步 `docs/api.md`
- [ ] 环境具备时实跑双平台 e2e 至落盘（**运维验收，持续**）

### 阶段 A — 服务端稳定化 ✅

- [x] Job 恢复 / 上限 429 / 进度线程安全
- [x] `GET /v1/jobs`、`DELETE /v1/jobs/{id}`、`summary()`
- [x] logging、`.env` 路径、persist 异步、explorer 安全

### 阶段 B — 客户端诚实闭环 ✅

- [x] 假成功清除、XSS、modal CSS
- [x] Jobs 轮询、设置、health 色、本地库、路径编码

### 阶段 C — 打包与分发 ✅

- [x] `client/desktop/main.py`：PyWebView；生产 thin / 开发可 embedded
- [x] `js_api`、health 轮询、端口冲突探测、closed → 退出
- [x] `scripts/build_exe.py`；`docs/release.md`
- [x] 正式包支持 `--noconsole` + 日志文件路径（E6）
- [ ] （可选）`INCLUDE_VENDOR=1`、安装器、代码签名、CI 产物

### 阶段 D — 商业化技术底座 ✅

> 方案：[`docs/STAGE_D_PLAN.md`](./docs/STAGE_D_PLAN.md) · 签名池：[`docs/sign_pool.md`](./docs/sign_pool.md)

| 切片 | 内容 | 状态 |
|------|------|------|
| **D-0** | `AUTH_MODE` + `Identity` / `require_identity` | ✅ |
| **D-1** | SQLite + 用户注册/登录 + JWT | ✅ |
| **D-2** | 真实卡密核销 + VIP 门闸（jobs） | ✅ |
| **D-4** | 限流 + 下载配额 | ✅ |
| **D-3** | 签名节点池（可开关；关则回落本机 Frida） | ✅ |

### 阶段 E — 商业产品 V1.0 ✅

> 方案：[`docs/COMMERCIAL_V1_PLAN.md`](./docs/COMMERCIAL_V1_PLAN.md) · 门禁：[`docs/release_gate.md`](./docs/release_gate.md)

| 切片 | 内容 | 状态 |
|------|------|------|
| **E0** | 发布门禁与履约质量 | ✅ |
| **E1** | 多用户 Job/文件隔离 | ✅ |
| **E2** | 客户端登录/兑卡/VIP 闭环 | ✅ |
| **E3** | 生产安全默认（禁默认密钥上公网） | ✅ |
| **E4** | 最小运营（封禁/废卡批次 + ops CLI） | ✅ |
| **E5** | 可观测性与备份 | ✅ |
| **E6** | 发行清单与版本 `1.0.0`（门禁文档全勾） | ✅ |

> **说明**：git tag / GitHub Release **非本文档范围**；工程侧 release_gate 已就绪，是否打标由发布流程另行决定。

### CQ — 代码质量修正 ✅

| 切片 | 内容 | 状态 |
|------|------|------|
| **CQ-01** | 唯一版本源 + 单 Worker 约束 | ✅ |
| **CQ-02** | 测试可信度（无模糊断言/无真外网） | ✅ |
| **CQ-03** | Job 取消生命周期 | ✅ |
| **CQ-04** | 原子持久化与优雅关闭 | ✅ |
| **CQ-05** | 可复现依赖与构建 | ✅ |
| **CQ-06** | 质量门禁 + 部署文档 | ✅ |

---

## 四、剩余 backlog（当前真正未完成）

### 运维 / 履约（持续）

| # | 项 | 说明 |
|---|----|------|
| OPS-1 | 双平台 e2e 实环境落盘 | 依赖模拟器/签名；门禁脚本在，需定期人工复验 |
| OPS-2 | 签名池实机压测 | 代码与 mock 测已有；生产节点需按 `sign_pool.md` 部署 |
| OPS-3 | 番茄设备稳定性 | 番茄进程 + Frida attach/会话 key（**不依赖红果签名**；见 HANDOFF） |

### 🟡 P2 — 可选体验债（不挡 V1.0）

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
| C-nit | `HOST=0.0.0.0` 时 health 探测用 `127.0.0.1` | desktop 小改 |

### 研究项（非工程阻塞）

| # | 项 | 说明 |
|---|----|------|
| R-1 | 番茄 native 解密离线化 | 算法/密钥派生未解；须进程内 decrypt |
| R-2 | Web×App 50 章自动对齐报告 | 采样齐，自动对比未收口 |

### V1.1+（明确非 V1.0 范围）

支付直连、完整 Web 运营后台、Celery/多机 Job、100% 绕过平台风控承诺 — 见 `COMMERCIAL_V1_PLAN` §12。

---

## 五、技术债确认

| 债项 | 当前状态 | 何时还 |
|------|----------|--------|
| 进程内 `JobManager` | 单机可接受 | **IMPLEMENTATION_MIGRATION_REQUIRED**：目标由 Client Download Manager 承担 |
| JSON Job 文件 | ✅ 恢复 + 原子写入 + 中断写回 | **IMPLEMENTATION_MIGRATION_REQUIRED**：Job 持久化目标迁 Client SQLite |
| Server Automation Scheduler | 当前存在 `server/app/automation/` | **IMPLEMENTATION_MIGRATION_REQUIRED**：目标由 Client Timer 驱动 |
| Server `/v1/files` 文件 API | 当前存在 | **DEPRECATE_API**：目标文件只在 Client 本地 |
| 单并发 Frida | 有签名池抽象；本机仍受设备限制 | 扩池 + 运维 |
| 全局 API Key | dev/运维旁路保留 | 生产用 dual/jwt_only |
| 单元测试 | ✅ auth/quota/isolation/pool/CQ 等 | 持续补强 |
| EXE 不内嵌 vendor | 有意 | release 外置说明 |

---

## 六、质量门槛（不可妥协）

1. **每平台至少 1 条脚本可跑的 E2E**，写进 `scripts/README.md`
2. **密钥 / token / Cookie 不提交 git**
3. **生产 API Key / JWT 密钥必须覆盖默认值**
4. **服务端完成以脚本 E2E 为准**，不以 UI 为准
5. **敏感路径走配置 / 环境变量**
6. **禁止用假成功掩盖 API 失败**
7. **对外版本号与 `version.py` / 文档一致**
8. **鉴权变更不得 silent break e2e（保留 `AUTH_MODE=dev` 旁路）**
9. **单进程 `WORKERS=1`**；多 Worker 配置须拒绝启动

---

## 七、执行优先级总览

```
已完成
  0 / A / B / C
  D-0～D-4（含签名池）
  E0～E6（商业 V1.0 工程）
  CQ-01～06（代码质量）

当前（非主线编码）
  文档与代码保持同步
  运维实跑 e2e / 签名池节点
  可选 P2 体验债
  V1.1+ 另立项
```

---

## 八、修订记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-20 | v1.0 | MVP 结束初稿 |
| 2026-07-20 | v1.1 | 全库评审：P0 下载缺口、阶段顺序、文档层级 |
| 2026-07-20 | v1.2 | 勾选 0/A/B；启动阶段 C；版本 0.2.0 |
| 2026-07-20 | v1.3 | 阶段 C ✅；起草 STAGE_D_PLAN |
| 2026-07-20 | v1.4 | D-0 落地 |
| 2026-07-20 | v1.5 | D-1/D-2 完成态；新增 COMMERCIAL_V1_PLAN；明确 D-4→D-3→阶段 E |
| 2026-07-27 | **v2.0** | 对齐 `1.0.0`：D-3/E0–E6/CQ 全部 ✅；本文改为进度总览 + 剩余 backlog；取消「D-3 待编码」等过期表述 |
| 2026-08-12 | **v2.1** | [T41] 对齐 ARCHITECTURE_BOUNDARY.md：标记 Server Job/Automation/FileAPI 为 IMPLEMENTATION_MIGRATION_REQUIRED；更新文档层级表；添加架构基线冻结说明 |
