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
>
> **生成 / 修订**: 2026-07-20（v1.1 按全库代码评审修正优先级与阶段顺序）  
> **代码基线**: 仓库当前 `main`（勿用 `v2.1.0` 暗示已达分发级交付）

---

## 一、MVP 成果确认

### 已完成里程碑

| 里程碑 | 范围 | 验收标准 | 状态 |
|--------|------|----------|------|
| **阶段 0** | 工程骨架 + 契约 + 鉴权 + 任务状态机 | `smoke_health.py` 通过 | ✅ 完成 |
| **MVP-H** | 红果主链路（vendor/hongguo 复用） | 签名/config 就绪时 job 成功并可出 MP4 | ⚠️ 链路代码完成；**产物下载 API 缺失会断 E2E 末步** |
| **MVP-F** | 番茄 Web + App 双模式接入 `FanqiePlatform` | `e2e_fanqie.py` 可建 job 出 TXT（App 需设备/会话） | ⚠️ 代码接入完成；运维依赖重，稳定性见 HANDOFF |
| **薄客户端 UI** | `ui/` HTML+CSS+JS | 复现脚本全部能力 | ❌ **未达标** — 视觉原型 + 部分 API 接线（见第二节） |

### 已交付的核心模块

```
server/
  app/main.py           ✅ FastAPI 入口 + lifespan + 静态 UI 挂载
  app/config.py         ✅ pydantic-settings + lru_cache
  app/models.py         ✅ 统一 DTO
  app/auth.py           ✅ X-API-Key 依赖注入
  app/api/router.py     ⚠️ REST 端点（缺 GET 文件下载；含商业化 Stub）
  app/jobs/manager.py   ⚠️ 进程内 JobManager + JSON 写盘（无启动恢复）
  platforms/base.py     ✅ BasePlatform 抽象
  platforms/registry.py ✅ 懒加载注册表
  platforms/fanqie/     ✅ Web SSR + App 双模式 + Frida 解密预言机
  platforms/hongguo/    ✅ bridge + platform（复用 vendor）

ui/
  index.html            ⚠️ 4 页视觉结构完整
  styles.css            ⚠️ 双主题（含 modal CSS 语法错误）
  app.js                ⚠️ 部分 API 接线；多处失败当成功；Jobs/设置未闭环

scripts/
  smoke_health.py       ✅
  e2e_fanqie.py         ⚠️ 依赖 GET /v1/files/{file_id}
  e2e_hongguo.py        ⚠️ 依赖 GET /v1/files/{file_id}
```

### 与质量门槛的当前差距

1. **E2E 闭环断开**：脚本与 `docs/api.md` 要求 `GET /v1/files/{file_id}`，路由**不存在**（仅有 `GET /v1/files` 列表与 `POST .../open`）。
2. **`scripts/README.md`** 几乎只有番茄样例，缺红果主路径完整示例。
3. **UI 不可作为验收依据**；且失败路径常提示「成功」，会掩盖故障。

---

## 二、已知问题清单（代码评审）

> 优先级: 🔴 P0 阻断验收 → 🟠 P1 本迭代 → 🟡 P2 近期

### ── 服务端 ──

#### 🔴 P0 — 阻断 E2E / 误导验收

| # | 问题 | 位置 | 修复方案 |
|---|------|------|---------|
| **S-P0-0** | **缺产物下载路由**；E2E / 契约依赖 `GET /v1/files/{file_id}` | `api/router.py`（已 import `FileResponse` 未使用） | **恢复契约**：`GET /v1/files/{file_id}` → `resolve_file` + `FileResponse`；`file_id` 可含 `/`（注意 URL 编码）。**不要**另造 `/download` 第三路径 |
| S-P0-1 | API Key 默认值无启动警告 | `app/config.py` / `main.py` lifespan | 默认 key 时 `logging.warning` 醒目提示；生产可后续改为拒绝启动 |
| S-P0-2 | 卡密 Stub 恒返回 `success=True` | `api/router.py` redeem | 返回 **501** 或 `success=False` + 明确「未实现」；UI 隐藏或 disabled 入口 |
| S-P0-3 | `list_files` 只扫 `outputs/` **顶层** | `api/router.py` | 递归 job 子目录，或仅枚举 Job 已登记 `files`；否则本地库恒空 |

