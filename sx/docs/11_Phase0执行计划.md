# 闪现 (sx) Phase 0 — 执行计划（修正版 · 可直接执行）

| 项 | 内容 |
|----|------|
| 文档版本 | v1.0 修正执行版 |
| 状态 | **批准执行** |
| 对应里程碑 | M1 UI Demo |
| 对应 Backlog | Epic B（B-01～B-17） |
| 入口文档 | 先读 `09_开发者交接与开工指南.md` |
| 本计划效力 | **实现以本文为准**；与旧 Implementation Plan 冲突时以本文为准 |

---

## 0. 范围与禁区（先读再写代码）

### 0.1 交付目标

可安装 **Debug APK**，具备：

- 启动与授权（开发卡密）
- 底部三 Tab 导航
- 首页模块入口
- **FakeSandboxEngine** 驱动的应用增删克隆（持久化）
- 定位 / 设备 / 网络 / 相机配置页 + **私有 SP 持久化**
- 桌面快捷方式 **stub**（可选成功 pin，失败 Toast）

### 0.2 明确不做（违反即超 scope）

| 禁止项 |
|--------|
| BlackBox / 任何真实沙箱引擎接入 |
| Xposed/LSPosed Hook、设备/定位/WiFi 真实伪装 |
| `MockLocationService` 真注入（TestProvider / 50ms 循环） |
| 地图 SDK |
| 代码加固 / 商业 VA 源码 |
| `SharedPreferences.MODE_WORLD_READABLE`（Phase 0 禁用） |

### 0.3 开发卡密

- 格式：`SX-DEV-YYYYMMDD`
- 验收示例：`SX-DEV-20991231`
- 密钥：使用现有 `BuildConfig.LICENSE_HMAC_SECRET`（勿另造一套）

---

## 1. 包名与 Manifest 对齐（必须一字不差）

全部新建类使用下列 FQCN（与 `AndroidManifest.xml` 一致）：

| 类 | FQCN |
|----|------|
| Application | `com.sx.app.SxApp` |
| Splash | `com.sx.app.ui.SplashActivity` |
| Main | `com.sx.app.ui.MainActivity` |
| License | `com.sx.app.ui.LicenseActivity` |
| 定位设置 | `com.sx.app.ui.location.LocationSettingsActivity` |
| 地点选择 | `com.sx.app.ui.location.LocationPickerActivity` |
| 设备 | `com.sx.app.ui.device.DeviceSettingsActivity` |
| 网络 | `com.sx.app.ui.network.NetworkSettingsActivity` |
| 相机 | `com.sx.app.ui.camera.VirtualCameraActivity` |
| 应用列表壳 | `com.sx.app.ui.sandbox.AppListActivity` |
| 选应用 | `com.sx.app.ui.sandbox.AppPickerActivity` |
| 详情 | `com.sx.app.ui.sandbox.AppDetailActivity` |
| 快捷方式落地 | `com.sx.app.ui.sandbox.ShortcutLaunchActivity` |
| 定位服务壳 | `com.sx.app.service.MockLocationService`（**空实现 only**） |

**Fragment（无单独 Manifest 项）：**

| 类 | FQCN |
|----|------|
| 首页 | `com.sx.app.ui.home.HomeFragment` |
| 应用 | `com.sx.app.ui.sandbox.AppListFragment` |
| 我的 | `com.sx.app.ui.me.MeFragment` |

---

## 2. 模型与引擎约定（修正后）

### 2.1 只保留一套分身模型

| 决策 | 使用 `com.sx.app.data.SandboxAppInfo` 作为唯一模型 |
|------|--------------------------------------------------|
| 字段 | 至少：`packageName`, `label`, `userId`, `addedAt`, `dataDir`（可空） |
| 说明 | docs/05 中的 `SandboxApp` **不另建类**；接口返回类型一律 `SandboxAppInfo` |
| 清理 | 勿新增并行的 `SandboxApp.java` |

### 2.2 新增类型（sandbox 包）

| 文件 | 职责 |
|------|------|
| `SandboxEngine.java` | 接口（方法对齐 docs/05，类型用 `SandboxAppInfo`） |
| `InstallResult.java` | success / userId / message |
| `HostAppInfo.java` | packageName, label, icon, sourceDir(可选) |
| `HostAppScanner.java` | 扫描本机可展示应用 |
| `FakeSandboxEngine.java` | Fake 实现 + **MODE_PRIVATE 持久化列表** |
| `SandboxProvider.java` | 单例：`init(app)` / `getEngine()` |

