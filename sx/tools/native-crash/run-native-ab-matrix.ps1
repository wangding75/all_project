<#
.SYNOPSIS
    A/B Matrix Runner for SX Native Crash Diagnostics (SX-EH-01R)
#>

param(
    [string]$DeviceSerial = "127.0.0.1:16384",
    [int]$LaunchTimeoutSeconds = 180,
    [int]$RunsPerCombo = 3,
    [string]$OutputRoot = "artifacts/native-crash",
    [string[]]$CombosToRun = @("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7")
)

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SxRootDir = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$CollectorScript = Join-Path $ScriptDir "collect-native-crash.ps1"
$ValidatorScript = Join-Path $ScriptDir "validate-native-diagnostics.ps1"

$OutputFullPath = Join-Path $SxRootDir $OutputRoot
if (Test-Path $OutputFullPath) {
    Get-ChildItem -Path $OutputFullPath | Where-Object { $_.Name -ne "app-debug-a0.apk" } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $OutputFullPath -Force | Out-Null
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " SX Native Crash A/B Matrix Diagnostic Suite (SX-EH-01R)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$combosDef = @{
    "A0" = @{ Flags = 63; IsA7 = $false; Desc = "Unfixed baseline (commit 5796121)" }
    "A1" = @{ Flags = 63; IsA7 = $false; Desc = "Current fixed version + All hooks enabled" }
    "A2" = @{ Flags = 62; IsA7 = $false; Desc = "Disable UnixFileSystemHook" }
    "A3" = @{ Flags = 61; IsA7 = $false; Desc = "Disable VMClassLoaderHook" }
    "A4" = @{ Flags = 59; IsA7 = $false; Desc = "Disable BinderHook" }
    "A5" = @{ Flags = 55; IsA7 = $false; Desc = "Disable SpoofRuntime" }
    "A6" = @{ Flags = 47; IsA7 = $false; Desc = "Disable Native Master Hook" }
    "A7" = @{ Flags = 0;  IsA7 = $true;  Desc = "Native OS launch outside sandbox" }
}

$matrixResults = @()

foreach ($comboKey in $CombosToRun) {
    if (-not $combosDef.ContainsKey($comboKey)) { continue }
    $cfg = $combosDef[$comboKey]

    # Ensure correct APK is installed for the combo
    if ($comboKey -eq "A0") {
        $a0Apk = Join-Path $SxRootDir "artifacts\native-crash\app-debug-a0.apk"
        if (Test-Path $a0Apk) {
            Write-Host "Installing A0 Baseline APK (commit 5796121)..." -ForegroundColor Cyan
            adb -s $DeviceSerial install -r $a0Apk | Out-Null
        }
    } elseif ($comboKey -ne "A7") {
        $currentApk = Join-Path $SxRootDir "app\build\outputs\apk\debug\app-debug.apk"
        if (Test-Path $currentApk) {
            Write-Host "Installing Current Fixed APK (branch feature/sx-native-crash-diagnostics)..." -ForegroundColor Cyan
            adb -s $DeviceSerial install -r $currentApk | Out-Null
        }
    }

    for ($run = 1; $run -le $RunsPerCombo; $run++) {
        $runLabel = "${comboKey}_run${run}"
        Write-Host "`n--- Iteration $run / $RunsPerCombo ($runLabel) ---" -ForegroundColor White

        & $CollectorScript `
            -DeviceSerial $DeviceSerial `
            -LaunchTimeoutSeconds $LaunchTimeoutSeconds `
            -OutputRoot $OutputRoot `
            -RunLabel $runLabel `
            -RequestedFlags $cfg.Flags `
            -IsA7 $cfg.IsA7 `
            -ComboName $comboKey

        # Locate result.json for this run
        $runDirs = Get-ChildItem -Path (Join-Path $SxRootDir $OutputRoot) -Directory | Where-Object { $_.Name -like "*-$runLabel" }
        if ($runDirs) {
            $resFile = Join-Path $runDirs[0].FullName "result.json"
            if (Test-Path $resFile) {
                $resObj = Get-Content $resFile -Raw | ConvertFrom-Json
                $matrixResults += [ordered]@{
                    Combo = $resObj.combo
                    RunLabel = $resObj.run_label
                    TargetStarted = $resObj.target_started
                    Status = $resObj.status
                    SurvivalSeconds = $resObj.survival_seconds
                    RequestedFlags = $resObj.requested_flags
                    AppliedFlags = $resObj.applied_flags
                    Pid = $resObj.pid
                    VirtualProcess = $resObj.virtual_process
                    Signal = $resObj.signal
                    FaultAddress = $resObj.fault_address
                    CrashLib = $resObj.crash_library
                    PCOffset = $resObj.pc_offset
                    TombstoneFile = $resObj.tombstone_file
                }
            }
        }
    }
}

# Save Summary JSON
$summaryPath = Join-Path $SxRootDir "$OutputRoot\ab-matrix-summary.json"
$matrixResults | ConvertTo-Json -Depth 5 | Set-Content $summaryPath -Encoding UTF8
Write-Host "`nSummary saved to $summaryPath" -ForegroundColor Green

# Print Output Summary Table
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " A/B Matrix Diagnostic Execution Summary" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
$matrixResults | Format-Table -Property Combo, RunLabel, TargetStarted, Status, SurvivalSeconds, RequestedFlags, AppliedFlags, Signal, CrashLib

# Run Gate 1 Integrity Validator
& $ValidatorScript -SummaryPath "$OutputRoot\ab-matrix-summary.json"
