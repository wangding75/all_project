# 验收脚本（MVP-1）

服务端默认：

```text
API_BASE=http://127.0.0.1:8000
API_KEY=dev-key-change-me
```

## 启动服务端

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

## 冒烟

```powershell
# 仓库根目录
pip install httpx   # 若根环境没有
$env:API_BASE="http://127.0.0.1:8000"
$env:API_KEY="dev-key-change-me"
python scripts/smoke_health.py
```

## 番茄 E2E

```powershell
python scripts/e2e_fanqie.py --id "https://fanqienovel.com/page/你的书ID" --range 1-2
```

产物默认写到 `data/e2e_downloads/`。
