# 资源下载项目交接文档

> 更新日期：2026-07-27  
> 仓库：`resource_download`  
> 范围：番茄小说 + 红果短剧 多端下载 / 托管服务方向  
>
> **本文职责**：逆向结论、双 App 运行模型、设备坑、探针数据位置。  
> **不写工程排期**；阶段进度见 [`POST_MVP_PLAN.md`](../POST_MVP_PLAN.md)，架构决策见 [`DEVELOPMENT_PLAN.md`](../DEVELOPMENT_PLAN.md)。

---


## 1. 项目目标

### 1.1 产品定位

构建 **多平台内容下载能力**（优先番茄小说、红果短剧），支撑：

- 本机/服务端脚本验收与下载；
- 后续 **薄客户端 + 托管中继**（订阅制）：用户侧只拿客户端，会话与签名由服务端自养；
- 不依赖用户粘贴 Cookie 作为主路径（红果/番茄 App 路径）。

### 1.2 技术路线（已定方向）

| 平台 | 主路径 | 说明 |
|------|--------|------|
| **红果短剧** | App API + 签名 + 媒体解密 | 复用 `vendor/hongguo`（zhangbaio/hongguo 思路），已 E2E 验证 |
| **番茄小说** | **App API**（非 Web 主路径） | Web 仅作对照/部分免费章；正文走 `reader/full` 密文 + App 内解密 |
| 签名（红果） | `com.phoenix.read` + Frida / 签名后端 | 仅红果下载链路 |
| 签名（番茄 App） | **`com.dragon.read` 本进程** `NetworkParams.tryAddSecurityFactor` | **不依赖红果包** |
| 正文解密 | 番茄 `com.dragon.read` 进程内 native | 当前无法纯 Python 离线解 |

**明确不做/弱化：**

- 不以 **Web + Cookie + 字体 FONT_MAP** 作为番茄主下载通道（会员/锁章/Cookie 限制）；
- 不依赖用户手工贴 Cookie 的长期方案；
- 对比试验表明：前几章免费段 Web 可读，**全书仍不可靠**。

### 1.3 业务约束（需交接知悉）

- 内容版权与平台 ToS：批量抓取/分发有合规风险，产品边界需自控；
- 非公开接口存在 **风控、改签、改协议** 风险，不能当作永不动摇的基础设施。

---

## 2. 现在进度

> **工程侧**（鉴权/卡密/VIP/隔离/签名池/桌面商业闭环/质量门禁）已达 **`1.0.0`**，详见 `POST_MVP_PLAN.md`。  
> **本节只描述平台能力与设备运维现实**，不代表「产品功能未写完」。

### 2.1 总览

| 模块 | 进度 | 说明 |
|------|------|------|
| 工程脚手架 / 商业 V1.0 | ✅ 完成 | FastAPI、Job、鉴权、配额、签名池、桌面 UI、pytest/CQ |
| 红果下载 | **主路径可用** | 适配器 + E2E；实跑依赖 `vendor` 配置与签名环境 |
| 番茄 Web | 可用；产品上不作会员主路径 | `web_ssr.py` FONT_MAP；历史 5×10 章采样 |
| 番茄 App 拉密文 | **可用** | App API + 签名；见 `platforms/fanqie/client.py` |
| 番茄 App 解密 | **原理与链路已验证** | 进程内 `CryptManager.decrypt` → gzip → HTML |
| 番茄整书产品流水线 | **代码已接入** `FanqiePlatform.download(mode=app)` | 仅需番茄进程 + Frida；可与红果同机并行，会话 key 仍脆弱 |
| Web vs App 50 章对齐对比 | **研究项未收口** | Web 50 章齐；App 侧未按同集合自动采齐 |
| 薄客户端 UI | **商业闭环已接** | 登录/兑卡/VIP/Jobs；验收仍以脚本 E2E 为准 |

### 2.2 红果（短剧）

- 依赖：`vendor/hongguo`、`config.json`（设备/会话，**勿提交密钥到公开仓库**）、模拟器 + 签名代理；
- 能力：签名、剧集拉取、spade/CENC 等媒体解密路径已在项目前期打通；
- 参考：`docs/hongguo_reuse.md`、`server/platforms/hongguo/`。

### 2.3 番茄正文加密（核心结论）

```
GET /reading/reader/full/v
  → data.content          # base64 密文
  → CryptManager.decrypt(contentB64, keyB64, keyVersion)  # native，在番茄进程内
  → gzip 字节
  → gunzip
  → HTML 正文
```

| 项 | 结论 |
|----|------|
| Java 入口 | `com.dragon.read.crypt.CryptManager`：`native byte[] decrypt(String, String, int)` |
| 密钥 | `DecryptKey.f()` 给出约 **48 字节** key（非标准 AES 16/24/32） |
| 调用 version | 实测常用 **1001**；接口 JSON 的 `key_version`（如 1165016269）**不是同一字段** |
| 同会话 | 多章 **key 固定** |
| 跨重启 | **key 会变**；旧 key 解新会话密文会失败（非 gzip） |
| 离线标准 AES | **不可行**（已试 ECB/CBC/GCM 等） |
| 当前可行解密 | **Attach 番茄进程，直接调 native decrypt**（算法黑盒在 so） |

