# SX Native Crash Diagnostics Scripts v2

> 修复 Windows PowerShell 5.1 解析错误：插值变量后紧跟冒号时使用 `${name}:`；Fixture 调用子 PowerShell 时允许预期的非零退出码。

# SX Native Crash Diagnostics Scripts

将本目录中的 4 个 `.ps1` 文件放到：

```text
sx/tools/native-crash/
```

脚本会通过自身位置自动定位 `sx` 根目录，因此可以从任意当前目录执行。

## 文件

| 文件 | 作用 |
|---|---|
| `collect-native-crash.ps1` | 单轮启动、精确绑定 PID/UID/starttime、采集日志和本轮 tombstone、生成 `result.json` |
| `run-native-ab-matrix.ps1` | 安装 A0/当前 APK、执行 A0～A7、失败即停、生成完整汇总 |
| `validate-native-diagnostics.ps1` | 深度核对 summary 与每轮 `result.json`，检查 PID、Flags、状态、tombstone、Host/Guest 证据 |
| `test-gate1-fixtures.ps1` | 3 个正向和 16 个负向 Fixture，确认门禁会主动拒绝坏数据 |

## 前置条件

1. Windows PowerShell 5.1 或 PowerShell 7。
2. `adb`、`git` 已加入 PATH。
3. sx Debug 构建包含：
   - `ShortcutLaunchActivity`；
   - `SX_TARGET_BOUND` 日志；
   - `debug.sx.native_hook_flags`；
   - `debug.sx.run_id`。
4. A0 APK 已从真实 `5796121` worktree 构建到：

```text
sx/artifacts/native-crash/app-debug-a0.apk
```

5. 当前 APK 已构建到：

```text
sx/app/build/outputs/apk/debug/app-debug.apk
```

## 先运行门禁 Fixture

在 `sx` 目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\native-crash\test-gate1-fixtures.ps1
```

只有输出以下结果才允许连接设备执行矩阵：

```text
All fixture cases passed.
```

## 单轮采集

### sx 沙盒内运行夸克

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\native-crash\collect-native-crash.ps1 `
  -DeviceSerial 127.0.0.1:16384 `
  -RunLabel A1_run1 `
  -ComboName A1 `
  -RequestedFlags 63 `
  -LaunchTimeoutSeconds 180
```

### 系统直接运行夸克

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\native-crash\collect-native-crash.ps1 `
  -DeviceSerial 127.0.0.1:16384 `
  -RunLabel A7_run1 `
  -ComboName A7 `
  -SystemDirect `
  -RequestedFlags 0 `
  -LaunchTimeoutSeconds 180
```

### 旧基线 A0

A0 没有 `SX_TARGET_BOUND` 时使用严格的“启动前后新进程 + 精确 cmdline + 宿主 UID”识别：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\native-crash\collect-native-crash.ps1 `
  -DeviceSerial 127.0.0.1:16384 `
  -RunLabel A0_run1 `
  -ComboName A0 `
  -LegacySandboxDiscovery `
  -RequestedFlags 63 `
  -LaunchTimeoutSeconds 180
```

## 完整矩阵

建议显式提供两个 APK 的 SHA-256：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\native-crash\run-native-ab-matrix.ps1 `
  -DeviceSerial 127.0.0.1:16384 `
  -LaunchTimeoutSeconds 180 `
  -RunsPerCombo 3 `
  -A0ExpectedSha256 "<A0_APK_SHA256>" `
  -CurrentExpectedSha256 "<CURRENT_APK_SHA256>"
```

执行逻辑：

1. 每轮创建唯一目录；
2. Collector 返回非零时矩阵立即停止；
3. 每轮后执行部分门禁；
4. 全部完成后执行完整门禁；
5. 不手工重建汇总字段，`summary` 保留完整 `result.json` 对象。

## 单独校验已有矩阵

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\native-crash\validate-native-diagnostics.ps1 `
  -SummaryPath "artifacts\native-crash\matrix-YYYYMMDD-HHMMSSfff\ab-matrix-summary.json" `
  -ArtifactsDir "artifacts\native-crash\matrix-YYYYMMDD-HHMMSSfff" `
  -ExpectedCombos "A0,A1,A2,A3,A4,A5,A6,A7" `
  -ExpectedRunsPerCombo 3
```

## 结果状态

| 状态 | 含义 |
|---|---|
| `PASS_TIMEOUT_ALIVE` | 原 PID、starttime、cmdline 在超时结束时仍一致 |
| `NATIVE_CRASH` | crash-buffer 或本轮 tombstone 中存在目标主 PID 的 Native 崩溃 |
| `CHILD_NATIVE_CRASH` | 精确目标子进程崩溃，主进程仍存活 |
| `JAVA_CRASH` | 目标主 PID 的 Java 崩溃 |
| `PROCESS_LOST` | 原进程消失，但没有精确崩溃证据 |
| `TARGET_NOT_STARTED` | 无法唯一绑定目标进程，Collector 返回 20 |
| `INVALID_EVIDENCE` | 命令失败、字段冲突或证据不完整，Collector 返回 30 |

## 报告绑定

报告需要写入汇总文件 SHA-256：

```text
Diagnostic-Summary-SHA256: <64位SHA256>
```

然后调用 Validator 的 `-ReportPath`。如果报告与汇总不是同一版本，或没有 C1～C3 证据却宣称 `CONFIRMED_SERVICE_ESCAPE`，门禁会失败。
