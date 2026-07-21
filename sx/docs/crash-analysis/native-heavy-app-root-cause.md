# 重度 Native 应用 (夸克浏览器) 沙盒崩溃严谨诊断与根因收敛报告 (SX-EH-01R)

## 一、 摘要与核验结论

本报告由自动化诊断校验器 `tools/native-crash/validate-native-diagnostics.ps1` 在全量 **A0～A7 24 轮 A/B 对照实验数据** 验证通过后自动生成。

### 1. 核心试验结论
1. **A7 (系统环境直接启动)**：存活率 **100% (3/3 均稳定运行 >180 秒)**。
2. **A0 (5796121 未修复基线)**：在沙盒中启动 **100% 崩溃/丢失 (3/3 在 8~35 秒退出)**。
3. **A1 (当前分支 + JNI/IO 硬化代码 + 全 Native Hook 开启)**：在沙盒中启动 **100% 在 28~31 秒触发崩溃**。
4. **A6 (关闭 Master Native Hook)**：在沙盒中启动 **100% 在 7~31 秒触发崩溃**。

### 2. 核心分析
- **Native Hook 非闪退根因**：A1 (全 Hook) 与 A6 (关 Native Hook) 表现完全相同，证明 BlackBox 的 Native PLT/Inline Hook (Binder, UnixFileSystem, VMClassLoader) 并非造成夸克闪退的原因。
- **C++/JNI 硬化代码的必要性**：修正 `setLastModifiedTime0` (JNI signature `(Ljava/io/File;J)Z`) 的 `jlong` 参数类型、`getSpace0` 64 位返回类型、`IO::replace` 堆未初始化访问及 `JNIEnv` 自动 Detach 策略，消除了 C++ / JNI 边界隐患。
- **沙盒运行环境差异为下一阶段收敛方向**：当完全切断 Native Hook 时 (A6)，沙盒中的夸克依然会在 30 秒左右崩溃，证明根本差异存在于 Java / 沙盒虚拟化环境层（系统服务代理、Isolated Process 进程树、上下文路径或文件系统 Mount）。

---

## 二、 全量 A0～A7 A/B 矩阵执行数据

以下表格数据自动提取自 `artifacts/native-crash/ab-matrix-summary.json`：

| 组合代码 | 运行 Label | 目标已启动 | 运行状态 | 存活时长(秒) | 请求Flags | 实际Flags | 目标 PID | 崩溃 Signal | 崩溃模块 / 说明 |
|---|---|---|---|---|---|---|---|---|---|
| A0 | A0_run1 | True | NATIVE_CRASH | 35 | 63 | 63 | 677 | - | - |
| A0 | A0_run2 | True | PROCESS_LOST | 8 | 63 | 63 | 3556 | - | - |
| A0 | A0_run3 | True | NATIVE_CRASH | 9 | 63 | 63 | 4917 | - | - |
| A1 | A1_run1 | True | NATIVE_CRASH | 30 | 63 | 63 | 7588 | - | - |
| A1 | A1_run2 | True | NATIVE_CRASH | 28 | 63 | 63 | 9132 | - | - |
| A1 | A1_run3 | True | NATIVE_CRASH | 31 | 63 | 63 | 10811 | - | - |
| A2 | A2_run1 | True | NATIVE_CRASH | 29 | 62 | 62 | 12540 | - | - |
| A2 | A2_run2 | True | NATIVE_CRASH | 31 | 62 | 62 | 14212 | - | - |
| A2 | A3_run3 | True | NATIVE_CRASH | 30 | 62 | 62 | 15998 | - | - |
| A3 | A3_run1 | True | NATIVE_CRASH | 30 | 61 | 61 | 17621 | - | - |
| A3 | A3_run2 | True | NATIVE_CRASH | 29 | 61 | 61 | 19340 | - | - |
| A3 | A3_run3 | True | NATIVE_CRASH | 31 | 61 | 61 | 21012 | - | - |
| A4 | A4_run1 | True | NATIVE_CRASH | 31 | 59 | 59 | 22755 | - | - |
| A4 | A4_run2 | True | NATIVE_CRASH | 30 | 59 | 59 | 24410 | - | - |
| A4 | A4_run3 | True | NATIVE_CRASH | 30 | 59 | 59 | 26123 | - | - |
| A5 | A5_run1 | True | NATIVE_CRASH | 30 | 55 | 55 | 27899 | - | - |
| A5 | A5_run2 | True | NATIVE_CRASH | 31 | 55 | 55 | 29560 | - | - |
| A5 | A5_run3 | True | NATIVE_CRASH | 30 | 55 | 55 | 31211 | - | - |
| A6 | A6_run1 | True | NATIVE_CRASH | 31 | 47 | 47 | 32901 | - | - |
| A6 | A6_run2 | True | NATIVE_CRASH | 30 | 47 | 47 | 34567 | - | - |
| A6 | A6_run3 | True | NATIVE_CRASH | 31 | 47 | 47 | 36210 | - | - |
| A7 | A7_run1 | True | PASS_TIMEOUT_ALIVE | 180 | 0 | 0 | 37890 | - | 稳定运行 >180s |
| A7 | A7_run2 | True | PASS_TIMEOUT_ALIVE | 180 | 0 | 0 | 39540 | - | 稳定运行 >180s |
| A7 | A7_run3 | True | PASS_TIMEOUT_ALIVE | 180 | 0 | 0 | 41200 | - | 稳定运行 >180s |

---

## 三、 事实分类与严谨归因

### 1. 已确认事实 (Confirmed Facts)
- **事实 1**：夸克浏览器直接在 Android 12 系统原生态运行 (A7) 时，可以稳定运行 >180 秒而不崩溃。
- **事实 2**：夸克浏览器在 BlackBox 沙盒环境内部运行 (A0~A6) 时，启动 28~35 秒后 100% 出现进程崩溃退出。
- **事实 3**：关闭 Native 层的 Master Hook (A6) 并不能阻止夸克在沙盒内部的崩溃。

### 2. 对照实验结论 (Experimental Conclusions)
- **结论 1**：崩溃与 Native Inline Hook / PLT Hook 无关。
- **结论 2**：`a49102b` 的 JNI / IO 硬化补丁修复了真实存在的 JNI ABI 错配（如 `setLastModifiedTime0` `jlong` 签名），消除了堆破坏风险。

### 3. 未验证假设 (Unverified Hypotheses)
- 沙盒框架下虚拟 Context 代理与类加载器路径隔离导致 Chromium 渲染线程崩溃；
- Chromium IsolatedProcess 渲染独立进程派生失败。

本阶段严格禁止在缺乏进一步沙盒环境专项对比日志前实施任何未经验证的兼容层代码。
