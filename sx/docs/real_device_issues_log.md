# 真机运行问题记录 (Real Device Issues Log)

> **记录时间**：2026-07-24  
> **说明**：本文档用于详细记录当前在真机（Android 10~15 真实设备）环境下使用闪现沙箱应用时遇到的问题现象、技术原因初步诊断及后续修复规划。按用户要求，目前优先记录备案，暂不立即修复。

---

## 问题一：内置应用点击启动后无反应

### 1. 现象描述
* 在闪现 App 内选择启动系统内置应用（如系统自带应用、基础组件等）。
* 界面弹出 Toast 提示“正在启动...”，但之后无任何画面跳转或界面呈现，停留在原地。

### 2. 技术诊断与可能原因
* **进程创建与 Stack 关联**：系统内置应用在 Android 系统的 `ApplicationInfo` 中可能具有特殊的 System/Privileged 标志或 UID（如 system/root 关联），沙箱在对其进行虚拟化包安装和进程 Fork 时可能受到系统 SELinux Policy 或 `BProcessManagerService` 限制。
* **Activity 栈调度**：`BActivityManagerService` 跨进程拉起 `ProxyActivity` 时，系统可能因为 UID/Permission 不匹配阻断了组件启动。

---

## 问题二：夸克浏览器点击启动后无反应

### 3. 现象描述
* 在闪现 App 内选择启动夸克浏览器（Quark Browser）。
* 界面弹出 Toast 提示“正在启动...”，随后没有弹出夸克浏览器的主界面，应用未响应。

### 4. 技术诊断与可能原因
* **Split APKs / 动态模块安装**：夸克浏览器等大型应用在真机安装时通常为 App Bundle (Split APKs)，除了 `base.apk` 之外还有 `split_config.arm64_v8a.apk` 等多 APK 结构。目前 `installFromHost` 默认仅复制了 `base.apk` 的 `sourceDir`，导致缺少 Native 库或 splits 资源。
* **Native 进程初始化崩溃**：夸克浏览器依赖多进程 UC 网页渲染内核（`libwebviewuc.so` / `u4proc`），在真机未分配完整隔离沙箱目录或沙箱 Native 进程拦截未完成时可能静默崩溃退出。

---

## 问题三：谷歌浏览器启动失败（报错“未能在沙箱安装或缺乏包访问权限”）

### 5. 现象描述
* 在闪现 App 内点击启动谷歌浏览器（Chrome Browser）。
* 界面弹出 Toast 报错提示：“启动失败：未能在沙箱安装或缺乏包访问权限”。

### 6. 技术诊断与可能原因
* **Android 11+ 包可见性限制 (`QUERY_ALL_PACKAGES`)**：Android 11 (API 30+) 及更高版本的真机系统（如华为/小米/vivo/oppo/三星）对第三方应用读取其他已安装应用列表进行了限制。如果未授予真机权限或系统应用未包含在 package query 列表中，`PackageManager.getPackageInfo("com.android.chrome")` 会直接返回 `NameNotFoundException`。
* **多用户分身安装**：谷歌浏览器在宿主系统可能以 Chrome Custom Tabs 存续，在虚拟 `UserId > 0` 尝试 `installPackageAsUser` 时缺乏有效 `sourceDir` 路径。

---

## 后续处理规划 (Roadmap)

| 序号 | 问题项 | 关键定位模块 | 规划修复动作 |
| :--- | :--- | :--- | :--- |
| 1 | 内置应用启动无反应 | `BProcessManagerService`, `ActivityStack` | 排查内置/系统应用特权标志处理与 ProxyActivity 调度 |
| 2 | 夸克浏览器启动无反应 | `BPackageManagerService`, `IOCore` | 支持 Split APKs 全量复制与多进程 UC 内核沙箱隔离 |
| 3 | 谷歌浏览器包访问失败 | `BlackBoxCore.java`, `AndroidManifest.xml` | 优化 Android 11+ 真机包可见性获取机制及提示 |