#### 🟠 P1 — 本迭代服务端

| # | 问题 | 位置 | 修复方案 |
|---|------|------|---------|
| S-P1-1 | `_persist()` 锁外同步磁盘 IO，堵事件循环 | `jobs/manager.py` | `await asyncio.to_thread(self._persist, record)` |
| S-P1-2 | `jobs_summary` 直读 `_jobs` 绕过锁 | `api/router.py` | `JobManager.summary()` 封装 |
| S-P1-3 | 进度回调在工作线程改 `record` 无锁 | `jobs/manager.py` | 更新经锁或线程安全队列再刷内存 |
| S-P1-4 | 重启后内存 Job 丢失 | `jobs/manager.py` | lifespan 扫描 `jobs/*.json`；`running` → `failed` |
| S-P1-5 | `env_file=".env"` 依赖 CWD | `app/config.py` | `env_file=REPO_ROOT / ".env"` |
| S-P1-6 | `client.py` import 时固化 settings | `fanqie/client.py` | 函数内懒加载 |
| S-P1-7 | `urllib3.disable_warnings()` 全局禁用 | `fanqie/client.py` | 局部 suppress |
| S-P1-8 | `Popen` 字符串拼 explorer 路径 | `api/router.py` open | 列表参数：`["explorer.exe", f"/select,{path}"]` |
| S-P1-9 | `create_job` 无并发上限 | `jobs/manager.py` | 活跃 Job 上限（建议 5），超限 429 |
| S-P1-10 | `jobs_summary` 假速度 / 假磁盘 | `api/router.py` | 速度未知用 `0` 或省略；磁盘失败勿写死 `100.0 GB` |

#### 🟡 P2 — 近期

| # | 问题 | 位置 | 修复方案 |
|---|------|------|---------|
| S-P2-1 | 字体解析失败静默 `{}` | `web_ssr.py` | `logging.warning` |
| S-P2-2 | `extract_initial_state` 手写括号匹配 | `web_ssr.py` | `json.JSONDecoder().raw_decode()` |
| S-P2-3 | fanqie `_run()` web/app 耦合 | `fanqie/platform.py` | 拆私有方法 |
| S-P2-4 | 路由内 format 体积逻辑 | `api/router.py` | `format_bytes()` |
| S-P2-5 | `main.py` 中部 import | `app/main.py` | import 置顶 |
| S-P2-6 | 缺统一 logging，`print` 散落 | 多处 | lifespan `basicConfig` |
| S-P2-7 | `JobStatus.cancelled` 无接口 | `api/router.py` | `DELETE /v1/jobs/{id}` |
| S-P2-8 | 无 `GET /v1/jobs` 列表 | `api/router.py` | 分页 + status 过滤（UI Jobs 页前置） |
| S-P2-9 | 历史 Job 内存无上限 | `jobs/manager.py` | 保留最近 N 条或淘汰已完成 |

---

### ── 前端 UI ──

#### 🔴 P0 — 诚实性与安全

| # | 问题 | 位置 | 修复方案 |
|---|------|------|---------|
| U-P0-1 | `.modal-overlay {` 选择器丢失，弹窗样式失效 | `styles.css` ~1169 | 补全选择器与 `position:fixed; inset:0; ...` |
| U-P0-2 | `innerHTML` 拼接书名/描述，XSS 风险 | `app.js` | `escapeHtml()` 或 `textContent` |
| **U-P0-3** | **多处 catch 仍提示成功**（建 Job / health / 卡密 / open 文件） | `app.js` | 失败必须展示真实错误；禁止假成功 toast |