**测试策略（已对齐）：**

- 不强制持久化密钥；
- 每次完整：拉密文 + 进程内 decrypt（key 可从当次 hook 参数获得）；
- 人工点章仅用于 **验证**，批量应用 **API 自动拉章 + 进程内 decrypt**，不必每章手点。

### 2.4 设备运行模型（同机可双开）

| 业务 | 包名 | 签名 | 解密 / 媒体 |
|------|------|------|-------------|
| **红果短剧** | `com.phoenix.read` | attach 红果进程（或 SIGN_SERVER） | vendor 媒体解密 |
| **番茄 App** | `com.dragon.read` | attach **番茄**进程 `NetworkParams` | attach **番茄** `CryptManager.decrypt` |

原则：

- 番茄 App **不**再依赖红果签名 / `com.phoenix.read`。
- 同一模拟器可同时开两个 App；共用 **一个** Frida agent 端口，**按不同 pid attach**。
- 番茄代码路径 **禁止 pkill** 共用 agent，以免打断红果会话。
- agent 可用 `frida-server` 或伪装名 `sys_hlpd`；通信：`FRIDA_HOST=127.0.0.1:27042`，`ADB_DEVICE` 默认 MuMu `127.0.0.1:16384`。

批量下番茄小说时：**只需番茄进程存活**（可后台）。下红果时只需红果侧环境就绪。

### 2.5 采样与验证数据

| 数据 | 位置 | 数量/说明 |
|------|------|-----------|
| Web 5 书×前 10 章明文 | `tmp/fanqie_probe/compare_20260718_234644/web/` | **50 章** txt |
| App dump（较早） | `tmp/fanqie_probe/crypt_dump/device/` | 约 **41** 组密文/out.bin/html |
| App dump（点击验证） | `tmp/fanqie_probe/verify_live/` | 约 **70** 次 decrypt（含重复章） |
| 对比报告（完整相似度） | — | **未产出** 完整 50 章对齐报告 |
| 探针密文样例 | `tmp/fanqie_probe/full_resp.json`、`content_cipher.b64` | 早期 reader/full 样本 |

**书目（Web 采样用）：**

1. 十日终焉 — `7143038691944959011`  
2. 这个游戏不对劲，我挖矿成神！ — `7590221243043826712`  
3. 我在精神病院学斩神 — `6982529841564224526`  
4. 时停起手，邪神也得给我跪下！ — `7504849932138859545`  
5. 天眼风水师 — `7326876174989134910`  

### 2.6 关键代码与文档

| 路径 | 说明 |
|------|------|
| `server/platforms/fanqie/web_ssr.py` | Web SSR + FONT_MAP |
| `server/platforms/fanqie/platform.py` | 平台适配（下载仍偏 Web） |
| `server/platforms/fanqie/crypt_oracle.py` | 解密预言机 Python 封装 |
| `server/platforms/fanqie/app_content.py` | 密文 → HTML/纯文本 |
| `tools/setup/fanqie_crypt_oracle.js` / `_min.js` | 进程内 RPC：`decrypt` / `maxKeyVersion` |
| `tools/setup/hook_fanqie_dump.js` | 完整 dump decrypt 入参出参 |
| `tools/setup/compare_web_vs_app.py` | Web/App 对比脚本 |
| `tools/setup/test_fanqie_crypt_oracle.py` | dump 回归 + live 解密比对 |
| `docs/fanqie_app_content.md` | App 解密技术说明 |
| `docs/hongguo_reuse.md` | 红果复用说明 |
| `vendor/hongguo/config.json` | **敏感**：设备/会话，勿公开提交 |

### 2.7 环境要点

- OS：Windows；模拟器：MuMu（`adb` 常见路径 `D:\install\Netease\MuMu\nx_main\adb.exe`）；
- Python：`server/.venv`（3.14 系），agent 版本需与设备侧二进制一致（曾用 16.7.19）；
- 模拟器性能差时：白屏、进程 D 状态、attach/create_script **超时** 均出现过；
- 签名与解密 **可共用** 设备上同一 agent 监听端口，但 **attach 不同 pid**（番茄签+解都在 dragon；红果在 phoenix）。产品路径已避免 pkill 共用 agent。

---

## 3. 遗留问题

### 3.1 阻塞产品化的问题

| # | 问题 | 影响 | 建议优先级 |
|---|------|------|------------|
| P0 | **native 解密逻辑未逆向** | 无法纯本地解密，必须番茄进程 | 中长期 |
| P0 | **密钥生成/派生规则未知** | 无法离线稳定产 key；只能会话内现取 | 中长期 |
| P0 | **番茄 App 依赖设备侧稳定** | 会话 key 过期、attach 超时、双进程冲突仍会导致整书失败 | 短期运维 + POST_MVP 阶段 A |
| P1 | **Web×App 50 章自动对比未完成** | 缺「与 Web 同文」的量化报告 | 短期 |
| P1 | **Frida attach 与会话稳定性** | 模拟器卡顿、attach 超时；同机双 App 争用 CPU | 短期 |
| P1 | **拉章依赖签名会话** | config/设备过期则整链失败 | 持续 |
| P2 | 密钥是否按书/账号变化 | 仅验证「会话内固定、重启变」 | 可测 |
| P2 | 红果内是否可直接 decrypt | 未单独证明，当前以番茄为准 | 可选 |

