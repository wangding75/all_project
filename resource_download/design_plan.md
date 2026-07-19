# 多平台内容下载器 — 早期设计文稿（历史存档）

> **⚠️ 本文档已部分过时（存档保留），请勿以此指导当前开发。**
>
> - **权威开发计划**：[`DEVELOPMENT_PLAN.md`](./DEVELOPMENT_PLAN.md)（已定稿）
> - **执行开发计划**：[`DEV_ROADMAP.md`](./DEV_ROADMAP.md)（最新，按此开发）
>
> **本文各节状态：**
> - §一「UI 规范」— 可参考，尚未过时
> - §二「架构选型」— **⛔ 已废弃**，早期本机一体化方案已被 HTTP 中转服务端取代
> - §三「文件结构」— **⛔ 已废弃**，与当前仓库结构不符
> - §四「红果解密」— **⚠️ 已更新**，当前复用 `vendor/hongguo`，需 Frida 签名后端，非纯离线
> - §五「番茄方案」— 可参考，Web SSR 链路已落地

本项目旨在开发一个扩展性强、视觉精美的桌面端内容下载器，集成番茄小说和红果短剧下载功能，并提供插件化架构支持未来扩展。

---

## 一、UI 与交互设计规范

客户端将复刻 `Fanqie-novel-Downloader` 的精美深色系 UI。

### 1.1 视觉系统 (CSS 变量)
```css
:root {
  --bg-primary:    #151f1b;   /* 深绿黑主背景 */
  --bg-card:       #1e2c27;   /* 半透明玻璃态卡片背景 */
  --bg-card-hover: #243630;   /* 卡片悬浮状态 */
  --accent:        #F5611A;   /* 主题橙色（番茄橙），用于按钮、激活项 */
  --text-primary:  #e8f0eb;   /* 主文本颜色 */
  --text-muted:    #8aa49a;   /* 次要/描述文本颜色 */
  --border:        #2d4038;   /* 细边框颜色 */
  --radius-lg:     12px;      /* 圆角大小 */
}
```

### 1.2 页面布局与导航
- **无边框窗口**：提供自定义的顶部标题栏，包含应用名称、最小化/关闭按钮以及平台切换器（番茄小说 / 红果短剧）。
- **Tab 导航栏**：搜索 🔍、书架 📚、历史 🕐、设置 ⚙、下载队列 ⬇（右上角角标实时显示进行中的任务数）。

---

## 二、架构选型（⛔ 已废弃 — 仅作历史参考）

> **⛔ 以下为早期「本机一体化」方案，已被 HTTP 中转服务端架构取代。**
> 当前实际架构：前端 UI（或脚本）→ HTTP API（FastAPI 服务端）→ 平台插件（hongguo / fanqie）。

> **⚠️ 以下目录结构为早期设计稿，与当前仓库实际结构不符，请以 README.md 为准。**

当前实际结构：

```text
resource_download/
├── server/             # 中转服务端（FastAPI）← 主战场
│   ├── app/            # API / 鉴权 / 任务队列
│   ├── platforms/      # hongguo（主路径）+ fanqie
│   └── run.py
├── vendor/hongguo/     # 上游 clone（勿提交 config.json）
├── scripts/            # e2e_hongguo / e2e_fanqie / smoke
├── client/             # 暂空，阶段 5 再建
└── data/               # jobs / outputs（.gitignore）
```

---

## 四、红果短剧 — 下载与解密核心机制（⚠️ 已更新）

> **⚠️ 当前实现复用 `vendor/hongguo`（zhangbaio/hongguo），需要 Frida 签名后端，非纯离线。**
> 下方「纯离线」描述为早期版本，spade_a 算法已内置于 vendor 中，无需单独实现。

**当前实际链路（vendor/hongguo 复用）：**

```text
FastAPI → platforms/hongguo/bridge.py → vendor/hongguo/hongguo.py
                                              ↓
                                    Frida 签名后端（MuMu/Redroid）
                                              ↓
                                    解密 MP4 → data/outputs/
```

**历史参考：早期设计的纯离线链路**

~~参考 `zhangbaio/hongguo` 的逆向成果，红果短剧的解密与下载完全采用**纯离线、无需 App、无需 Frida 运行**的纯算法流程。~~

## 四、红果短剧 — 下载与解密核心机制

参考 `zhangbaio/hongguo` 的逆向成果，红果短剧的解密与下载完全采用**纯离线、无需 App、无需 Frida 运行**的纯算法流程。

```
                    【红果短剧全离线解密链路】
                    
  1. API 接口获取明文直链 & spade_a 包装密钥
     video_model.video_list[]
        ├── main_url (CDN 密文 mp4 直链)
        └── encrypt_info.spade_a (37B Base64 密钥盒)
        
  2. 离线算 Key (spade_decrypt.py)
     spade_a ──(Base64解码)──► 37B 字节 ──(unwrap_v1 字节变换)──► 16B Content Key
     
  3. 提取 IV 偏移 (video.py)
     GET main_url ──► 下载密文 mp4 ──► 解析 senc 盒 ──► 提取首样本的 base_iv (8B)
     
  4. 离线解密合成 (video.py)
     AES-128-CTR 逐样本解密 (K=Content Key, IV=((base_iv + 样本序号) << 64))
        └── 解密视频轨 & 音频轨 ──► 明文临时 mp4
        
  5. 剥离 CENC (remux_playable)
     利用 ffmpeg 进行重封装: -c copy -tag:v hvc1 ──► 可播放的标准 MP4 ✓
```