#### 🟠 P1 — 功能闭环（服务端 E2E 修复后做）

| # | 问题 | 位置 | 修复方案 |
|---|------|------|---------|
| U-P1-1 | `btnSaveSettings` 未绑定 | `app.js` | 写 `state` + `localStorage` 后 `checkServerHealth` |
| U-P1-2 | Jobs 页静态，无真实任务列表 | `app.js` | 依赖 `GET /v1/jobs` 或扩展 summary；`renderJobCard` |
| U-P1-3 | 无任务进度轮询 | `app.js` | 活跃 job `setInterval` 调 `/v1/jobs/{id}` |
| U-P1-4 | health 失败仍绿点 | `app.js` | 失败改红/橙 +「服务不可达」 |
| U-P1-5 | 8+ 按钮无事件 | `app.js` | 见下表 |
| U-P1-6 | 卡密入口对接假成功 Stub | `app.js` / UI | 隐藏或显示「开发中」；对接 501 |

**按钮绑定清单**:

| 元素 | 期望行为 |
|------|---------|
| `btnLoad` | 搜索框内容直接 `loadDetail`（跳过 search） |
| `btnOpenOutputDir` | 打开 outputs（需服务端能力或本地 pywebview） |
| `btnSaveSettings` | 保存 apiBase / apiKey |
| 「全部开始 / 暂停」 | toast「功能开发中」或隐藏 |
| 「清空已完成」 | 仅 UI 移除 success 卡片，或调未来清理 API |
| 设置「恢复默认」 | 重置 localStorage |
| 本地库 filter / 搜索 | 按 media_type / 文件名过滤 |

#### 🟡 P2 — 体验

| # | 问题 | 修复方案 |
|---|------|---------|
| U-P2-1 | 选集只渲前 10 集 | 分页，每页 20 |
| U-P2-2 | 搜索 meta 硬编码 80 集/900 章 | 用 `segments.length` / detail |
| U-P2-3 | nav-badge 硬编码 `3` | 绑 `active_jobs` |
| U-P2-4 | 全局 `user-select: none` | 仅按钮禁用选择 |
| U-P2-5 | active nav border 挤文字 | 预置 transparent border |
| U-P2-6 | 内联 style 过多 | 抽 CSS 类 |
| U-P2-7 | warning 与 fanqie 同色 | warning → `#FB923C` |

---

## 三、后续阶段规划（顺序已按质量门槛重排）

> **原则**：服务端以**脚本 E2E** 为准，不以 UI 为准。  
> **顺序**：恢复 E2E → 服务端稳定 → UI 诚实闭环 → 打包 → 商业化。

### 阶段 0 — 恢复验收闭环（预计 0.5~1 天）← **立即**

- [ ] **S-P0-0** 实现 `GET /v1/files/{file_id}`（契约路径，非新 `/download`）
- [ ] **S-P0-3** `list_files` 与产物目录布局对齐
- [ ] 跑通 `smoke_health` + `e2e_hongguo` / `e2e_fanqie` 至文件落盘
- [ ] 更新 [`scripts/README.md`](./scripts/README.md)：双平台各 ≥1 条可复制命令
- [ ] 同步 [`docs/api.md`](./docs/api.md) 与真实路由

### 阶段 A — 服务端稳定化（预计 2~3 天）

**A-1 Job 恢复与上限**

- [ ] lifespan 加载 `jobs/*.json`；`running` → `failed`
- [ ] 活跃 Job 上限 + 429
- [ ] 进度更新线程安全

**A-2 Job / 文件 API**

- [ ] `GET /v1/jobs` 分页列举（status 过滤）
- [ ] `DELETE /v1/jobs/{job_id}` 取消（可选）
- [ ] `JobManager.summary()`；去掉假速度

**A-3 日志与配置**

- [ ] 统一 `logging`；替换 `print`
- [ ] `.env` 绝对路径；默认 API Key 启动警告
- [ ] Stub redeem → 501 / 明确未实现

**A-4 健壮性**