### 2.3 SandboxEngine 方法（Phase 0 行为）

| 方法 | Phase 0 行为 |
|------|----------------|
| `initialize` | 读 SP 恢复列表，`isReady=true` |
| `isReady` | initialize 后 true |
| `installFromHost` | 校验包名，加入 userId=0（已存在可返回失败或幂等成功） |
| `installFromApk` | **固定失败**：message=`Not supported in Phase 0` |
| `listInstalled` | 返回副本 List |
| `get` / `isInstalled` | 按 pkg+userId |
| `launch` | 不启真进程；返回 true + 调用方可 Toast |
| `kill` / `killAll` | no-op 成功或标记 isRunning=false |
| `clone` | 同包新 userId = max+1，label 带分身语义 |
| `uninstall` | 移除条目并持久化 |
| `clearData` | Fake：Toast 级成功，可更新时间戳；不删宿主数据 |
| `createShortcut` | 尝试 `ShortcutManager` 指向 `ShortcutLaunchActivity`；失败返回 false |
| `setDisplayName` | 改 label 并持久化（有则做） |

### 2.4 持久化

- 应用列表：JSON 数组写入 **私有** SP（可用 `SxPrefs` 的 private 路径，或 `sandbox_fake` + `MODE_PRIVATE`）。
- 配置：`LocationConfig` / `DeviceProfile` / `NetworkProfile` / `CameraConfig` 现有 `save/load`，**修改 `SxPrefs.get()` 为 MODE_PRIVATE**（或新增 `getPrivate` 并统一走 private）。
- **禁止** Phase 0 使用 `MODE_WORLD_READABLE`。

### 2.5 UI 取引擎

```text
// 仅允许
SandboxProvider.getEngine()
// 禁止在 Activity 内 new FakeSandboxEngine()
```

`SxApp.onCreate`：`SandboxProvider.init(this)` → engine.initialize。

---

## 3. UI / Layout 策略

### 3.1 复用现有 layout

绑定 **现有** `app/src/main/res/layout/*.xml` 中的 id，优先不改结构。  
允许小改：缺 id、Toolbar 位置导致无法工作。

### 3.2 App 列表布局（修正）

| 决策 | 新增 `fragment_app_list.xml`（内容可从 `activity_app_list.xml` 拷贝） |
|------|----------------------------------------------------------------------|
| `AppListFragment` | inflate `fragment_app_list` |
| `AppListActivity` | 仅承载 `AppListFragment` 或 include 同一布局；供首页卡片跳转 |

### 3.3 定位「启动模拟」（修正）

| 控件行为 | 只 `LocationConfig.enabled=true/false` + `save` + Toast |
|----------|--------------------------------------------------------|
| Toast 文案 | 例如：`已保存。Phase 0 不启动系统模拟定位服务。` |
| `MockLocationService` | **空壳**：`onStartCommand` 打日志并 `stopSelf`；**禁止** addTestProvider |
| 若 UI 误调 startService | 最多启动空壳，不崩溃 |

### 3.4 首页状态文案

| 授权 | `LicenseManager.isActivated` 真实结果 |
|------|----------------------------------------|
| Xposed/模块 | 固定：`LSPosed 模块未激活（Phase 0 不依赖）` 或等价，**不阻断进入** |

### 3.5 应用详情菜单

必须支持（与 docs/04 对齐，可简化实现）：

| 动作 | Phase 0 |
|------|---------|
| 启动 | engine.launch + Toast |
| 克隆 | engine.clone + 刷新/finish |
| 快捷方式 | engine.createShortcut |
| 清除数据 | 确认框 → clearData |
| 卸载/移除 | 确认框 → uninstall |
| 独立设置 | 跳转 `LocationSettingsActivity`，extras：`package_name`, `user_id`（设置页可先忽略 extras，但入口要有） |

---

## 4. 权限（B-16）

新增 `com.sx.app.util.PermissionHelper`（名称可微调）：

| 场景 | 权限 |
|------|------|
| 选媒体（相机页） | READ_MEDIA_* / READ_EXTERNAL_STORAGE |
| 定位页（可选） | FINE/COARSE；后台定位 Phase 0 可不强求 |
| 通知（若起空壳前台） | POST_NOTIFICATIONS（API 33+）；空壳可不申请 |
| 列应用 | Manifest 已有 QUERY_ALL_PACKAGES；扫描失败时 Toast 说明 |

