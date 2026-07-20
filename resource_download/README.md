# resource_download

多平台内容下载中转（**方案 2**：托管服务端 + 瘦客户端）。  
当前主路径：**红果**，复用 [zhangbaio/hongguo](https://github.com/zhangbaio/hongguo)；番茄为 Web/App 双模式适配。

## 文档怎么读

| 文档 | 职责 |
|------|------|
| [`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md) | 架构决策与非目标（稳定） |
| [`POST_MVP_PLAN.md`](./POST_MVP_PLAN.md) | **当前迭代任务与问题清单**（执行看这份） |
| [`DEV_ROADMAP.md`](./DEV_ROADMAP.md) | MVP-H/F 历史完成记录 |
| [`docs/api.md`](./docs/api.md) | HTTP API 契约 |
| [`docs/hongguo_setup.md`](./docs/hongguo_setup.md) / [`docs/fanqie_app_setup.md`](./docs/fanqie_app_setup.md) | 平台环境 |
| [`docs/HANDOFF.md`](./docs/HANDOFF.md) | 逆向结论与设备运维坑 |
| [`business_landing_architecture.md`](./business_landing_architecture.md) | 商业化规划（未实施） |

## 目录

```text
server/                 # 中转服务端（FastAPI）
  app/                  # API / 鉴权 / 任务
  platforms/hongguo/    # 适配 vendor/hongguo（主路径）
  platforms/fanqie/     # Web SSR + App 会话
  run.py
ui/                     # Web UI 实验壳（未达「复现脚本全部能力」）
vendor/hongguo/         # 上游 clone（config 自备，勿提交密钥）
scripts/                # smoke / e2e_hongguo / e2e_fanqie
docs/
data/                   # jobs / outputs（本地运行时）
```

## 快速开始（红果主路径）

### 0. 准备上游

```powershell
git clone --depth 1 https://github.com/zhangbaio/hongguo.git vendor/hongguo
# 配置 config.json + 签名环境（Frida / SIGN_SERVER），先在 vendor 内用 offline_dl 验证
```

### 1. 启动本仓服务端

需要 **Python 3.10+**（推荐 `py -3.14`）。

```powershell
cd server
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install requests pycryptodome
python run.py
```

默认：`http://127.0.0.1:8000`，`X-API-Key: dev-key-change-me`。

> **生产环境**请在仓库根或运行目录 `.env` 中设置 `api_key=<随机强密钥>`，默认值仅限本地开发。

浏览器可打开 `http://127.0.0.1:8000/` 或 `/ui/` 查看实验 UI；**验收以脚本为准**。

### 2. 脚本验收

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY  = "dev-key-change-me"
python scripts/smoke_health.py
python scripts/e2e_hongguo.py --search "剧名" --range 1-1
```

更多命令见 [`scripts/README.md`](./scripts/README.md)。

## 里程碑

| 级别 | 范围 | 状态（摘要） |
|------|------|----------------|
| **MVP-H** | 复用 hongguo + relay + e2e 出 MP4 | 适配完成；注意文件下载 API 缺口见 POST_MVP_PLAN |
| **MVP-F** | 番茄 Web/App 接入 | 代码接入；App 依赖设备与会话稳定性 |
| **UI** | 薄客户端 | 实验性，未达标 |
| **之后** | 服务端稳定、订阅/卡密 | 见 POST_MVP_PLAN 阶段 A~D |

## 说明

- 会话与签名在服务端；用户客户端不贴源站 Cookie 作为主路径。  
- 仅供个人学习研究，请遵守平台条款与版权法。
