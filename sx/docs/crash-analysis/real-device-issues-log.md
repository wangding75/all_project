# 实机验证已知问题记录 (Real-Device Feedback Log)

| 项 | 内容 |
|----|------|
| 最近更新 | 2026-07-27 |
| 验证设备 | 小米 25019PNF3C / HyperOS / Android 16 (API 36) |
| 应用包名 | `com.sx.app.debug` |

---

## 一、 问题列表

### 问题 1：LSPosed 模块显示未激活
- **现象**：在真机环境安装应用后，LSPosed 框架检测提示闪现 (sx) Xposed 模块未激活或未生效。
- **状态**：待排查（非本轮阻塞）
- **排查方向**：
  - 检查 `AndroidManifest.xml` 中的 Xposed 模块声明 (`xposedmodule`, `xposeddescription`, `xposedminversion`)；
  - 检查 LSPosed 作用域（Scope）是否绑定宿主/目标应用。

### 问题 2：沙盒调起提示“启动失败：授权未激活或底层引擎没有启动”
- **现象**：真机调起 Chrome / 夸克时提示 `启动失败：授权未激活或底层引擎未就绪`。
- **状态**：已在本轮调试中处理引擎 `mReady` / 授权校验相关逻辑；需回归验证。
- **排查方向（历史）**：
  1. `mReady == false`（`BlackBoxCore.doCreate()` 失败）；
  2. 授权状态在多 Context 下未同步。

### 问题 3：沙箱内系统时钟无法保持打开（HyperOS DeskClock）
- **现象**：
  - SX 内点击系统时钟（`com.android.deskclock`）只显示“正在启动”，随后无界面 / 回到主页；
  - 或 Activity 创建后立即销毁；
  - 日志曾出现 `onActivityCreated` 后毫秒级 `onFinishActivity`。
- **验证环境**：Android 16 (API 36) + HyperOS 预装时钟。
- **状态**：**已修复并真机验证通过**（2026-07-26）

#### 根因（分层）

| 层级 | 原因 | 版本/厂商关系 |
|------|------|----------------|
| A. Activity 启动改写失败 | `HCallbackProxy` 在 Android 12+ 只改写 `getLaunchingActivity`，未同步改写 `LaunchActivityItem.mInfo/mIntent`。实际实例仍是 `ProxyActivity`，其 `finish()` 用同一 token 拆掉访客虚拟栈。 | **Android 12+ / 16 必现风险** |
| B. isTaskRoot 判断错误 | 访客（HyperOS 时钟）`isTaskRoot()` 走 `getTaskForActivity(token, onlyRoot=true)`；Proxy 壳导致返回 false，可能 finish + MAIN 重开。此前误 hook `isTopOfTask`。 | **API 31+ ActivityClient 路径** |
| C. bindService 未拦截 | 时钟 UI 已创建后，`StopwatchFragment` 绑定 `StopWatchService`。Android 14+ 走 `bindServiceInstance`，未 hook 时绑到系统未 export 服务 → `SecurityException` 进程崩溃。 | **Android 14+** |
| D. 其它本轮顺带修复 | PM flags Long 转型、RECEIVER_EXPORTED、JNI ExceptionClear、ContentProvider UID、JobScheduler 空安全、MAIN 启动防抖等 | 高版本通用 |

#### 修复点（代码）

- `HCallbackProxy`：Pie+ 统一改写 `LaunchActivityItem`；S+ 仍同步 `getLaunchingActivity`
- `IActivityClientProxy` / `ActivityManagerCommonProxy`：hook `getTaskForActivity(onlyRoot=true)`；Proxy 壳 finish 不 `onFinishActivity` 访客
- `ProxyActivity`：壳 finish 标记，避免拆访客栈
- `IActivityManagerProxy`：hook `bindServiceInstance`，访客服务走 `ProxyService`
- 及相关：`IPackageManagerProxy` flags、`BroadcastManager` EXPORTED、`JniHook`、`ContentProviderStub` 等

#### 验收证据（真机）

```
HCallbackStub: rewrote LaunchActivityItem -> com.android.deskclock.DeskClockTabActivity
AppInstrumentation: callActivityOnCreate: com.android.deskclock.DeskClockTabActivity
SX_SERVICE_ROUTE: ... StopWatchService ... routeType=VIRTUAL_PROXY
mCurrentFocus = com.android.deskclock/DeskClockTabActivity
进程 com.android.deskclock 持续存活，无 Force finishing
```

#### 经验结论

- **VA / BlackBox 路线必须按 Android 版本分流 hook**；国内 ROM（HyperOS 等）上系统 App 需真机专项验证。
- 同类问题在 VirtualApp 等方案上同样存在，属技术路线共性，非本项目独有。

---

## 二、 本轮真机调试修复清单（摘要）

| 项 | 说明 |
|----|------|
| 授权 | `LicenseManager` 真实校验；DEV 卡 `SX-DEV-20991231` |
| 引擎 | `BlackBoxSandboxEngine` ready / 启动兜底 |
| 时钟启动 | HCallback + isTaskRoot + bindServiceInstance（问题 3） |
| 配置/伪装 | ProfileRepository 广播、Camera/Location hook 加固 |
| 服务端 | `server/api/license.py`、`server/config.py` 同步调整 |

---

## 三、 后续建议回归

1. Android 12 / 13 / 14 / 15 各至少一台（非仅 16）
2. 其它系统 App：录音机、文件管理、相册
3. 三方目标：夸克、钉钉、Chrome
4. OPPO / vivo 各一台（厂商 ROM 差异）

---

> 本文档记录实机问题与结论；问题 3 已带修复说明，便于交接与回归。
