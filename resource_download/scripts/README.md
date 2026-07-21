# 验收脚本

服务端默认：

```text
API_BASE=http://127.0.0.1:8000
API_KEY=dev-key-change-me
```

质量门槛：每平台至少 1 条可复制命令的 E2E；**以脚本结果为准，不以 UI 为准**。

---


## 启动服务端

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# 红果解密等还可能需要：requests pycryptodome（见根 README）
python run.py
```

另开终端，在**仓库根目录**设置环境变量后跑脚本。

---

## 冒烟

```powershell
pip install httpx   # 若当前环境没有
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY  = "dev-key-change-me"
python scripts/smoke_health.py
```

期望：HTTP 200，`platforms` 含 `hongguo` / `fanqie`。

---

## 阶段 E0 自动化冒烟与 E2E (`ci_smoke.ps1` / `ci_smoke.sh`)

发版前一键冒烟检查脚本：

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY  = "dev-key-change-me"

# 可选注入真实样例 ID（无 ID 时 E2E 自动输出 [SKIP] 并 exit 0）
$env:E2E_FANQIE_ID = "https://fanqienovel.com/page/7000000000000000000"
$env:E2E_HONGGUO_ID = "7000000000000000000"

powershell scripts/ci_smoke.ps1
# 或 Bash:
# ./scripts/ci_smoke.sh
```

---

## 红果 E2E（主路径）

前置：

1. `vendor/hongguo` 已 clone，且上游可独立 `offline_dl` 出片  
2. 设备/会话 `config.json` 与签名后端（Frida / SIGN_SERVER）可用  
3. 详见 [`docs/hongguo_setup.md`](../docs/hongguo_setup.md)

```powershell
$env:API_BASE = "http://127.0.0.1:8000"
$env:API_KEY  = "dev-key-change-me"

# 按 series_id
python scripts/e2e_hongguo.py --id "SERIES_ID" --range 1-1

# 或先搜索再取第一条
python scripts/e2e_hongguo.py --search "剧名关键词" --range 1-1
```

期望：job `success`，`data/e2e_downloads/` 下有可播 MP4（若下载 API 未恢复，至少 `data/outputs/{job_id}/` 有文件）。

---

## 番茄 E2E

### Web 模式（默认，无需 Frida）

```powershell
python scripts/e2e_fanqie.py --id "https://fanqienovel.com/page/你的书ID" --range 1-2
# 或纯数字 book_id
python scripts/e2e_fanqie.py --id "BOOK_ID" --range 1-2
```

### App 模式（需模拟器 + 解密预言机）

前置见 [`docs/fanqie_app_setup.md`](../docs/fanqie_app_setup.md)。

```powershell
python scripts/e2e_fanqie.py --id "BOOK_ID" --range 1-3 --options "{\"mode\":\"app\"}"
```

产物默认写到 `data/e2e_downloads/`。

---

## 打包（阶段 C）

详见 [`docs/release.md`](../docs/release.md)。

```powershell
# 仓库根目录；已激活含依赖的 venv
pip install pyinstaller pycryptodome
python scripts/build_exe.py
# 产物: dist/ResourceDownloader.exe
```

桌面入口源码：`desktop/main.py`（启动服务并打开浏览器）。

---

## 脚本列表

| 脚本 | 作用 |
|------|------|
| `smoke_health.py` | `/health` 冒烟 |
| `e2e_hongguo.py` | 红果 search/detail → job → poll → 下文件 |
| `e2e_fanqie.py` | 番茄 detail → job → poll → 下文件 |
| `build_exe.py` | PyInstaller 打 Windows 单文件（含 ui + platforms） |
| `_common.py` | `API_BASE` / `API_KEY` / httpx 客户端 |

---

## 退出码

- `0`：成功  
- 非 `0`：search/detail/job/file 任一步失败（见 stderr）
