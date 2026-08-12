# 番茄 App 正文解密（App 路径）

## 结论

| 步骤 | 说明 |
|------|------|
| 接口 | `GET /reading/reader/full/v` → `data.content`（base64 密文） |
| 解密 | **native** `CryptManager.decrypt(contentB64, keyB64, keyVersion)` |
| 密钥 | `DecryptKey.f()`，本会话为 48 字节 base64；版本 `DecryptKey.b()` = **1001** |
| 输出 | gzip 字节 → gunzip → HTML 正文 |

标准 AES（16/24/32 字节密钥）**无法**直接解 48 字节 key；当前产品路径：**Frida 预言机调番茄 App 内 native**（与红果签名无关）。

## 组件

| 路径 | 作用 |
|------|------|
| `server/platforms/fanqie/device.py` | 启动番茄 / 复用 Frida agent（不 pkill） |
| `server/platforms/fanqie/client.py` + `oracle_sign.js` | **番茄本进程**签名拉章 |
| `server/platforms/fanqie/crypt_oracle.py` | 解密预言机封装 |
| `tools/setup/fanqie_crypt_oracle.js` | Frida RPC（`decrypt` / `maxKeyVersion`） |
| `server/platforms/fanqie/app_content.py` | 密文 → html/text |
| `tools/setup/test_fanqie_crypt_oracle.py` | dump 回归 + live 精确比对 |
| `tmp/fanqie_probe/crypt_dump/device/` | 完整样本（密文/密钥/out.bin/html） |

## 环境

1. MuMu 模拟器，番茄 `com.dragon.read`（**无需**安装/打开红果）  
2. `/data/local/tmp/frida-server`（或 `AGENT_BIN=sys_hlpd` 伪装副本）  
3. 与红果同机时：**共用 agent、分 pid attach**；番茄路径不会杀 agent  
4. host：`ADB`、`MUMU_INSTANCE_NAME=RD测试`、`FRIDA_HOST=127.0.0.1:27042`；ADB serial 由 discovery 取得。
5. Python：`server/.venv` + 与 agent 匹配的 frida

## 回归

```powershell
$env:AGENT_BIN="/data/local/tmp/sys_hlpd"
$env:ADB="D:\install\Netease\MuMu\nx_main\adb.exe"
$env:MUMU_INSTANCE_NAME="RD测试"
$env:FRIDA_HOST="127.0.0.1:27042"
.\server\.venv\Scripts\python.exe -u tools\setup\test_fanqie_crypt_oracle.py
```

期望：`OK exact out.bin match`。

## 密钥

- 开发默认：`FANQIE_CONTENT_KEY` 或 dump 会话密钥（会过期/随设备变化）  
- 生产：attach 后从阅读链路取 `DecryptKey.f()`，或 hook 一次写入本地 key 文件  

## 下一步

1. ✅ 签名拉章：番茄本进程 `NetworkParams`（不依赖红果/phoenix）  
2. 自动取 key（会话内缓存 `DecryptKey`）  
3. ✅ `FanqiePlatform.download(mode=app)` 整书导出  

