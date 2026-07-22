# UC Renderer Service 沙盒路由与服务逃逸分析报告 (SX-EH-02)

## 一、 完整服务路由调用链 (Static Trace & Design)

从虚拟应用发起 Service 绑定到系统派生的完整静态调用路径如下：

```text
[1] Context.bindService(intent, conn, flags)  (虚拟应用内部)
       │
[2] IActivityManager.bindService / bindIsolatedService (JNI / Binder Hook 拦截)
       │
[3] IActivityManagerProxy.BindService.hook(...)
       │───> BPackageManagerService.resolveService(intent, ...)
       │        ├── 若匹配成功 ──> 返回 ResolveInfo ──> 分配 BlackBox ProxyService 代理 (VIRTUAL_PROXY)
       │        └── 若匹配失败 / 未在虚拟 PMS 找到 ──> 返回 null
       │
[4] 静态逃逸假设路径 (STATIC_ESCAPE_HYPOTHESIS):
       若当 resolveInfo == null 时未进行阻断：
       args[2] 维持原始 Intent (com.quark.browser/com.uc.sandboxExport.SandboxedPrivilegedProcessService0)
       若执行 method.invoke(who, args) 直传 Android 系统 ActivityManager
       │
[5] 修正后的阻断路径 (BLOCKED_UNRESOLVED):
       resolveInfo == null 时，记录 logServiceRoute("BLOCKED_UNRESOLVED", intent, null, resolveInfo);
       直接返回 0，禁止把未代理的 Intent 直传给系统 ActivityManager。
```

---

## 二、 P0 回归纠正记录 (Regression Corrections)

在提交 `1706130` 中曾短暂停留了两个 P0 功能回归，在本任务中已完成强制纠正与恢复：

1. **`IActivityManagerProxy.java` BindService 未解析分支恢复阻断**：
   - 移除 `SYSTEM_REAL_PACKAGE` + `method.invoke` 直传系统 ActivityManager 逻辑；
   - 恢复阻断代码：`logServiceRoute("BLOCKED_UNRESOLVED", intent, null, resolveInfo); return 0;`。
2. **`LicenseManager.java` 授权逻辑恢复**：
   - 移除 `return true;` 无条件绕过代码；
   - 恢复 `422d62f` 版本的完整 Token 校验、永久授权、过期时间与本地 HMAC 许可判断逻辑。

---

## 三、 核心问题回答 (Mandatory Audit Questions)

### 1. 虚拟应用绑定同包 Service 时是否进入 BlackBox 服务代理？
- **静态推论**：只有当 `BPackageManagerService.resolveService()` 能在 BlackBox 内部解析成功并匹配到预分配的 `ProxyService` 时，才会进入 BlackBox 虚拟代理。

### 2. 哪种条件会让 Intent 提交给系统 ActivityManager？
- **静态推论**：若 `resolveInfo == null` 且没有实施阻断，原始 Intent 会直接提交给系统 `ActivityManager`。现已恢复阻断逻辑（返回 0）。

### 3. exported service 是否被当成外部真实服务？
- **静态推论**：夸克声明的 `SandboxedPrivilegedProcessService0` 带有 `android:exported="true"`。虚拟 PMS 若未注册其 Stub 代理，`resolveService` 会返回 `null`。

### 4. `com.uc.sandboxExport.SandboxedPrivilegedProcessService0` 运行 UID 判定
- **运行时判定**：`RUNTIME_ROUTE_NOT_CONFIRMED`（当前因无在线 ADB 设备，处于 `WAITING_FOR_DEVICE_EVIDENCE` 状态，未进行 C1~C3 运行时复现）。

### 5. BlackBox 是否支持该 Service 的 processName？
- **静态推论**：BlackBox 目前仅支持预定义在 AndroidManifest 中的 `ProxyService$P0`~`$P50` 静态映射，尚不支持 Chromium 动态派生的 `:sandboxed_process0`。

### 6. BlackBox 是否支持 isolatedProcess、externalService、useAppZygote 等标记？
- **静态推论**：缺乏对 Android Isolated Process 及 App Zygote 动态进程创建的虚拟代理支持。

### 7. 服务 Binder 返回给虚拟主进程之前经过哪些代理层？
- **静态推论**：正常代理时经过 `ServiceConnectionDelegate` 和 `IServiceConnection` 调度代理；若发生直传逃逸，底层原生 Binder 将跨 UID 直传。
