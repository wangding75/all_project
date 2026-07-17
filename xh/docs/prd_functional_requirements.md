# 基于星盒 (XH) 的虚拟沙箱 App 产品需求文档 (PRD)

本页总结了复刻或二开类似于“星盒”App 的核心功能需求清单（Product Requirements Document），分为 6 大核心模块。

---

## 1. 核心多开沙箱管理模块 (Core Sandbox Container)

该模块负责构建一个独立的“虚拟 Android 系统环境”，供目标应用（分身）运行。

* **F-1.1 应用双开与导入**：用户可以从系统已安装的 App 列表中选择任意应用（如微信、考勤App），导入并安装在沙箱内。
* **F-1.2 独立隔离存储**：
  * 重定向沙箱内 App 的数据读写目录（如 `/data/data/com.xin.h6/virtual/data/user/0/[目标包名]/`）。
  * 实现分身应用与外部物理系统的文件、数据库完全隔离，防止数据污染。
* **F-1.3 多实例管理 (Multi-Instance)**：支持同一个目标 App 导入多个副本（如多开 3 个不同的微信），各个实例数据相互独立。
* **F-1.4 桌面快捷方式生成**：允许用户将沙箱内部的某个应用快捷方式直接创建在物理手机桌面上，点击可直接唤起沙箱内特定实例。

---

## 2. 虚拟定位注入模块 (Virtual Geolocation)

在沙箱中接管并伪造 GPS、网络基站及第三方地图定位数据。

* **F-2.1 地图可视化选点**：
  * 集成百度地图/高德地图 SDK，提供直观的地图选点界面。
  * 支持输入具体地址进行全国范围搜索并精确定位。
* **F-2.2 多模式定位注入**：
  * 拦截系统的 `ILocationManager` 服务，对目标 App 强制喂入虚假的 `Location` 数据。
  * 包含经纬度（Latitude/Longitude）、海拔高度（Altitude）、精度误差（Accuracy）等全套数据指标。
* **F-2.3 高频高精定时更新**：
  * 启动后台前台服务（Foreground Service），建立 50ms 循环定时器。
  * 自动匹配并更新 `ElapsedRealtimeNanos`（开机相对纳秒），防止位置信息因时间戳未更新被目标 App 判定为静止或模拟。
* **F-2.4 轨迹/速度模拟**：支持设置起点和终点，模拟步行、骑行或驾车状态下的轨迹移动。
* **F-2.5 屏蔽模拟位置检测 (Anti-Mock Detection)**：
  * 彻底拦截目标 App 对 `isFromMockProvider()` 的查询，使其恒返回 `false`。
  * 隐藏物理手机开发者选项中“选择模拟位置应用”的标志，防止被钉钉、企业微信等 App 检测到使用了 MockLocation API。

---

## 3. 虚拟相机流替换模块 (Virtual Camera)

拦截系统的摄像头数据流，用本地多媒体资源进行静默替换。

* **F-3.1 视频源与图片源导入**：支持用户选择手机本地相册中的视频文件（MP4/H.264）或图片文件，作为替换源。
* **F-3.2 相机 API 劫持 (Camera/Camera2 Hook)**：
  * 劫持 `android.hardware.Camera` 与 `android.hardware.camera2.CameraDevice` 核心方法。
  * 拦截分身 App 对 `startPreview()` 和 `setRepeatingRequest()` 的调用。
* **F-3.3 媒体帧实时转码 (Decoders)**：
  * 启动本地异步解码引擎，将 MP4 视频解码为 `NV21` / `YUV420p` 的像素字节数组（Byte Array）。
* **F-3.4 图像表面映射 (OpenGL Render)**：
  * 将解码后的视频帧实时绘制到目标 App 提供的 `Surface` 或 `SurfaceTexture` 预览组件上。
  * 适配不同的相机分辨率，实现自动裁剪与缩放，防止虚假视频在目标 App 预览框内拉伸变形。

---

## 4. 手机设备参数伪装模块 (Device Spoofing)

为分身应用伪造一套全新的“手机硬件指纹”，用于规避应用多开风控。

* **F-4.1 设备核心 ID 伪装**：
  * 拦截 `TelephonyManager.getDeviceId()`、`getImei()`、`getMeid()`，返回虚假生成的 IMEI 码。
  * 拦截 `Settings.Secure.getString(..., ANDROID_ID)`，返回随机生成的 16 位十六进制 Android ID。
* **F-4.2 系统硬件参数修改**：
  * Hook 并反射修改 `android.os.Build` 内的静态字段。
  * 支持自定义修改：手机品牌（`BRAND`）、型号（`MODEL`）、主板（`BOARD`）、制造商（`MANUFACTURER`）、硬件序列号（`SERIAL`）。
* **F-4.3 SIM 卡及运营商伪装**：
  * 拦截返回虚假的电话号码（`Line1Number`）、SIM卡序列号（`SimSerialNumber` / ICCID）、IMSI（`SubscriberId`）以及运营商名称。

---

## 5. 网络/基站环境伪装模块 (Network Spoofing)

防止 App 通过收集周边的网路环境和蓝牙设备来辅助判定物理位置和设备真实性。

* **F-5.1 正在连接的 WiFi 伪装**：
  * Hook `WifiManager.getConnectionInfo()`，替换返回的 `WifiInfo`。
  * 伪造当前连接路由器的名字（SSID）和 MAC 物理地址（BSSID）。
* **F-5.2 WiFi 扫描列表伪造 (WiFi Scan List)**：
  * Hook `WifiManager.getScanResults()`。
  * 返回虚构的周边路由器列表，防止 App 通过 WiFi 空间交叉定位发现用户的真实位置。
* **F-5.3 基站定位模拟 (Cell Tower)**：
  * 拦截 `TelephonyManager.getAllCellInfo()` 和基站监听器。
  * 返回虚假的基站标识（MCC、MNC、LAC、CID），防止 App 越过 GPS 强行使用基站定位。

---

## 6. 用户授权与防逆向模块 (Security & Licensing)

保护 App 商业化收益及代码安全。

* **F-6.1 卡密激活验证 (Licensing)**：
  * 界面提供卡密输入框，支持卡密与设备 ID 在服务器端的绑定授权。
* **F-6.2 离线到期校验**：
  * 客户端解密并验签服务器下发的 ExpireTime Token（如 JWT 签名），校验本地有效期（如 3 个月）。
* **F-6.3 网络授时防时钟回拨 (Anti-Cheating)**：
  * 不使用系统本地时间，通过网络请求（如请求知名大厂的 HTTP Date 响应头）获取标准网络时间用于到期对比。
  * 比较本地数据库文件的最后修改时间，检测用户是否将手机时钟往回拨。
* **F-6.4 代码防逆向保护 (VMP 加固)**：
  * 核心的卡密校验、签名算法、以及相机/定位 Hook 核心逻辑必须采用 **Dex2C 编译或 VMP（Java 字节码翻译为 JNI C++ 机器码）** 进行加固，防止被逆向者通过简单的 Xposed 模块一键破解。