`HostAppScanner`：排除自身包名；优先 `ACTION_MAIN`+`LAUNCHER` 应用；系统应用可默认隐藏。

---

## 5. 执行步骤（严格顺序）

每日结束应能编译；顺序勿跳。

### Step 1 — 工程变绿（B-01）≈ 0.5–1d

1. 实现 `SxApp`，Manifest 已指向 `.SxApp`。  
2. 为 Manifest 中**每一个** Activity/Service 建立 **可编译空壳**（`setContentView` 可用对应 layout 或临时 TextView）。  
3. `MockLocationService` 空壳落地。  
4. 修正 `SxPrefs` → **MODE_PRIVATE**。  
5. `./gradlew.bat :app:assembleDebug` **必须成功**。

**出口标准：** 安装后能启动（可进白屏/半成品页，不崩）。

---

### Step 2 — 引擎核心（B-06）≈ 1d

1. `SandboxEngine` + `InstallResult` + `HostAppInfo` + `HostAppScanner`。  
2. `FakeSandboxEngine` 持久化列表。  
3. `SandboxProvider`。  
4. `SxApp` 中 init。

**出口标准：** 单元级或临时调试可 install/list/clone/uninstall 且杀进程仍在。

---

### Step 3 — 启动与主框架（B-02/03/04/05/15）≈ 1–1.5d

1. `SplashActivity`：展示 `activity_splash` → 延迟约 2s →  
   - 未激活 → `LicenseActivity`  
   - 已激活 → `MainActivity`  
2. `LicenseActivity`：设备 ID、卡密、激活；成功进 Main。  
3. `MainActivity`：`activity_main` + BottomNav → Home / Apps / Me。  
4. `HomeFragment`：卡片跳转各模块 + 状态文案。  
5. `MeFragment`：版本、设备 ID、进授权。

**出口标准：** 卡密 `SX-DEV-20991231` 可激活并进三 Tab。

---

### Step 4 — 沙箱 UI（B-07/08/09）≈ 1.5–2d

1. `fragment_app_list.xml` + `AppListFragment` + Adapter。  
2. `AppListActivity` 包装 Fragment。  
3. `AppPickerActivity` + `HostAppScanner` + 权限/空列表提示。  
4. `AppDetailActivity`：启动/克隆/快捷方式/清数据/卸载/独立设置。  
5. `ShortcutLaunchActivity`：读 extras，Toast「Phase 0 模拟启动 pkg#userId」后可选 finish。

**出口标准：** 添加 → 列表 → 克隆 #2 → 删除；杀进程列表仍在。

---

### Step 5 — 配置页（B-10～B-14）≈ 1.5–2d

1. `LocationSettingsActivity`：绑定 `LocationConfig`；保存；启动模拟按 **§3.3**。  
2. `LocationPickerActivity`：内置 POI（北上广深等）+ 搜索过滤；`setResult` lat/lng/address。  
3. `DeviceSettingsActivity`：绑定 `DeviceProfile`；随机/重置/保存。  
4. `NetworkSettingsActivity`：绑定 `NetworkProfile`。  
5. `VirtualCameraActivity`：绑定 `CameraConfig`；选文件可 stub 或系统选择器写 path。

**出口标准：** 四类配置保存后强杀仍在；非法经纬度有提示。

---

### Step 6 — 收尾（B-16/B-17）≈ 0.5–1d

1. 权限封装接到 Picker/相机/定位。  
2. 对照 `docs/04` 主路径走查。  
3. 修崩溃与阻断交互。  
4. 填写进度（MR 描述勾选 B-01～B-17）。

**出口标准：** 下文验收清单全过。

---

## 6. 建议文件清单（创建时打勾）