- [ ] `_persist` → `to_thread`
- [ ] fanqie settings 懒加载、SSL 警告局部化
- [ ] explorer `Popen` 列表参数

### 阶段 B — 客户端诚实闭环（预计 3~5 天）

> 前提：阶段 0 通过；阶段 A 至少具备 job 列表或可轮询单 job。

**B-1 去掉假成功 + P0 UI**

- [ ] U-P0-1 / U-P0-2 / U-P0-3
- [ ] 卡密入口禁用或「开发中」

**B-2 Jobs / 设置**

- [ ] 动态任务列表 + 进度轮询
- [ ] 设置页 localStorage 真保存
- [ ] health 状态色正确

**B-3 搜索/详情体验**

- [ ] 选集分页、真实 meta
- [ ] 按钮绑定清单
- [ ] 本地库过滤（依赖 list_files 修复）

### 阶段 C — 打包与分发（预计 2~3 天）

- [ ] 验证 `scripts/build_exe.py`（含 `ui/`）
- [ ] 依赖清单（Frida / fonttools 等）
- [ ] `docs/release.md`：首次配置、API Key、模拟器前置
- [ ] 版本号与真实能力对齐（勿虚标 v2.1.0 桌面完整版）

### 阶段 D — 商业化基础（规划中，2~4 周）

> 详见 [`business_landing_architecture.md`](./business_landing_architecture.md)。  
> **未实施前**：不在 UI 假装 VIP 已可用。

- [ ] D-1 JWT / 用户表 / VIP 期限（SQLite → PG）
- [ ] D-2 真实卡密核销
- [ ] D-3 Redroid 签名池
- [ ] D-4 限流与配额

---

## 四、技术债确认

| 债项 | 当前状态 | 何时还 |
|------|----------|--------|
| 进程内 `JobManager` | 单机可接受 | 商业化 Celery/RQ |
| JSON 持久化无恢复 | **阶段 A-1** | — |
| 单并发 Frida | 文档限制 + Job 上限 | 商业化签名池 |
| httpx / requests 双栈 | 可接受 | 阶段 A 可统一 httpx |
| 无单元测试 | 技术债 | 阶段 A 补 pytest 骨架 |
| 番茄默认会话 key / 硬编码 ADB 默认值 | 开发便利、易过期 | config / 环境变量；见 HANDOFF |

---

## 五、质量门槛（不可妥协）

1. **每平台至少 1 条脚本可跑的 E2E**，写进 `scripts/README.md`
2. **密钥 / token / Cookie 不提交 git**
3. **生产 API Key 必须覆盖默认值**
4. **服务端完成以脚本 E2E 为准**，不以 UI 为准
5. **敏感路径（ADB、设备 ID）走配置 / 环境变量**
6. **禁止用假成功掩盖 API 失败**（脚本与 UI 均适用）

---

## 六、执行优先级总览

```
立即（阶段 0）
  S-P0-0  恢复 GET /v1/files/{file_id}     ← 验收阻断
  S-P0-3  list_files 与 outputs 布局对齐
  文档    scripts/README + docs/api 对齐
  回归    smoke + e2e 双平台至文件落盘

本迭代（阶段 A — 服务端）
  S-P0-1  API Key 默认值警告
  S-P0-2  Stub redeem 勿假成功
  S-P1-*  persist / 恢复 / summary / 并发 / 配置 / 线程安全

随后（阶段 B — UI）
  U-P0-*  CSS / XSS / 去掉假成功
  U-P1-*  设置 / Jobs / 轮询 / 按钮

再后
  阶段 C  打包分发
  阶段 D  商业化
```

---

## 七、修订记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-20 | v1.0 | MVP 结束初稿（服务端 + 前端问题清单） |
| 2026-07-20 | v1.1 | 全库评审修正：文档层级、S-P0-0 下载缺口、假成功、list 不递归、阶段顺序（服务端先于 UI）、弱化 v2.1.0 完成表述 |
