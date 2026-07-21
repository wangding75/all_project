# UC Renderer Service 边界逃逸诊断报告 (SX-EH-02)

## 一、 摘要与定位结论

本报告对夸克浏览器 (UC 核心) 渲染服务在 BlackBox 沙盒内部的路由逻辑与跨沙盒逃逸行为进行了静态代码追踪与路由分析。

---

## 二、 事实分类与分析结论

### 1. 已确认事实 (Confirmed Facts)
- **事实 1**：夸克浏览器渲染主服务 `com.uc.sandboxExport.SandboxedPrivilegedProcessService0` 在其 AndroidManifest.xml 中声明了 `android:exported="true"`。
- **事实 2**：BlackBox 在处理 Service 绑定请求 (`bindService` / `bindIsolatedService`) 时，使用 `BPackageManagerService.resolveService()` 进行虚拟服务查找。对于未被 BlackBox 包管理器接管的导出服务或特定 Isolated 服务，`resolveService` 返回 `null`。
- **事实 3**：当 `resolveInfo == null` 时，BlackBox 的 `IActivityManagerProxy.BindService` 会放弃 Component 重写，直接将原始 Intent (`com.quark.browser/com.uc.sandboxExport.SandboxedPrivilegedProcessService0`) 直传给 Android 系统的真实 `ActivityManager`。

### 2. 已确认调用链 (Confirmed Call Chain)
`Context.bindService(...)`
  └──> `IActivityManager.bindService` (Proxy Hook 拦截)
         └──> `IActivityManagerProxy.BindService.hook(...)`
                ├── `BlackBoxCore.getBPackageManager().resolveService(intent, ...)`  ===> 返回 `null`
                └── 跳过 Component 代理转换，直接执行 `method.invoke(who, args)` 直传系统 `ActivityManager`
                       └──> 系统 `ActivityManager` 以 **真实夸克 UID** 启动 `com.quark.browser:sandboxed_process0`

### 3. 已确认逃逸点 (Confirmed Escape Point)
- **逃逸类**：[`top.niunaijun.blackbox.fake.service.IActivityManagerProxy.BindService`](file:///d:/github/all_project/sx/blackbox/Bcore/src/main/java/top/niunaijun/blackbox/fake/service/IActivityManagerProxy.java#L244-L269)
- **逃逸逻辑**：
  ```java
  ResolveInfo resolveInfo = BlackBoxCore.getBPackageManager().resolveService(intent, 0, resolvedType, userId);
  if (resolveInfo != null || AppSystemEnv.isOpenPackage(intent.getComponent())) {
      // 代理逻辑 ...
  }
  // 当 resolveInfo == null 时，直接向下走：
  logServiceRoute("SYSTEM_REAL_PACKAGE", intent, null, resolveInfo);
  return method.invoke(who, args); // <-- 逃逸点：直传系统 ActivityManager
  ```

### 4. x86 Native Bridge 影响 (x86 Native Bridge Impact)
- x86 架构下的 `libhoudini` / `ndk_translation` 属于**协同放大因素**而非服务逃逸的根本原因。
- 服务逃逸导致渲染服务跨 UID 逃逸至系统环境，造成 Binder 通信与 IPC 权限隔离失败，进一步触发 Native 层的 IPC 崩溃。

### 5. ARM64 真机结果 (ARM64 Device Result)
- **状态**：`PENDING_ARM64_DEVICE` (当前环境无连接的物理 ARM64 调试真机，保持严格客观不伪造数据)。

### 6. 建议修改的具体类和方法 (Suggested Fix Scope)
在后续修复任务中（本诊断任务严格不实施修改），建议针对以下类和方法进行虚拟服务代理增强：
1. **类**：`top.niunaijun.blackbox.fake.service.IActivityManagerProxy.BindService`
   - **方法**：`hook(Object who, Method method, Object[] args)`
   - **改进**：对同包但 `resolveInfo == null` 的同源 Service，强制创建虚拟动态 ProxyService 容器，阻止直传系统 ActivityManager。
2. **类**：`top.niunaijun.blackbox.core.system.pm.BPackageManagerService`
   - **方法**：`resolveService(...)`
   - **改进**：补充对 `isolatedProcess="true"` 和 dynamic `processName` 的解析支持。

### 7. 尚未验证问题 (Unverified Issues)
- 渲染子进程重定向至 Stub 虚拟进程后，Chromium 内部 Native 共享内存 (ashmem/mmap) 跨进程传递问题。
