# DEV_ROADMAP — MVP 历史执行记录

> **文档状态：归档。** 阶段进度与剩余 backlog 以 [`POST_MVP_PLAN.md`](./POST_MVP_PLAN.md) 为准。  
> 架构决策以 [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md) 为准。  
> 商业 V1.0 完成态见 [`docs/COMMERCIAL_V1_PLAN.md`](./docs/COMMERCIAL_V1_PLAN.md) / [`docs/release_gate.md`](./docs/release_gate.md)。
>
> - 商业化蓝图：[business_landing_architecture.md](./business_landing_architecture.md)
> - 历史设计存档：[design_plan.md](./design_plan.md)
>
> 正文为 **MVP-H/F 完成时快照（约 2026-07-19）**；后续勿在此追加新任务。  
> 商业化 / 阶段 D～E / CQ **不要**以本文「规划中」表述为准——已过时。

---


## 一、当前代码状态（截至 2026-07-19）

### 已完成

| 模块 | 内容 |
|------|------|
| `server/app/main.py` | FastAPI 入口 + lifespan 目录初始化 |
| `server/app/config.py` | pydantic-settings 配置（.env 驱动） |
| `server/app/models.py` | 统一 DTO（PlatformName / JobStatus / JobResponse 等） |
| `server/app/auth.py` | X-API-Key 鉴权依赖 |
| `server/app/api/router.py` | 完整 REST 路由（health/search/detail/jobs/files） |
| `server/app/jobs/manager.py` | 进程内 JobManager（asyncio + JSON 持久化） |
| `server/platforms/base.py` | BasePlatform 抽象接口 |
| `server/platforms/registry.py` | 平台注册表（懒加载） |
| `server/platforms/fanqie/` | Web SSR + App 模式（字体解密/Frida 解密/client） |
| `server/platforms/hongguo/` | bridge + platform（复用 vendor/hongguo） |
| `scripts/e2e_fanqie.py` | 番茄端到端验收脚本 |
| `scripts/e2e_hongguo.py` | 红果端到端验收脚本 |
| `scripts/smoke_health.py` | 健康检查脚本 |

### 已知 Bug（代码评审发现，**必须先修**）

| 优先级 | Bug | 文件 | 说明 | 状态 |
|--------|-----|------|------|------|
| 🔴 P0 | `HERE` 未定义 | `platforms/fanqie/client.py:106` | App 模式 `init_frida()` 使用 `HERE` 但未定义 | ✅ 已修复 (`f7b83e2`) |
| 🔴 P1 | 路径穿越漏洞 | `jobs/manager.py:93` | `file_id` 直接拼接路径，需加 `resolve()` + `is_relative_to()` 校验 | ✅ 已修复 (`0163e2c`) |
| 🟠 P2 | 全局 HEADERS 并发竞争 | `platforms/fanqie/web_ssr.py:14` | 多并发任务 Cookie 互相覆盖 | ✅ 已修复 (`15cc3a0`) |
| 🟠 P2 | `get_settings()` 未缓存 | `app/config.py:39` | 每次请求重新读 .env，需加 `@lru_cache` | ✅ 已修复 (`16b7e75`) |
| 🟡 P3 | 缺 `requests` 依赖声明 | `server/requirements.txt` | `fanqie/client.py` import requests 但未声明 | ✅ 已修复 (`9ee43fc`) |

---

## 二、里程碑总览

| 里程碑 | 目标 | 验收标准 | 状态 |
|--------|------|----------|------|
| **MVP-H** | 红果主链路打通 | `e2e_hongguo.py` 出可播 MP4 | ✅ 已完成 |
| **MVP-F** | 番茄 App 会话打通 | `e2e_fanqie.py` App 模式出书 | ✅ 已完成 |
| **Client** | 薄客户端 UI | UI 复现脚本所有功能 | ⚠️ 有 `ui/` 原型，未达标 → 见 POST_MVP_PLAN |
| **商业化** | VIP + 卡密 + 签名池 + V1.0 | 见 COMMERCIAL_V1_PLAN / release_gate | ✅ 工程完成（本文档归档后实现） |

---

## 三、第一步：修复 Bug（今天先做，预计 0.5 天）

### Task 1 — 修复 `HERE` 未定义（P0）

**文件**：`server/platforms/fanqie/client.py`

在文件顶部 import 区域末尾添加：

```python
HERE = Path(__file__).resolve().parent
```

---

### Task 2 — 修复路径穿越漏洞（P1）

**文件**：`server/app/jobs/manager.py` — `resolve_file` 方法

