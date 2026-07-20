# 当前迭代执行文档（Post-MVP）

> **文档层级**（勿与其它文档抢「唯一权威」）:
>
> | 文档 | 职责 |
> |------|------|
> | [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md) | **架构决策**（方案 2、非目标、API 契约原则）— 稳定少改 |
> | **本文 `POST_MVP_PLAN.md`** | **当前迭代 backlog**（问题清单、阶段顺序、本周任务）— 可随评审更新 |
> | [`DEV_ROADMAP.md`](./DEV_ROADMAP.md) | **历史执行记录**（MVP-H/F 已完成任务归档） |
> | [`docs/HANDOFF.md`](./docs/HANDOFF.md) | **逆向/运维知识**（签名、解密、设备坑）— 不写任务状态 |
> | [`business_landing_architecture.md`](./business_landing_architecture.md) | **商业化蓝图**（未实施） |
> | [`docs/release.md`](./docs/release.md) | **打包与首次运行**（阶段 C） |
>
> **生成 / 修订**: 2026-07-20（v1.2 勾选 0/A/B 完成，启动阶段 C）  
> **代码版本**: `0.2.0`（服务端 `__version__`；勿与 UI 历史文案 v2.1.0 混淆）

---

## 一、MVP / 迭代成果确认

### 里程碑

| 里程碑 | 范围 | 验收标准 | 状态 |
|--------|------|----------|------|
| **阶段 0（工程骨架）** | 契约 + 鉴权 + 任务状态机 | `smoke_health.py` | ✅ 完成 |
| **MVP-H** | 红果 vendor 复用 | job 出 MP4（环境就绪时） | ✅ 适配完成 |
| **MVP-F** | 番茄 Web + App | job 出 TXT（App 需设备） | ✅ 代码接入；运维见 HANDOFF |
| **阶段 0（Post-MVP 闭环）** | 恢复下载 API + 列表递归 + 文档 | E2E 可 `GET /v1/files/{id}` | ✅ 完成（`977a506` 一带） |
| **阶段 A** | 服务端稳定化 | Job 恢复/上限/列表/取消/日志 | ✅ 完成 |
| **阶段 B** | UI 诚实闭环 | 无假成功、Jobs 轮询、设置 | ✅ 完成 |
| **阶段 C** | 打包与分发 | `build_exe` + `docs/release.md` | 🔄 **进行中** |
| **阶段 D** | 商业化 | JWT/卡密/Redroid | ⏳ 未开始 |

### 核心模块（当前）

```
server/
  app/*                 ✅ API / Job / 鉴权 / 下载契约
  platforms/fanqie|hongguo  ✅
ui/                     ✅ 诚实错误 + Jobs/设置/本地库
desktop/main.py         ✅ 阶段 C 入口（服务 + 浏览器）
scripts/build_exe.py    ✅ 阶段 C 打包脚本
docs/release.md         ✅ 发布说明
scripts/e2e_*.py        ✅ 依赖 GET /v1/files/{file_id}
```

---

## 二、已知问题清单（历史评审 — 阶段 0/A/B 已关闭）

> 下列 P0/P1 项在 **0.2.0** 代码中已修复；保留表便于追溯。未完成项仅剩 P2 与阶段 C/D。

### 服务端 — 已关闭

| # | 问题 | 状态 |
|---|------|------|
| S-P0-0 | 缺 `GET /v1/files/{file_id}` | ✅ |
| S-P0-1 | 默认 API Key 启动警告 | ✅ |
| S-P0-2 | 卡密 Stub 假成功 | ✅ `success=false` |
| S-P0-3 | list_files 不递归 | ✅ |
| S-P1-1～10 | persist/锁/恢复/env/SSL/explorer/上限/summary 等 | ✅ |
| 评审 Issue 1～12 | 目录 open、分段编码、MIME、DTO 等 | ✅ |

### 前端 — 已关闭（P0/P1）

| # | 问题 | 状态 |
|---|------|------|
| U-P0-1～3 | modal CSS / XSS / 假成功 | ✅ |
| U-P1-1～6 | 设置/Jobs/轮询/health/按钮/卡密 | ✅ |

### 🟡 P2 — 仍可选（不挡阶段 C）

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

---

## 三、阶段规划与勾选

> **原则**：服务端以**脚本 E2E** 为准。顺序：0 闭环 → A 服务端 → B UI → **C 打包** → D 商业化。

### 阶段 0 — 恢复验收闭环 ✅

- [x] **S-P0-0** `GET /v1/files/{file_id:path}`
- [x] **S-P0-3** `list_files` 递归 outputs
- [x] 更新 `scripts/README.md` 双平台示例
- [x] 同步 `docs/api.md`
- [ ] 环境具备时实跑 `smoke_health` + 双平台 e2e 至落盘（**环境受限，暂未执行**）

