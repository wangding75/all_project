# BlackBox 集成笔记

- **上游 URL**：`https://github.com/FBlackBox/BlackBox.git`
- **commit / tag**：`f833752` (Merge pull request #119 from AmySama/patch-1, 基于 2.1.0 tag 的最新稳定修复点)
- **支持系统（声称 / 实测）**：声称支持 Android 5.0 ～ 12.0；实测重点覆盖 Android 10 和 Android 13 真机。
- **引入方式**：源码目录 (放在 `blackbox/` 目录下，解耦引入)
- **32/64 或插件位说明**：当前阶段使用主进程默认架构。如果宿主应用加载 64 位专有 App，需后续根据 BlackBox 官方建议引入 64 位插件位进程，一期仅做主架构适配。

## 与 SandboxEngine 方法映射表

| SandboxEngine 接口方法 | BlackBoxCore 对应 API / 实现细节 | 说明 |
| :--- | :--- | :--- |
| `initialize(Application app)` | 保存 Application Context 实例 | 基础初始化 |
| `onAttachBaseContext(Context base)` | `BlackBoxCore.get().doAttachBaseContext(base, clientConfiguration)` | 在 Application 初始化阶段挂载沙箱底层 |
| `onAppCreate()` | `BlackBoxCore.get().doCreate()` | 在 Application onCreate 阶段执行服务与 Binder 挂载 |
| `isReady()` | 返回 `mReady` 状态 (当 doAttachBaseContext 成功执行后置为 true) | 标识引擎是否就绪 |
| `installFromHost(String packageName)` | `BlackBoxCore.get().installPackageAsUser(packageName, 0)` | 从宿主导入应用到虚拟空间 (默认用户 0) |
| `installFromApk(String apkPath)` | 返回 `InstallResult(false, -1, "Not supported")` | 一期暂不支持直接从 APK 安装 |
| `uninstall(String packageName, int userId)` | 若 `userId == 0` 调用 `uninstallPackage(packageName)` 彻底卸载；否则调用 `uninstallPackageAsUser(packageName, userId)` 卸载分身 | 卸载逻辑 |
| `clearData(String packageName, int userId)` | `BlackBoxCore.get().clearPackage(packageName, userId)` | 清除沙箱分身数据 |
| `listInstalled()` | 遍历 `getUsers()` 获取所有已创建的虚拟用户，再通过 `BlackBoxCore.get().getInstalledPackages(0, userId)` 查询每个用户下的包，映射为 `SandboxAppInfo` | 列表查询 |
| `get(String packageName, int userId)` | 检索已安装列表，匹配 pkg 与 userId | 获取单分身详情 |
| `isInstalled(String packageName, int userId)` | `BlackBoxCore.get().isInstalled(packageName, userId)` | 判断分身是否已安装 |
| `launch(String packageName, int userId)` | `BlackBoxCore.get().launchApk(packageName, userId)` | 启动指定分身进入真实界面 |
| `kill(String packageName, int userId)` | `BlackBoxCore.get().stopPackage(packageName, userId)` | 强停指定分身进程 |
| `killAll()` | 遍历所有运行中的分身执行 `stopPackage` | 强停所有 |
| `clone(String packageName)` | 查找已有分身最大 userId，计算 `newUserId = maxUserId + 1`，调用 `BUserManager.get().createUser(newUserId)`，随后调用 `installPackageAsUser(packageName, newUserId)` | 多开克隆 |
| `createShortcut(Context context, String pkg, int userId)` | 使用 `ShortcutManager` (Android 8.0+) 固定快捷方式到桌面，指向 `ShortcutLaunchActivity`，并携带 package_name 和 user_id 额外参数 | 桌面快捷方式 |
| `setDisplayName(String pkg, int userId, String name)` | 使用本地 SharedPreferences 保存包名 and 用户 ID 对应的显示名称，在 `listInstalled()` 返回的 `SandboxAppInfo.label` 中做动态替换 | 重命名支持 |

## 已知问题与限制
1. **未实现 Phase 2 Hook**：本阶段只实现多开和基础运行闭环，不涉及任何定位、设备、网络、相机 Hook。
2. **多进程共享 SharedPreferences**：在 `setDisplayName` 和 list 列表缓存中，涉及多进程数据读写，必须保证持久化安全。
3. **Android 14/15 兼容性**：受限于上游 commit 库对系统 API 的适配深度，Android 14/15 上可能会存在虚拟化 Hook 注入失效，需要后续 Phase 适配。

## 兼容性与实测矩阵

| 运行设备/模拟器 | Android 系统版本 | 测试应用类型 | 运行结果 / 兼容性结论 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| Google Pixel 4a (真机) | Android 10 (API 29) | 系统计算器, 三方轻量 App | **通过** (启动/克隆/清除数据正常) | 稳定可靠 |
| Xiaomi 12 (真机) | Android 13 (API 33) | 基础应用, 部分第三方社交应用 | **通过** (分身数据独立隔离, 快捷方式启动正常) | 稳定可靠 |
| Pixel 7 (真机/模拟器) | Android 14 (API 34) | 任何三方应用 | **部分受限/不可用** (隐藏 API 调用在 Android 14 被拦截导致挂载崩溃) | 记录为已知兼容问题 |
| Emulator | Android 15 (API 35) | 任何三方应用 | **暂不支持** (系统进程启动机制发生变更导致沙箱子进程启动失败) | 记录为已知兼容问题 |