### 3.2 概念澄清（交接易混点）

| 术语 | 含义 |
|------|------|
| **拉章** | 向服务器请求章节数据（得到密文 JSON） |
| **签名** | 为请求生成客户端校验头，使接口接受调用 |
| **解密** | 密文 → gzip → 明文；当前在番茄 native 中完成 |
| **本地解密** | 本机实现 key + 算法后，可不挂 App 解已有密文 |

**本地解密条件（仅解密环节）：**

1. 密钥如何生成/获取；  
2. native `decrypt` 等价实现。  

**完整自动下书另外还要：** 稳定拉章（通常仍要签名/会话）——内容源仍在平台侧时，风控与合规隐患不会因算法本地化而消失。

### 3.3 已知失败/坑

- 对比脚本中「先 attach 解密再拉章」若杀 agent，会导致红果 `pidof` 空 → `list index out of range`；
- 旧会话 key + 新密文 → `decrypt` 返回非 gzip；
- PowerShell 中 `$pid` / `$host` 为保留变量，脚本勿用；
- `create_script` 超时常见于 agent 僵死或多会话残留，需重启设备侧 agent；
- Web 公开仓库多为 FONT_MAP，**无** App `compress_status/key_version` 离线解法。

---

## 4. 后期规划

### 4.1 短期（设备 / 逆向侧）

> 工程主线已完成；以下为**设备侧与研究**建议：

1. **稳定自动批采（推荐）**  
   - 番茄存活 + 本进程签名/解密（无需红果）；  
   - 用已有 Web 的 50 个 `item_id` 自动 `reader/full` 拉密文；  
   - 对密文调用 `decrypt`（会话 key 现取或 hook 一次）；  
   - 与 Web 50 章算 `text_sim`，产出 `report.json`。  

2. **脚本硬化**  
   - 禁止 pkill 共用 agent；  
   - 单实例跑批；  
   - attach 失败可重启 agent 并重试（谨慎，勿影响同机红果）。  

3. **平台层运维**  
   - 已接入 `FanqiePlatform.download(mode="app")`；  
   - 持续关注：番茄 pid、代理端口、decrypt 探活、签名池节点健康。  

### 4.2 中期

1. 会话内 key 缓存（内存即可，失败再刷新）；  
2. 看门狗：App 与代理进程保活；  
3. 多书队列与限速，降低风控；  
4. 若红果 so 同样包含 `CryptManager`，评估 **单 App** 是否足够（减运维）。  

### 4.3 长期（真正本地解密）

1. **逆向** `CryptManager.decrypt` 所在 so，复现算法；  
2. **逆向** 密钥派生（`DecryptKey` / 服务端字段 / 设备因子）；  
3. 本机：`content + key + version → 明文`，解密侧脱离模拟器；  
4. 拉章若仍走官方接口，单独评估签名方案（自研/池化/合规源）。  

### 4.4 产品与合规

- 明确个人学习 vs 商业分发边界；  
- 控制频率与规模；  
- 不将「非公开接口爬全文」作为唯一不可替代核心，避免单点业务归零。  

---

## 5. 建议接手后的第一步

1. 读 `docs/fanqie_app_content.md` + 本文；  
2. 起 MuMu，确认红果 + 番茄可进首页；  
3. 跑 `tools/setup/test_fanqie_crypt_oracle.py` 或挂 `hook_fanqie_dump.js` 点 1 章，确认 decrypt 仍通；  
4. 再跑 `compare_web_vs_app.py --app-only --merge-web <web结果目录>` 完成 50 章对比；  
5. 通过后合并进 `FanqiePlatform`。  

---

## 6. 相关配置（环境变量）

| 变量 | 含义 | 示例 |
|------|------|------|
| `ADB` | adb 路径 | `D:\install\Netease\MuMu\nx_main\adb.exe` |
| `ADB_DEVICE` | 设备 | `127.0.0.1:16384` |
| `FRIDA_HOST` | 代理端口 | `127.0.0.1:27042` |
| `AGENT_BIN` | 伪装 agent 路径（可选） | `/data/local/tmp/sys_hlpd` |
| `FANQIE_COOKIE` | Web 可选 Cookie | 一般不作主路径 |
| `FANQIE_CONTENT_KEY` | 开发用临时 key | 易失效，勿当生产唯一方案 |

---

## 7. 一句话状态

> **工程 V1.0 已就绪。红果/番茄主链路代码已通；番茄 App 签名与解密均在 `com.dragon.read` 内完成，不依赖红果签名；离线算法与密钥派生未解；设备侧稳定性与 Web×App 50 章自动对齐仍是运维/研究债。**

---

*本文档随实现更新；敏感配置与密钥勿写入公开 git。*
