# 番茄 App 正文解密（App 路径）

## 结论

| 步骤 | 说明 |
|------|------|
| 接口 | `GET /reading/reader/full/v` → `data.content`（base64 密文） |
| 解密 | **native** `CryptManager.decrypt(contentB64, keyB64, keyVersion)` |
| 密钥 | `DecryptKey.f()`，本会话为 48 字节 base64；版本 `DecryptKey.b()` = **1001** |
| 输出 | gzip 字节 → gunzip → HTML 正文 |

标准 AES（16/24/32 字节密钥）**无法**直接解 48 字节 key；当前产品路径与红果类似：**Frida 预言机调 App 内 native**。

## 组件

| 路径 | 作用 |
|------|------|
| `server/platforms/fanqie/crypt_oracle.py` | Python 预言机封装 |
| `tools/setup/fanqie_crypt_oracle.js` | Frida RPC（`decrypt` / `maxKeyVersion`） |
| `server/platforms/fanqie/app_content.py` | 密文 → html/text |
| `tools/setup/test_fanqie_crypt_oracle.py` | dump 回归 + live 精确比对 |
| `tmp/fanqie_probe/crypt_dump/device/` | 完整样本（密文/密钥/out.bin/html） |

## 环境

1. MuMu 模拟器，番茄 `com.dragon.read` 已打开  
2. `/data/local/tmp/frida-server`（仅复制源）  
3. 运行时进程名 **`sys_hlpd`**（`AGENT_BIN`，禁止含 `frida`）  
4. host：`ADB`、`ADB_DEVICE=127.0.0.1:16384`、`FRIDA_HOST=127.0.0.1:27042`  
5. Python：`server/.venv` + `frida==16.7.19`

## 回归

```powershell
$env:AGENT_BIN="/data/local/tmp/sys_hlpd"
$env:ADB="D:\install\Netease\MuMu\nx_main\adb.exe"
$env:ADB_DEVICE="127.0.0.1:16384"
$env:FRIDA_HOST="127.0.0.1:27042"
.\server\.venv\Scripts\python.exe -u tools\setup\test_fanqie_crypt_oracle.py
```

期望：`OK exact out.bin match`。

## 密钥

- 开发默认：`FANQIE_CONTENT_KEY` 或 dump 会话密钥（会过期/随设备变化）  
- 生产：attach 后从阅读链路取 `DecryptKey.f()`，或 hook 一次写入本地 key 文件  

## 下一步

1. 签名拉章（复用红果/phoenix `reader/full`）  
2. 自动取 key（会话内缓存 `DecryptKey`）  
3. `FanqiePlatform.download(mode=app)` 整书导出  
