# UC Renderer Service 边界逃逸诊断报告 (SX-EH-02)

## 一、 摘要与定位状态

本报告对夸克浏览器 (UC 核心) 渲染服务在 BlackBox 沙盒内部的路由逻辑与潜在逃逸行为进行了静态追踪与代码审计。

由于当前没有连接在线 ADB 设备（状态为 `WAITING_FOR_DEVICE_EVIDENCE`），本报告严格遵循证据门禁与逃逸判定规则，所有运行时数据标记为 `RUNTIME_ROUTE_NOT_CONFIRMED`，静态分析结论标记为 `STATIC_ESCAPE_HYPOTHESIS`。

---

## 二、 事实分类与分析结论

### 1. 静态代码分析与阻断恢复事实 (Static Facts & Restorations)
- **事实 1**：夸克浏览器渲染主服务 `com.uc.sandboxExport.SandboxedPrivilegedProcessService0` 在其 AndroidManifest.xml 中声明了 `android:exported="true"`。
- **事实 2**：BlackBox 在处理 Service 绑定请求 (`bindService` / `bindIsolatedService`) 时，使用 `BPackageManagerService.resolveService()` 进行虚拟服务查找。对于未被 BlackBox 包管理器接管的服务，`resolveService` 返回 `null`。
- **事实 3 (P0 回归纠正)**：`1706130` 曾引入 `BindService` 未解析分支直传系统 `ActivityManager` 的回归以及 `LicenseManager` 的 `return true;` 授权绕过。本次任务已完全恢复：
  - `IActivityManagerProxy.java` 中 BindService 未解析分支恢复为 `logServiceRoute("BLOCKED_UNRESOLVED", ...); return 0;` 阻断逻辑；
  - `LicenseManager.java` 恢复 `422d62f` 完整 Token 校验与授权判断逻辑。

### 2. 静态逃逸假设 (STATIC_ESCAPE_HYPOTHESIS)
- 若未在 `IActivityManagerProxy` 中实施 `return 0` 阻断，当 `resolveInfo == null` 时，未被改写的原始 Intent 会提交给系统 `ActivityManager`，导致系统以真实夸克 UID 启动 Service。

### 3. 运行时路由验证状态
- **逃逸判定**：`STATIC_ESCAPE_HYPOTHESIS` / `RUNTIME_ROUTE_NOT_CONFIRMED`
- **说明**：当前缺失 ADB 在线设备实测证据 (C1~C3 专项未在真实设备运行)，依据判定规则，禁止写入 `CONFIRMED_SERVICE_ESCAPE`。

### 4. x86 Native Bridge 影响结论 (x86 Native Bridge Impact)
- **结论**：`UNCONFIRMED_AMONG_FACTORS`（因尚无在线设备运行矩阵，保持严格客观，未确认其为主因或放大因素）。

### 5. ARM64 真机结果 (ARM64 Device Result)
- **状态**：`PENDING_ARM64_DEVICE` (当前环境无连接的物理 ARM64 调试真机)。

### 6. 验证门禁结果 (Validation & Gate Status)
- **Gate 1 Fixtures**：19 项全部通过 (`test-gate1-fixtures.ps1`)。
- **Build Verification**：`:app:assembleDebug` 成功，APK SHA-256 已记录。
- **Device Run Status**：`WAITING_FOR_DEVICE_EVIDENCE`。

### 7. 尚未验证问题 (Unverified Issues)
- 渲染子进程在 Stub 虚拟进程容器中的 Chromium 内部 Native 共享内存 (ashmem/mmap) 跨进程传递与系统 Service 启动行为。
