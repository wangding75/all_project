# SX Quark automation scripts v2

## v2 correction

- Install into `tools/quark-automation`, isolated from legacy `tools/native-crash` scripts.
- The parser gate validates an exact seven-script package manifest.
- Unrelated scripts such as legacy `generate-report.ps1` are reported and ignored.
- No legacy script is deleted or modified.

# SX Quark automated diagnostics

This package reuses the evidence-gated native diagnostic scripts whose parser and 19 fixture cases were already run successfully under Windows PowerShell, then adds a Quark-specific driver and deterministic summarizer.

## Scenarios

- **Q0 / A7:** system-direct Quark, 1 run, 180 seconds by default.
- **Q1 / A1:** Quark inside SX with flags 63, 3 runs by default.
- **Q2 / A6:** Quark inside SX with flags 47, 3 runs by default.
- **Q3:** automatic extraction of service-route, process, crash, Native Bridge, mmap/ashmem and UC renderer evidence from Q0-Q2 artifacts.

The scripts do not automatically claim a root cause and do not modify project source code.

## Files

- `collect-native-crash.ps1`: one evidence-bound run.
- `run-native-ab-matrix.ps1`: fail-fast matrix runner and validator integration.
- `validate-native-diagnostics.ps1`: evidence consistency gate.
- `test-gate1-fixtures.ps1`: 3 positive and 16 negative fixtures.
- `test-quark-automation-scripts.ps1`: PowerShell parser gate for the package.
- `run-quark-diagnostics.ps1`: Q0-Q3 Quark automation driver.
- `summarize-quark-diagnostics.ps1`: JSON/Markdown deterministic summary.

## Installation

Extract the package, then copy all `.ps1` files to:

```text
tools/quark-automation/
```

Run commands from the `sx` repository root.

## 1. Syntax and fixture self-test

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\quark-automation\test-quark-automation-scripts.ps1
```

Expected key output:

```text
[+] PowerShell parser and automatic-variable preflight passed for 7 package scripts.
[+] All 19 fixture cases passed.
[+] Quark automation script gate passed.
```

## 2. Confirm the emulator serial

```powershell
adb devices -l
```

Use the serial shown as `device`. Do not guess the MuMu port.

## 3. Build the current SX APK

```powershell
.\gradlew.bat :app:assembleDebug
```

Default APK path:

```text
app/build/outputs/apk/debug/app-debug.apk
```

## 4. Run the complete Quark automation

Example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\quark-automation\run-quark-diagnostics.ps1 `
  -DeviceSerial "127.0.0.1:16384" `
  -HostPackage "com.sx.app.debug" `
  -TargetPackage "com.quark.browser" `
  -VirtualUserId 0 `
  -ObservationSeconds 180 `
  -SandboxRuns 3
```

The driver stops immediately if syntax, fixtures, device binding, target binding, flags, collector evidence, or validator evidence fails.

## 5. Outputs

A new session is created under:

```text
artifacts/quark-automation/quark-session-<timestamp>/
```

Important files:

- `session-manifest.json`
- `quark-diagnostic-summary.json`
- `quark-diagnostic-summary.md`
- Q0/Q1/Q2 matrix directories
- each run's `result.json`
- `logcat-all.txt`, `logcat-crash.txt`
- `process-before.txt`, `process-after.txt`
- `maps-after.txt`, `fd-list.txt`, `mountinfo.txt`
- tombstone before/after evidence
- `quark-route-evidence.txt`

## Boundary

A successful run proves only that the artifacts are internally consistent. The automatic summary always uses:

```text
EVIDENCE_ONLY_ROOT_CAUSE_NOT_AUTO_CONFIRMED
```

Root-cause confirmation requires reviewing exact process, service-route and crash evidence.
