<#
.SYNOPSIS
    Native Crash A/B Matrix Testing Executor
.DESCRIPTION
    Runs A0..A7 matrix combinations (3 iterations each) and collects evidence.
#>

param(
    [string]$DeviceSerial = "127.0.0.1:16384",
    [string]$HostPackage = "com.sx.app.debug",
    [string]$TargetPackage = "com.quark.browser",
    [int]$LaunchTimeoutSeconds = 120,
    [int]$RunsPerCombo = 3
)

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SxRootDir = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

# Ensure ADB connection
adb connect $DeviceSerial | Out-Null

$Matrix = @(
    @{ Label = "A1"; Flags = 63; Desc = "All fixes applied + All hooks enabled" },
    @{ Label = "A2"; Flags = 62; Desc = "A1 + Disable UnixFileSystemHook" },
    @{ Label = "A3"; Flags = 61; Desc = "A1 + Disable VMClassLoaderHook" },
    @{ Label = "A4"; Flags = 59; Desc = "A1 + Disable BinderHook" },
    @{ Label = "A5"; Flags = 55; Desc = "A1 + Disable SpoofRuntime Injection" },
    @{ Label = "A6"; Flags = 47; Desc = "A1 + Disable All Native Hooks" },
    @{ Label = "A7"; Flags = 0;  Desc = "Native OS launch outside sandbox" }
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " SX Native Crash A/B Matrix Diagnostic Runner" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$SummaryResults = @()

foreach ($combo in $Matrix) {
    $label = $combo.Label
    $flags = $combo.Flags
    $desc = $combo.Desc

    Write-Host "`n[>>>] Running Matrix Combo $label ($desc) - Flags: $flags" -ForegroundColor Yellow

    for ($run = 1; $run -le $RunsPerCombo; $run++) {
        $runLabel = "${label}_run${run}"
        Write-Host "`n--- Iteration $run / $RunsPerCombo ($runLabel) ---" -ForegroundColor Green

        if ($label -eq "A7") {
            # Direct system launch of target package
            adb -s $DeviceSerial shell am force-stop $TargetPackage
            Start-Sleep -Seconds 1
            adb -s $DeviceSerial shell monkey -p $TargetPackage -c android.intent.category.LAUNCHER 1
        } else {
            # Set debug native hook flags property on device
            adb -s $DeviceSerial shell setprop debug.sx.native_hook_flags "$flags"
            
            # Force stop host app and relaunch target inside sandbox
            adb -s $DeviceSerial shell am force-stop $HostPackage
            Start-Sleep -Seconds 1
            
            # Launch host main activity
            adb -s $DeviceSerial shell am start -n "$HostPackage/com.sx.app.ui.SplashActivity"
            Start-Sleep -Seconds 3
        }

        # Collect evidence
        $collectorScript = Join-Path $ScriptDir "collect-native-crash.ps1"
        & $collectorScript -DeviceSerial $DeviceSerial `
                           -HostPackage $HostPackage `
                           -TargetPackage $TargetPackage `
                           -LaunchTimeoutSeconds $LaunchTimeoutSeconds `
                           -RunLabel $runLabel `
                           -TryAdbRoot $true `
                           -GenerateBugreport $false

        # Read output result.json
        $latestArtifactDir = Get-ChildItem -Path "$SxRootDir\artifacts\native-crash" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latestArtifactDir) {
            $resultJsonPath = Join-Path $latestArtifactDir.FullName "result.json"
            if (Test-Path $resultJsonPath) {
                $resData = Get-Content $resultJsonPath -Raw | ConvertFrom-Json
                $SummaryResults += [PSCustomObject]@{
                    Combo = $label
                    Run = $run
                    Flags = $flags
                    Reproduced = $resData.reproduced
                    SurvivalSec = $resData.survival_seconds
                    Signal = $resData.signal
                    CrashLib = $resData.crash_library
                    PCOffset = $resData.pc_offset
                }
            }
        }
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " A/B Matrix Diagnostic Execution Summary" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
$SummaryResults | Format-Table -AutoSize

$SummaryPath = Join-Path $SxRootDir "artifacts\native-crash\ab-matrix-summary.json"
$SummaryResults | ConvertTo-Json -Depth 5 | Set-Content $SummaryPath -Encoding UTF8
Write-Host "Summary saved to $SummaryPath" -ForegroundColor Green
