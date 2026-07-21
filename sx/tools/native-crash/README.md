# Native Crash Diagnostics Tools

This directory contains automated evidence collection and A/B matrix testing tools for diagnosing native crashes in `sx` sandbox.

## Tools Overview

### 1. `collect-native-crash.ps1`
Automated evidence collector for a single run.

#### Parameters:
- `-DeviceSerial`: ADB target device serial (default: `127.0.0.1:16384`)
- `-HostPackage`: Host application package name (default: `com.sx.app.debug`)
- `-TargetPackage`: Target application package name (default: `com.quark.browser`)
- `-LaunchTimeoutSeconds`: Monitoring duration in seconds (default: `120`)
- `-OutputRoot`: Artifact output path relative to `sx` (default: `artifacts/native-crash`)
- `-RunLabel`: Identifier label for the run (e.g. `A1_run1`)
- `-TryAdbRoot`: Attempt `adb root` to read `/data/tombstones/` (default: `$true`)
- `-GenerateBugreport`: Generate `adb bugreport` fallback if tombstone inaccessible (default: `$false`)

#### Usage Example:
```powershell
.\tools\native-crash\collect-native-crash.ps1 -RunLabel "A1_run1" -LaunchTimeoutSeconds 60
```

### 2. `run-native-ab-matrix.ps1`
Automated executor for the A0..A7 diagnostic matrix.

#### Matrix Combinations:
- **A1**: All 3 deterministic C++/JNI fixes applied + All Native Hooks enabled (Flags = 63)
- **A2**: A1 + Disable `UnixFileSystemHook` (Flags = 62)
- **A3**: A1 + Disable `VMClassLoaderHook` (Flags = 61)
- **A4**: A1 + Disable `BinderHook` (Flags = 59)
- **A5**: A1 + Disable `SpoofRuntime` / `RuntimeHook` (Flags = 55)
- **A6**: A1 + Disable All Native Hooks (Flags = 47)
- **A7**: Direct OS launch outside sandbox (Flags = 0)

#### Usage Example:
```powershell
.\tools\native-crash\run-native-ab-matrix.ps1 -RunsPerCombo 3 -LaunchTimeoutSeconds 120
```

## Collected Artifact Structure
Each run outputs to `artifacts/native-crash/<Timestamp>-<RunLabel>/`:
- `metadata.json`
- `result.json`
- `git.txt`
- `device-properties.txt`
- `abi-native-bridge.txt`
- `packages.txt`
- `host-apk-libs.txt`
- `target-apk-libs.txt`
- `process-list.txt`
- `process-status.txt`
- `cmdline.txt`
- `maps-before-crash.txt`
- `maps-at-crash.txt`
- `smaps-rollup.txt`
- `fd-list.txt`
- `mountinfo.txt`
- `logcat-all.txt`
- `logcat-crash.txt`
- `tombstone.txt`
- `dumpsys-package-host.txt`
- `dumpsys-package-target.txt`
- `dumpsys-activity.txt`
