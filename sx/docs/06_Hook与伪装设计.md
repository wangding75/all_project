# Hook 与环境伪装设计

## 1. 总则

- **作用范围**：默认仅虚拟分身进程；配置来自 `ProfileRepository.resolve`  
- **开关**：各子模块 `enabled` 为 false 时不 Hook 或透传真值  
- **对齐 xh**：行为结果对齐，不绑定其类名  

---

## 2. 虚拟定位

### 2.1 目标行为（xh FackLocService + Hook）

| 项 | 规格 |
|----|------|
| 坐标 | lat/lng/altitude/accuracy 可配 |
| 周期 | 默认 50ms 级更新（可配置） |
| 时间 | `setTime(System.currentTimeMillis)` + `setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos())` |
| 反检测 | `Location.isFromMockProvider` → false；隐藏 mock 标志（API 31+ `isMock` 等按版本处理） |
| 微漂移 | 可选：在坐标上加亚米级噪声，模拟 GPS 抖动 |

### 2.2 Hook 点（建议）

| API | 策略 |
|-----|------|
| `Location.getLatitude/Longitude/Altitude/Accuracy` | after 改结果或替换 Location 对象 |
| `Location.isFromMockProvider` / `isMock` | 返回 false |
| `LocationManager.getLastKnownLocation` | 返回构造的假 Location |
| `LocationManager.requestLocationUpdates*` | 包装 listener，回调假位置 |
| 第三方地图定位 SDK | 二期按需（腾讯/高德/百度） |

### 2.3 辅助通道

`MockLocationService` 前台服务 + TestProvider：用于调试或对未进沙箱场景；沙箱主路径不依赖开发者选项。

---

## 3. 设备指纹

### 3.1 字段表

| 配置项 | Hook / 修改目标 |
|--------|-----------------|
| brand | `Build.BRAND` |
| model | `Build.MODEL` |
| manufacturer | `Build.MANUFACTURER` |
| board | `Build.BOARD` |
| serial | `Build.SERIAL` / `getSerial` |
| imei | `TelephonyManager.getDeviceId/getImei` |
| meid | `getMeid` |
| androidId | `Settings.Secure.getString(ANDROID_ID)` |
| phone | `getLine1Number` |
| imsi | `getSubscriberId` |
| iccid | `getSimSerialNumber` |
| operator | `getNetworkOperatorName` / `getSimOperatorName` |

### 3.2 生成算法

- IMEI：Luhn 校验（对齐 xh 还原逻辑）  
- Android ID：16 位 hex  
- 品牌型号：内置机型表随机  

### 3.3 Build 字段

final 字段需 **Hook getter 反射路径** 或引擎提供的 Build 欺骗能力；纯 Java 改 static final 不可靠。

---

## 4. 网络与基站

| 配置 | Hook 目标 |
|------|-----------|
| ssid | `WifiInfo.getSSID`（注意带引号格式） |
| bssid | `WifiInfo.getBSSID` |
| mac | `WifiInfo.getMacAddress` / `NetworkInterface`（视范围） |
| scanList | `WifiManager.getScanResults` 返回构造 `ScanResult` 列表 |
| mcc/mnc/lac/cid | `TelephonyManager.getAllCellInfo` / `getCellLocation` 等 |

**策略：** 开启伪装时优先返回伪造列表，避免 App 用真实周边 WiFi/基站纠偏 GPS。

---

## 5. 虚拟相机

### 5.1 流水线

```
媒体文件(MP4/JPEG)
    → 解码器(MediaCodec / Bitmap)
    → 帧队列 NV21/YUV 或 GL 纹理
    → Hook Camera 预览输出
    → 写入目标 Surface / byte[] callback
```

### 5.2 Hook 范围

| API 族 | 切入点（示意） |
|--------|----------------|
| Camera1 | `setPreviewTexture` / `setPreviewDisplay` / `startPreview` / `takePicture` |
| Camera2 | `CameraDevice.createCaptureSession` / `setRepeatingRequest`；ImageReader 路径 |

### 5.3 一期 / 二期

| 阶段 | 范围 |
|------|------|
| 一期 | 图片静态帧 + Camera1 或 Camera2 单路径预览替换 |
| 二期 | MP4 循环、双 API、分辨率自适应裁剪 |

---

## 6. 配置热更新

| 模式 | 行为 |
|------|------|
| 冷启动 | 必加载最新 Profile |
| 热更新 | 发送包内、签名权限保护的广播；接收端清理 Profile 缓存并通过监听器重新加载当前 `packageName + userId` 配置，各 Hook 更新静态配置引用；失败则提示重启分身 |

---

## 7. 日志与调试

- Tag：`SX-Spoof`  
- Debug 包打印：pkg、userId、各模块 enabled、坐标摘要  
- Release：默认关闭敏感字段日志  

---

## 8. 测试矩阵（最小）

| 用例 | 期望 |
|------|------|
| 分身开定位，读 GPS | 与配置一致且时间在变 |
| isFromMockProvider | false |
| 改 IMEI/AndroidId | 分身内 Settings/反射可见 |
| 开 WiFi 伪装 | SSID/BSSID 为配置值 |
| 关总开关 | 恢复真实（或引擎默认） |
| 独立设置覆盖全局 | 仅该分身使用独立坐标 |

测试 App 可用自写 `SpoofProbe` 小工具读取上述 API。