```text
com/sx/app/SxApp.java
com/sx/app/sandbox/SandboxEngine.java
com/sx/app/sandbox/InstallResult.java
com/sx/app/sandbox/HostAppInfo.java
com/sx/app/sandbox/HostAppScanner.java
com/sx/app/sandbox/FakeSandboxEngine.java
com/sx/app/sandbox/SandboxProvider.java
com/sx/app/ui/SplashActivity.java
com/sx/app/ui/MainActivity.java
com/sx/app/ui/LicenseActivity.java
com/sx/app/ui/home/HomeFragment.java
com/sx/app/ui/me/MeFragment.java
com/sx/app/ui/location/LocationSettingsActivity.java
com/sx/app/ui/location/LocationPickerActivity.java
com/sx/app/ui/device/DeviceSettingsActivity.java
com/sx/app/ui/network/NetworkSettingsActivity.java
com/sx/app/ui/camera/VirtualCameraActivity.java
com/sx/app/ui/sandbox/AppListFragment.java
com/sx/app/ui/sandbox/AppListActivity.java
com/sx/app/ui/sandbox/AppPickerActivity.java
com/sx/app/ui/sandbox/AppDetailActivity.java
com/sx/app/ui/sandbox/ShortcutLaunchActivity.java
com/sx/app/ui/sandbox/SandboxAppAdapter.java      # 名称可调
com/sx/app/ui/sandbox/HostAppAdapter.java
com/sx/app/ui/location/PlaceAdapter.java
com/sx/app/service/MockLocationService.java        # 空壳
com/sx/app/util/PermissionHelper.java
res/layout/fragment_app_list.xml                  # 新增
```

已有、优先复用：`data/*`、`license/LicenseManager`、`util/DeviceIdGenerator|CryptoUtil|TimeGuard`、全部既有 layout（除新增 fragment）。

---

## 7. 验收清单（全部勾选才算完成）

### 7.1 构建

- [ ] `gradlew :app:assembleDebug` 成功  
- [ ] 安装启动无闪退  

### 7.2 启动与授权

- [ ] Splash 展示后按激活状态跳转  
- [ ] 未激活进 License；输入 `SX-DEV-20991231` 成功进 Main  
- [ ] 设备 ID 可见  

### 7.3 导航

- [ ] 首页 / 应用 / 我的 可切换  
- [ ] 首页卡片可进：定位、设备、网络、相机、授权、应用列表  

### 7.4 Fake 沙箱

- [ ] 添加本机应用成功出现在列表  
- [ ] 详情启动 Toast（模拟）  
- [ ] 克隆出现新 userId 分身  
- [ ] 清除数据有反馈  
- [ ] 卸载后列表消失  
- [ ] **强杀进程后列表仍在**  
- [ ] 列表为空时有空态  

### 7.5 配置

- [ ] 定位/设备/网络/相机保存后 **强杀仍在**  
- [ ] 地点选择回传坐标到定位页  
- [ ] 定位「启动模拟」不崩溃且不宣称已系统级注入（Toast 说明 Phase 0）  

### 7.6 边界

- [ ] 工程 **无** BlackBox 依赖仍能完成以上路径  
- [ ] 未使用 MODE_WORLD_READABLE  

### 7.7 不测项（勿当作失败）

- 分身内读到假 GPS/IMEI  
- 真多开微信  
- 快捷方式启动真实第三方进程  
- 前台定位通知常驻  

---

## 8. 分支与交付

| 项 | 要求 |
|----|------|
| 分支 | `feature/sx-phase0-ui-fake`（建议） |
| 提交范围 | 仅 `sx/` |
| MR 描述 | 勾选 B-01～B-17；已知问题；编译命令 |
| 可选 | 截图：启动、首页、应用列表、设置、授权 |

完成后 **停止开发**，等待 Phase 1（Epic C BlackBox）指令；勿自行接引擎。

---

## 9. 一句话执行令

> 按本文 Step 1→6 顺序，在 `sx` 内实现 Manifest 对齐的 UI + `FakeSandboxEngine`（`SandboxAppInfo` 单模型、MODE_PRIVATE、定位服务仅空壳），完成第 7 节验收后提交 `feature/sx-phase0-ui-fake`。先读 `docs/09`，任务状态回写 `docs/10` Epic B。

---

## 10. 修订相对原稿（审计摘要）

| 原稿问题 | 本文处理 |
|----------|----------|
| 双模型 SandboxApp / SandboxAppInfo | 只用 `SandboxAppInfo` |
| 定位 service toggle 易做真服务 | 仅存配置 + Toast；Service 空壳 |
| 缺 fragment 布局 | 明确新增 `fragment_app_list.xml` |
| 缺权限/包可见性 | Step 6 + PermissionHelper + Scanner 说明 |
| MODE_WORLD_READABLE | 禁用，改 PRIVATE |
| 缺 Provider / Adapter / 顺序 | 全文补齐 |
| 类名 CameraSettings | 统一 `VirtualCameraActivity` |