### 阶段 A — 服务端稳定化 ✅

**A-1 Job 恢复与上限**

- [x] lifespan 加载 jobs；running/pending → failed 并写回
- [x] 活跃 Job 上限 5 + 429
- [x] 进度更新线程安全

**A-2 Job / 文件 API**

- [x] `GET /v1/jobs` 分页 + status
- [x] `DELETE /v1/jobs/{job_id}`
- [x] `JobManager.summary()`；假速度改为 0.0

**A-3 日志与配置**

- [x] `logging.basicConfig`
- [x] `.env` 绝对路径 / frozen 根目录
- [x] Stub redeem 明确未开通

**A-4 健壮性**

- [x] `_persist` → `to_thread`
- [x] fanqie settings 懒加载、SSL 局部 suppress
- [x] explorer 列表参数 + 空格路径

### 阶段 B — 客户端诚实闭环 ✅

- [x] U-P0 CSS / XSS / 假成功
- [x] 卡密仅 `success===true` 关弹窗；Stub 文案
- [x] Jobs 列表 + 3s 轮询
- [x] 设置 localStorage + 恢复默认（稳定 id）
- [x] health 红/绿
- [x] 本地库过滤 / 分段路径编码 / 打开目录

### 阶段 C — 打包与分发 🔄 **当前**

- [x] 提供可用入口 `desktop/main.py`（原脚本依赖缺失文件）
- [x] 重写 `scripts/build_exe.py`（含 `ui/` + `platforms/`，默认不打 vendor）
- [x] 撰写 [`docs/release.md`](./docs/release.md)（首次运行、API Key、依赖、验收表）
- [x] 版本号对齐服务端 `0.2.0`（诚实口径）
- [x] 在本机执行 `python scripts/build_exe.py` 验证出 exe
- [x] 按 `docs/release.md` 检查表做一次发布前冒烟
- [ ] （可选）`INCLUDE_VENDOR=1` 体积与启动验证
- [ ] （可选）noconsole + 日志文件、安装器、CI artifact

### 阶段 D — 商业化基础 ⏳

> 详见 [`business_landing_architecture.md`](./business_landing_architecture.md)。  
> **未实施前**：不在 UI 假装 VIP 已可用。

- [ ] D-1 JWT / 用户表 / VIP 期限
- [ ] D-2 真实卡密核销
- [ ] D-3 Redroid 签名池
- [ ] D-4 限流与配额

---

## 四、技术债确认

| 债项 | 当前状态 | 何时还 |
|------|----------|--------|
| 进程内 `JobManager` | 单机可接受 | 商业化 Celery/RQ |
| JSON 持久化 | ✅ 已恢复 + 中断写回 | — |
| 单并发 Frida | 文档限制 + Job 上限 | 商业化签名池 |
| httpx / requests 双栈 | 可接受 | 可后续统一 httpx |
| 无单元测试 | 技术债 | 补 pytest 骨架 |
| 番茄默认会话 key / ADB 默认路径 | 开发便利 | config / 环境变量 |
| EXE 默认不内嵌 vendor | 有意为之 | release 说明外置 |

---

## 五、质量门槛（不可妥协）

1. **每平台至少 1 条脚本可跑 of E2E**，写进 `scripts/README.md`
2. **密钥 / token / Cookie 不提交 git**
3. **生产 API Key 必须覆盖默认值**
4. **服务端完成以脚本 E2E 为准**，不以 UI 为准
5. **敏感路径走配置 / 环境变量**
6. **禁止用假成功掩盖 API 失败**
7. **对外版本号与 `__version__` / release.md 一致，禁止商业完整版虚标**

---

## 六、执行优先级总览

```
已完成
  阶段 0  下载契约 + 列表递归 + API/脚本文档
  阶段 A  Job 恢复/上限/列表/取消/日志/配置
  阶段 B  UI 诚实闭环 + Jobs/设置

当前（阶段 C）
  [x] desktop/main.py + build_exe.py + docs/release.md + version 0.2.0
  [ ] 本机跑通打包与 EXE 冒烟
  [ ] 发布检查表勾选

再后
  阶段 C 可选增强（安装器 / noconsole / CI）
  阶段 D 商业化
  P2 体验与代码整理
```

---

## 七、修订记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-20 | v1.0 | MVP 结束初稿 |
| 2026-07-20 | v1.1 | 全库评审：P0 下载缺口、阶段顺序、文档层级 |
| 2026-07-20 | v1.2 | 勾选阶段 0/A/B 完成；启动阶段 C（build_exe + release.md + desktop 入口）；版本 0.2.0 |
