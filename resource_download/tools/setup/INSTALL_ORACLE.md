# 红果签名环境安装清单（Windows）

上游默认：**MuMu 12 + root + frida-server 16.x + 红果 App**。

## 已在本机完成的部分

| 项 | 状态 |
|----|------|
| 宿主机 `frida==16.7.19` | 已装到 `server/.venv` |
| `frida-server-16.7.19` android-x86_64 | 已下载到 `tools/setup/frida-server` |
| `vendor/hongguo` | 已 clone |
| MuMu 模拟器 | **需你安装**（官方安装包需 GUI，无法静默完成） |
| 红果 APK | **需你在模拟器内安装** |
| `config.json` | **需从运行中的 App 导出** |

## 本机实测路径（MuMu 6.3 / 2026-07）

| 项 | 值 |
|----|-----|
| 安装目录 | `D:\install\Netease\MuMu` |
| adb | `D:\install\Netease\MuMu\nx_main\adb.exe` |
| 设备 | 由 MuMuManager 按 `MUMU_INSTANCE_NAME=RD测试` 动态发现（不要写死端口） |
| Android | **15** / abi **x86_64** |
| root | 用 `adb root`（`su` 命令可能不存在） |
| frida-server | 已推送并可运行（需 `adb root` 后启动） |

### 1. 安装 MuMu

已安装则跳过。官方：https://mumu.163.com/download/

### 2. 推送 / 启动 frida-server

模拟器开着时在仓库根：

```powershell
.\tools\setup\push_frida.ps1
# 或指定 adb:
.\tools\setup\push_frida.ps1 -Adb "D:\install\Netease\MuMu\nx_main\adb.exe"
```

上游 `start_oracle.ps1` 的 adb 路径是旧版 Player 12，**不要直接用**，已用本脚本替代。

### 3. 安装红果 App

- 包名：`com.phoenix.read`  
- 在模拟器内安装官方/可信 APK，打开一次保证可进首页（免登录即可）。  

### 4. 生成 config.json

按上游 `config.example.json` / `extract_config.py` / 文档，从抓包或工具导出设备与会话，保存为：

```text
vendor/hongguo/config.json
```

**勿提交 git。**

### 5. 验证上游再接本仓

```powershell
cd vendor\hongguo
# 使用装了 frida 的 python，或:
..\..\server\.venv\Scripts\python.exe offline_dl.py search "剧名"
..\..\server\.venv\Scripts\python.exe offline_dl.py series <id> 1-1
```

通过后：

```powershell
cd server
.\.venv\Scripts\python.exe run.py
# 另窗
python scripts\e2e_hongguo.py --search "剧名" --range 1-1
```

## 注意

- frida **宿主与 frida-server 必须同为 16.x**（17 会缺 Java bridge）。  
- 本环境 **不能代替你点安装向导 / 不能代替你装 APK**。  
- 若你已装 MuMu 但路径不同，把实际 `adb.exe` 路径发我，可改 `start_oracle.ps1` 封装脚本。  
