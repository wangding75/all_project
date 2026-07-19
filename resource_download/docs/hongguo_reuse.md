# 红果：复用 zhangbaio/hongguo

## 结论

**优先复用，不重写。** 本仓库通过 `vendor/hongguo` + `platforms/hongguo` 薄适配层接入统一 relay API。

## 可复用能力映射

| 上游模块 | 能力 | 我们怎么用 |
|----------|------|------------|
| `hongguo.py` | search / get_episodes / get_video_tracks / 签名 | `HongguoPlatform.search/detail` |
| `offline_dl.py` | 整剧下载+解密+续传 | `HongguoPlatform.download` → `dl_series` |
| `frida/unwrap_spade.py` | spade → key | 由 offline_decrypt 间接使用 |
| `frida/offline_decrypt.py` | 密文→明文 mp4 | 由 `dl_vid` 间接使用 |
| `frida/oracle.js` + 模拟器 | 签名预言机 | **运行时依赖，不打包进业务** |
| `unidbg-sign` / SIGN_SERVER | 可选签名后端 | 环境变量对接上游 |
| `server.py` | 上游自带 FastAPI | **不直接用**；我们用本仓 `server/app` 统一鉴权/jobs |
| `config.json` | 设备/会话 | 放在 `vendor/hongguo/config.json`（勿提交） |

## 目录

```text
vendor/hongguo/          # git clone 上游（已可本地存在）
server/platforms/hongguo/
  bridge.py              # sys.path + 探测
  platform.py            # BasePlatform 适配
```

## 本机准备

```powershell
# 1) vendor（若无）
git clone --depth 1 https://github.com/zhangbaio/hongguo.git vendor/hongguo

# 2) 会话：按上游 README 生成 config.json → 拷到 vendor/hongguo/config.json

# 3) 签名：启动 Frida oracle 或 SIGN_SERVER（见上游 start_oracle.ps1 / unidbg）

# 4) 本仓服务
cd server
.\.venv\Scripts\Activate.ps1
# 上游依赖（与 hongguo 对齐，按需安装）
pip install requests pycryptodome
# 若用 frida 签名还需 frida==16.x 等，见上游 requirements
python run.py
```

## 验收

```powershell
python scripts/e2e_hongguo.py --search "剧名" --range 1-1
# 或
python scripts/e2e_hongguo.py --id SERIES_ID --range 1-1
```

## 策略

1. **先能在 vendor 目录用 `python offline_dl.py` 跑通**，再调 relay。  
2. 上游更新：`cd vendor/hongguo && git pull`。  
3. 业务层只改 `platforms/hongguo/*`，避免改 vendor 源码（必要时打 patch 文件记录）。  