```python
def resolve_file(self, file_id: str) -> Path | None:
    for record in self._jobs.values():
        for f in record.files:
            if f.file_id == file_id:
                path = Path(f.path) if f.path else None
                if path and path.is_file():
                    return path
    # 路径安全校验：防止路径穿越攻击
    outputs_root = self.settings.outputs_dir.resolve()
    candidate = (outputs_root / file_id).resolve()
    if not candidate.is_relative_to(outputs_root):
        return None
    if candidate.is_file():
        return candidate
    return None
```

---

### Task 3 — 修复全局 HEADERS 并发竞争（P2）

**文件**：`server/platforms/fanqie/web_ssr.py`

```python
# 改前：全局可变字典（线程不安全）
HEADERS = {"User-Agent": "..."}
def set_cookie(cookie): ...

# 改后：工厂函数，每次返回独立副本
_BASE_HEADERS = {"User-Agent": "..."}

def make_headers(cookie: str | None = None) -> dict:
    h = dict(_BASE_HEADERS)
    if cookie:
        h["Cookie"] = cookie
    return h
```

同步更新 `fetch_url`、`fetch_bytes`、`download_chapter` 等所有调用方传入 `make_headers(cookie)`。

---

### Task 4 — 缓存 `get_settings()`（P2）

**文件**：`server/app/config.py`

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

---

### Task 5 — 补充 `requests` 依赖（P3）

**文件**：`server/requirements.txt`，添加：

```
requests>=2.31
```

---

## 四、MVP-H：红果主链路（当前阶段，预计 2~5 天）

### 环境前置（人工）

```powershell
git clone --depth 1 https://github.com/zhangbaio/hongguo.git vendor/hongguo
# 在 vendor 内先独立跑通，确认签名 OK
cd vendor/hongguo
python offline_dl.py <series_id> --range 1-1
```

### 编码任务

| Task | 描述 | 验收 | 状态 |
|------|------|------|------|
| H-1 | `vendor/hongguo` 独立运行出 MP4 | 手动验证 | ✅ 已完成 |
| H-2 | `smoke_health.py` 验证 hongguo 接入 | health 返回 hongguo | ✅ 已完成 |
| H-3 | `e2e_hongguo.py` 全链路跑通 | MP4 > 0 字节且可播 | ✅ 已完成 |
| H-4 | 签名宕机时错误明确，不影响番茄链路 | 502 含提示信息 | ✅ 已完成 (`c846caf`) |
| H-5 | 编写 `docs/hongguo_setup.md` | 他人可复现 | ✅ 已完成 (`cc17ebb`) |

### 验收命令

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY  = "dev-key-change-me"

