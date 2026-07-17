# 星盒 (xh.apk) 脱壳反编译与安全分析项目交接文档

## 一、 项目概述与当前状态
* **项目目标**：对具有 360 加固保护的星盒 App（`com.xin.h6`）进行脱壳、反编译，提取纯净的业务逻辑源码，还原混淆的字符串，并分析其定位/相机模拟机制与加固防线。
* **当前状态**：**阶段性大捷，核心技术瓶颈已完全突破。** 
  * 成功绕过 360 壳的模拟器闪退防御。
  * 成功通过内存 Dump 导出解密后的 58 个原始 DEX 文件。
  * 成功完成 JADX 绕过校验反编译，提取出纯净的自定义业务代码（`src_clean`）。
  * 成功实现了**作用域感知的全局字符串解密**，全盘还原了代码中混淆的数据流。
  * 对定位模拟核心文件 `FackLocService.java` 完成了可读变量重构。

---

## 二、 逆向技术路径与关键操作记录

### 1. 动态脱壳阶段 (Unpacking)
* **运行环境**：**MuMu 模拟器 12**（内置的 ARM 翻译层兼容性最强，能稳定运行 360 加壳 of ARM 底层代码，避免了其他模拟器的闪退崩溃）。
* **Frida 注入**：由于加固修改了进程名（变为中文乱码），无法通过包名注入。最终在模拟器上运行 `frida-server`（监听端口 `29999`），并通过查询动态 PID（如 `2654`）进行 PID 注入：
  ```powershell
  python -m frida_dexdump -H 127.0.0.1:29999 -p 2654 -d
  ```
  该操作成功从运行内存中导出了 58 个解密的 DEX 文件。

### 2. 绕过校验反编译阶段 (Decompilation)
* **文件排除**：`classes02.dex` 存在 360 加固故意损毁的偏移指针（`newPosition > limit` 异常导致 JADX 闪退）。在反编译入参中将该损坏段剔除。
* **绕过 Checksum 校验**：JADX 默认会拒绝反编译头部校验不通过的内存 Dump DEX。在 `04_decompile.ps1` 中加入指令关闭校验，成功强行反编译：
  ```powershell
  -Pdex-input.verify-checksum=no
  ```

---

## 三、 成果文件与代码地图 (Assets & Mappings)

### 1. 工作目录结构
* **脱壳 DEX 存放点**：`D:\github\xh\blackdex_out\`
* **原始反编译输出**（含 10,000+ 第三方库噪声）：`D:\github\xh\unpack_out\`
* **精简纯净的业务源码**（你的主要审计目录）：📁 **`D:\github\xh\src_clean\`**

### 2. 纯净源码分布 (`src_clean\sources\`)
* [App.java](file:///D:/github/xh/src_clean/sources/com/loc/va/App.java) (App 程序入口)
* `com/loc/va/ui/activity/` (界面 UI 控制器)
* [FackLocService.java](file:///D:/github/xh/src_clean/sources/com/loc/va/service/FackLocService.java) (虚拟定位核心服务)
* [MyUtil.java](file:///D:/github/xh/src_clean/sources/com/loc/va/utils/MyUtil.java) (AES 加解密与设备参数读取工具)

---

## 四、 自动化反混淆与重构技术 (Deobfuscation)

在 `src_clean` 中，我们发现了大量的混淆字符串 `$(start, end, key)`，以及内部类变量冲突。为此我们通过两轮脚本重构了代码：

### 1. 全局作用域感知解密
* **脚本文件**：`C:\...\scratch\deobfuscate_classes.py`
* **原理**：利用大括号 `{}` 划分嵌套的作用域，自下而上（Back-to-front）处理内部类。解析每个类的 `short[] $` 静态密文数组。
* **高维参数求解**：内置了 Android SDK 和 IjkPlayer 的常量表，并结合“连续 printable 字符”规则，对缺失参数和变量引用的加密 Key 进行爆破。
* **效果**：将代码中所有的 `$(...)` 全部原地替换为逆向得出的明文字符串常量（如 `"gps"`、`"network"`、`"addTestProvider[GPS_PROVIDER] success"`），并自动剥离了密文数组以精简代码。

### 2. 变量重构 (以 `FackLocService.java` 为例)
* **脚本文件**：`C:\...\scratch\rename_fackloc.py`
* **原理**：将无意义的混淆属性变量进行全局安全替换，避开系统标准的 `Log.d/i/e`。
* **变量还原状态**：
  * `f22699f` $\rightarrow$ `mLocationManager` (位置管理器)
  * `f22694a` $\rightarrow$ `TAG` (日志标签 "FackLocService")
  * `f22698e` $\rightarrow$ `mLatLng` (选点坐标)
  * `f22693i` $\rightarrow$ `isSimulating` (定位开关)

---

## 五、 核心业务逻辑深度审计

### 1. 沙箱多开机制
星盒本质上是一个定制版的 **VirtualApp (VA) 沙箱**，底层使用了 `libvv.so` 作为虚拟化引擎，使用 `libpine.so` 作为虚拟机 Hook 框架。

### 2. 虚拟定位原理
在后台定时器（50ms 循环）中，通过 `mLocationManager` 的 `addTestProvider` 注册虚拟的 `"gps"` 和 `"network"`，高频调用 `setTestProviderLocation` 往系统里注入伪造的 `Location` 数据。

### 3. VMP（虚拟机方法抽取）的影响
* 360 对该 App 采取了**“保 UI 和入口，放行后台服务”**的收费版 VMP 保护。
* 欢迎界面 `SplashActivity`、卡密激活 `ActiveCardActivity` 以及相机劫持的实际运行类 `VirtualCameraActivity.a()` 的方法实现都被抽取为了 `native` 方法，逻辑写死在底层 `.so` 中。
* **激活校验拦截判定**：星盒的卡密激活（`ActiveCardActivity`）仅是一个“本地开关”，其多开、定位、相机逻辑全在本地离线运行。通过 Hook 本地激活状态（如 Hook 持久化配置 `getConfig` 返回激活状态）可以完美绕过，不影响后台数据注入。

---

## 六、 下一步调试与逆向指南

1. **对于个人本地调试**：
   参考已在第二步编译生成或记录的 LSPosed 模块脚手架，直接 Hook 目标 App 的 `Location`、`TelephonyManager`（IMEI）以及 `WifiInfo`，开发出轻量级的自定义虚拟插件。
2. **针对 VMP 屏蔽的 Native 函数（如虚拟相机拦截）**：
   * **动态调试法**：在运行状态下，使用 Frida 脚本 Hook `VirtualCameraActivity.a(InputStream, OutputStream)` 的入参，直接在内存中拦截并 Dump 正在被读取的 MP4 数据流，以此反推其解码流程。
   * **静态脱壳法**：使用 `SoFixer` 修复运行时从内存 Dump 出来的 `libjiagu.so` 或 `libvv.so`，利用 IDA Pro 查找 `JNI_OnLoad` 下的 `RegisterNatives` 动态注册表，定位 Native 函数在内存中的真实偏移，反编译审计底层 C++ 劫持细节。
