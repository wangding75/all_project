# UC Renderer Service 沙盒路由与服务逃逸分析报告 (SX-EH-02)

## 一、 完整服务路由调用链 (Service Routing Trace)

从虚拟应用发起 Service 绑定到系统派生的完整调用路径如下：

```text
[1] Context.bindService(intent, conn, flags)  (虚拟应用内部)
       │
[2] IActivityManager.bindService / bindIsolatedService (JNI / Binder Hook 拦截)
       │
[3] IActivityManagerProxy.BindService.hook(...)
       │───> BPackageManagerService.resolveService(intent, ...)
       │        ├── 若匹配成功 ──> 返回 ResolveInfo ──> 分配 BlackBox ProxyService 代理 (VIRTUAL_PROXY)
       │        └── 若匹配失败 / exported=true / isolatedProcess=true / 无代理匹配 ──> 返回 null
       │
[4] 逃逸路径 (SYSTEM_REAL_PACKAGE):
       当 resolveInfo == null 时，proxyIntent 未生成：
       args[2] 维持原始 Intent (com.quark.browser/com.uc.sandboxExport.SandboxedPrivilegedProcessService0)
       执行 method.invoke(who, args) 直传 Android 系统 ActivityManager
       │
[5] Android 系统 ActivityManager 收到原始 Intent：
       直接按照系统 PMS 规则拉起真实夸克包名的渲染子进程 `com.quark.browser:sandboxed_process0`
       进程运行于系统赋予夸克的真实 UID（例如 u0_a150），而非宿主 sx 的 UID (u0_a47)
```

---

## 二、 核心问题回答 (Mandatory Audit Questions)

### 1. 虚拟应用绑定同包 Service 时是否进入 BlackBox 服务代理？
- **结论**：只有当 `BPackageManagerService.resolveService()` 能在 BlackBox 内部解析成功并匹配到预分配的 `ProxyService` 时，才会进入 BlackBox 虚拟代理。若解析失败或属于导出的系统服务，则无法进入代理。

### 2. 哪种条件会让 Intent 直接提交给系统 ActivityManager？
- **结论**：当 `resolveInfo == null` 且组件不处于 `AppSystemEnv.isOpenPackage()` 白名单时，`IActivityManagerProxy.BindService` 中 `proxyIntent` 为 `null`，跳过 Intent Component 重写，直接调用 `method.invoke(who, args)` 将原始 Intent 提交给系统 `ActivityManager`。

### 3. exported service 是否被当成外部真实服务？
- **结论**：是的。夸克声明的 `SandboxedPrivilegedProcessService0` 带有 `android:exported="true"`。BlackBox 默认不会为未注册的外部导出服务分配虚拟 Stub 代理。

### 4. `com.uc.sandboxExport.SandboxedPrivilegedProcessService0` 为什么以真实夸克 UID 启动？
- **结论**：因为原始 Intent 未经修改直接提交给了系统 `ActivityManager`，系统直接派生 `com.quark.browser:sandboxed_process0` 进程，分配的是系统给夸克安装包分配的真实 App UID，而非沙盒宿主的 UID。

### 5. BlackBox 是否支持该 Service 的 processName？
- **结论**：不支持。BlackBox 目前仅支持预定义在 AndroidManifest 中的 `ProxyService$P0`~`$P50` 进程映射，无法处理 Chromium 架构动态派生的 `:sandboxed_process0`。

### 6. BlackBox 是否支持 isolatedProcess、externalService、useAppZygote 等标记？
- **结论**：不支持。BlackBox 目前缺乏对 Android Isolated Process 沙盒隔离服务及 App Zygote 动态进程创建的虚拟代理支持。

### 7. 服务 Binder 返回给虚拟主进程之前经过哪些代理层？
- **结论**：正常代理时经过 `ServiceConnectionDelegate` 和 `IServiceConnection` 调度代理；发生逃逸时，系统底层的原生 Binder 句柄将直接返回给虚拟主进程，导致跨沙盒 UID 的 Binder 通信损坏。