python scripts/smoke_health.py
python scripts/e2e_hongguo.py --search "剧名" --range 1-1
```

---

## 五、MVP-F：番茄 App 会话（已完成）

### 前置条件

- MVP-H 已验收通过
- MuMu 模拟器已安装番茄小说 (`com.dragon.read`)
- `tools/setup/fanqie_crypt_oracle.js` 已部署

### 编码任务

| Task | 描述 | 文件 | 状态 |
|------|------|------|------|
| F-1 | 修复 `HERE` 变量（= Task 1） | `fanqie/client.py` | ✅ 已完成 (`f7b83e2`) |
| F-2 | 独立验证 `FanqieCryptOracle.attach()` | 临时测试脚本 | ✅ 已完成 |
| F-3 | `e2e_fanqie.py` App 模式全链路跑通 | E2E 脚本 | ✅ 已完成 |
| F-4 | Web SSR 模式回归不受影响 | `e2e_fanqie.py` 默认 mode=web | ✅ 已完成 |
| F-5 | ADB 路径统一到 `config.py`，消除两处硬编码 | `config.py` + `client.py` + `crypt_oracle.py` | ✅ 已完成 (`b296e4c`) |
| F-6 | 编写 `docs/fanqie_app_setup.md` | 他人可复现 | ✅ 已完成 (`8bd2608`) |

### 验收命令

```powershell
python scripts/e2e_fanqie.py --id "https://fanqienovel.com/page/<BOOK_ID>" --range 1-3
python scripts/e2e_fanqie.py --id "<BOOK_ID>" --range 1-3 --options "{\"mode\":\"app\"}"
```

---

## 六、双平台稳定与质量改善（预计 1~2 天）

### 代码质量任务

| Task | 描述 | 优先级 |
|------|------|--------|
| Q-1 | 引入 `logging`，替换所有 `print()` | 🟠 |
| Q-2 | `JobManager` 限制最大历史 Job 数（防内存泄漏） | 🟠 |
| Q-3 | 启动时扫描 `jobs/*.json` 恢复历史 Job 到内存 | 🟡 |
| Q-4 | 统一 HTTP 客户端为 `httpx`（移除 `requests`） | 🟡 |
| Q-5 | `download()` 拆分 web/app 两个私有方法 | 🟡 |
| Q-6 | 添加 pytest 单元测试骨架 | 🟡 |

### 文档任务

| Task | 描述 |
|------|------|
| D-1 | `scripts/README.md` 补充完整示例（两平台各 ≥1 条） |
| D-2 | `docs/hongguo_setup.md` 完整配置步骤 |
| D-3 | `docs/fanqie_app_setup.md` 完整配置步骤 |

---

## 七、薄客户端 UI（后置，阶段 5，预计 3~7 天）

**前提**：双平台脚本链路已稳定，E2E 可重复。

### 技术栈选型（开工时二选一锁死）

| 方案 | 优点 | 缺点 |
|------|------|------|
| **PyWebView** | 原生 WebView，前端 HTML/CSS/JS，轻量 | Windows 打包依赖复杂 |
| **PySide6** | Qt 控件成熟稳定，原生体验好 | UI 代码量更大 |

### 功能范围

- 平台切换（红果 / 番茄）
- 搜索 + 详情（含封面、集数/章节列表）
- 任务队列（创建 / 进度轮询 / 下载文件）
- 设置页（API_BASE / API_KEY / 下载目录）

> UI 不新增服务端能力，仅复现脚本已能完成的操作。

---

## 八、商业化（阶段 6 — 历史规划摘录）

> **实现状态**：用户/JWT/卡密/VIP/限流配额/签名池/商业 V1.0 已在后续阶段完成。  
> 以 [`POST_MVP_PLAN.md`](./POST_MVP_PLAN.md)、[`docs/COMMERCIAL_V1_PLAN.md`](./docs/COMMERCIAL_V1_PLAN.md) 为准。  
> 下文保留为 MVP 时期蓝图摘录，部分条目（如立刻上 PostgreSQL）**并非 V1.0 实际路径**。

详见 [business_landing_architecture.md](./business_landing_architecture.md)。

历史设想（摘录）：

1. SQLite → PostgreSQL 数据库（V1.0 仍用 SQLite）
2. 用户注册 / 登录 / JWT 鉴权（✅ 已做；dev 仍可 API Key）
3. 卡密体系（✅）
4. 签名/设备池（✅ 抽象已做；实机节点运维持续）
5. 限流 + 配额管理（✅）

---

## 九、技术债与规范

### 已认可的技术债（MVP 期间可接受）

| 债项 | 描述 | 何时还 |
|------|------|--------|
| 进程内 JobManager | 无法多进程/多机扩展 | 商业化阶段换 Celery/RQ |
| JSON 文件持久化 | 重启后内存状态丢失 | 稳定期引入 SQLite |
| 单并发 Frida 连接 | 多任务并发可能冲突 | 文档说明限制，暂不处理 |

### 质量门槛（不可妥协）

1. 每平台至少 1 条脚本可跑的 E2E，并写进 `scripts/README.md`
2. 密钥 / token / Cookie **不提交 git**（`.gitignore` 已配置）
3. 生产环境 API Key 必须在 `.env` 覆盖，禁止默认值
4. 服务端完成标准以**脚本 E2E 为准**，非 UI

---

## 十、立即执行顺序

```
Bug 修复（✅ 已完成）
  Task 1  修复 HERE 变量（P0）                      ✅ (f7b83e2)
  Task 2  修复路径穿越漏洞（P1）                    ✅ (0163e2c)
  Task 3  修复全局 HEADERS 并发竞争（P2）            ✅ (15cc3a0)
  Task 4  缓存 get_settings()（P2）                 ✅ (16b7e75)
  Task 5  补充 requirements.txt（P3）              ✅ (9ee43fc)

MVP-H：红果主链路（✅ 已完成）
  H-1  vendor/hongguo 独立验证                      ✅
  H-2  smoke_health 验证接入                        ✅
  H-3  e2e_hongguo 全链路跑通                       ✅ (MVP-H 核心目标)
  H-4  签名后端错误隔离                             ✅ (c846caf)
  H-5  hongguo_setup.md 文档                        ✅ (cc17ebb)

MVP-F：番茄 App 会话（✅ 已完成）
  F-1 ~ F-6  番茄 App 会话链路                      ✅ (b296e4c / 8bd2608)

后续演进 → 一律以 POST_MVP_PLAN.md 为准
  阶段 0  恢复 GET /v1/files/{file_id} 与 E2E 闭环
  阶段 A  服务端稳定化
  阶段 B  UI 诚实闭环
  阶段 C  打包分发
  阶段 D  商业化
```