### 4.1 spade_a ➜ Content Key 纯算法解密 (`spade_decrypt.py`)
该算法是从 `libttmplayer.so` 的 `FUN_001c4550` 逆向复现的纯字节变换，不涉及外部 KEK 和 AES 运算：
```python
def popcount(x):
    return bin(x & 0xffffffff).count("1")

def s8(v):
    v &= 0xff
    return v - 256 if v >= 128 else v

def unwrap_spade_v1(spade_bytes, flag=0):
    L = len(spade_bytes)
    if L < 3: return None
    bVar5 = spade_bytes[0] ^ spade_bytes[1] ^ spade_bytes[2]
    iVar9 = bVar5 - 0x30
    if iVar9 < 1: return None
    uVar1 = (L - bVar5) + 0x2f
    if uVar1 < 1 or 1 + uVar1 > L: return None
    
    dest = bytearray(spade_bytes[1:1 + uVar1])
    b14, b16 = 0x55, 0xfa
    for i in range(uVar1):
        b6 = dest[i]
        u18 = popcount(i)
        b3, b7 = b6, b14
        if i & 1:
            b3, b7, b16 = b16, b6, b14
        cVar4 = (u18 + 0x15) if flag else s8(-0x15 - u18)
        dest[i] = (cVar4 + (b16 ^ b6)) & 0xff
        b14, b16 = b7, b3

    b0 = dest[0]
    if 0x30 <= b0 <= 0x39: u11 = b0 - 0x30
    elif 0x61 <= b0 <= 0x7a: u11 = b0 - 0x57
    else: return None
    
    iv9 = uVar1 - (u11 & 0xff)
    if iv9 < 2: return None
    return bytes(dest[1:iv9]).decode("latin1", "replace") # 返回 32位 Hex 密钥
```

### 4.2 音视频多轨解密与重封装 (`video.py`)
1. **IV 提取**：读取密文 mp4 字节流，通过正则定位 `senc` 盒，在其偏移后提取首样本的 `base_iv` (高8字节)。
2. **AES-CTR 运算**：使用标准 `cryptography` 或 `pycryptodome` 库。每一帧/样本的 `IV = (base_iv + sample_index) << 64`。
3. **ffmpeg 重封装**：由于密文内部包含 `encv` 等 CENC 盒信令，常规严格播放器在解密后仍可能报错。通过 `ffmpeg -i temp_dec.mp4 -c copy -tag:v hvc1 output.mp4` 进行重封装，剥离 CENC 信令以获得完美兼容的 MP4 视频。

---

## 五、番茄小说 — 方案设计
番茄小说分为两条支线：
- **支线 A：Web SSR 方案（成熟稳定）**
  直接发起带有 Cookie 的网页请求，提取网页中的 `__INITIAL_STATE__`。章节内容中混淆 of PUA 乱码文字通过下载对应 CSS 内的 `.woff2` 字体，解析其 cmap 映射表，并将 Glyphs 对应到静态 FONT_MAP 还原为明文。
- **支线 B：官方 API 方案（极致性能）**
  使用注册的设备 ID，构造带有 `X-Argus` 和 `X-Ladon` 请求头的请求。API 返回的章节数据为 Protobuf 二进制，首先进行 Protobuf 解析，然后使用协商出的内容密钥进行 AES-256-CBC 离线解密，并结合 Gzip 解压得到明文。

---

## 六、多平台插件化扩展性

在 `core/base_platform.py` 中定义标准抽象类：
```python
class BasePlatform(ABC):
    @abstractmethod
    async def search(self, query: str, **kwargs) -> list[dict]:
        """统一搜索接口，返回包含 id, title, cover, desc, extra 的列表"""

    @abstractmethod
    async def get_detail(self, item_id: str) -> dict:
        """获取详情，包括元数据、目录（章节/集数）"""

    @abstractmethod
    async def download_segment(self, item_id: str, segment_id: str, output_dir: str, **kwargs) -> str:
        """下载与解密单段内容（小说单章或视频单集），返回本地文件路径"""
```

新增任何新平台（例如：起点中文网、Bilibili等），仅需在 `platforms/` 新建文件夹实现此接口，并在启动时动态装载即可，无需改动核心下载器逻辑与前端结构。

---

## 七、开发步骤与排期

1. **第一阶段：应用外壳与 UI 基础 (2天)**
   - 初始化 PyWebView、asyncio 循环与 WebSocket 骨架。
   - 编写 `frontend/`，完成精美的深色卡片式两栏下载器 UI。
2. **第二阶段：番茄 Web SSR + 导出器 (2天)**
   - 接入番茄 Web 爬取、WOFF2 字体解析还原逻辑。
   - 实现 TXT 与 EPUB (含封面、排版) 格式导出。
3. **第三阶段：红果短剧（基于 zhangbaio/hongguo） (3天)**
   - 实现 `spade_decrypt.py` 的离线密钥算解。
   - 实现 senc IV 解析与 AES-128-CTR 全轨（音+视）解密。
   - 编写 ffmpeg 整合与重封装逻辑。
   - 完成红果短剧列表接口浏览（分类、最新上架、榜单）。
4. **第四阶段：官方接口签名攻坚与打包 (持续)**
   - 调试与接入字节系接口签名（Argus/Ladon）的 fallback 策略（可配合模拟器 RPC 或算法还原）。
   - PyInstaller 打包为单 EXE 桌面程序。
