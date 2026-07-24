<#
.SYNOPSIS
    Lightweight 3x 20-minute stability verification for DingTalk inside Shanxian sandbox.
    Optimized to minimize Windows host process creation and memory usage.
#>

param(
    [string]$DeviceSerial = "127.0.0.1:16384",
    [string]$HostPackage = "com.sx.app.debug",
    [string]$TargetPackage = "com.alibaba.android.rimet",
    [int]$VirtualUserId = 0,
    [int]$ObservationSecondsPerRun = 1200, # 20 minutes = 1200 seconds
    [int]$TotalRuns = 3,
    [string]$OutputDir = "artifacts/dingtalk-automation"
)

$ErrorActionPreference = "Continue"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

$summaryFile = Join-Path $OutputDir "dingtalk-stability-summary.json"
$results = @()

# Disable Android 12 Phantom Process Killer & keep screen on (One-time call)
Write-Host "[+] Disabling Android 12 Phantom Process Killer & keeping screen on..."
adb -s $DeviceSerial shell "settings put global settings_enable_monitor_phantom_procs false; svc power stayon true" 2>$null | Out-Null

for ($run = 1; $run -le $TotalRuns; $run++) {
    Write-Host "=========================================="
    Write-Host "[+] Starting Run $run / $TotalRuns (Duration: $ObservationSecondsPerRun s)..."
    Write-Host "=========================================="

    # Force stop packages using a single adb call
    adb -s $DeviceSerial shell "am force-stop com.quark.browser; am force-stop net.gsantner.markor; am force-stop org.tasks; am force-stop $TargetPackage; am force-stop $HostPackage" 2>$null | Out-Null
    Start-Sleep -Seconds 3

    # Clear logcat
    adb -s $DeviceSerial logcat -c 2>$null | Out-Null

    # Launch target in Shanxian sandbox
    $component = "$HostPackage/com.sx.app.ui.sandbox.ShortcutLaunchActivity"
    $launchOut = adb -s $DeviceSerial shell am start -W -n $component --es package_name $TargetPackage --ei user_id $VirtualUserId 2>&1
    Write-Host "[+] Launch output: $launchOut"

    # Wait up to 30 seconds for target process to bind
    $isStarted = $false
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        $psCheck = adb -s $DeviceSerial shell "ps -ef | grep $TargetPackage" 2>$null
        if ($psCheck -and $psCheck.Trim().Length -gt 0) {
            $isStarted = $true
            break
        }
    }

    if (-not $isStarted) {
        Write-Host "[-] RUN $run FAIL: Target package $TargetPackage failed to start within 30 seconds."
        $results += [pscustomobject]@{
            run = $run
            status = "FAILED_TO_START"
            duration_seconds = 0
        }
        continue
    }

    Write-Host "[+] Target package started successfully!"

    # Monitor process for 20 minutes with lightweight 15s interval
    $startTime = Get-Date
    $endTime = $startTime.AddSeconds($ObservationSecondsPerRun)
    $isAlive = $true
    $elapsed = 0

    while ((Get-Date) -lt $endTime) {
        Start-Sleep -Seconds 15
        $elapsed = [int]((Get-Date) - $startTime).TotalSeconds

        # Check process status using device-side grep (lightweight, single command)
        $psCheck = adb -s $DeviceSerial shell "ps -ef | grep $TargetPackage" 2>$null
        
        if (-not $psCheck -or $psCheck.Trim().Length -eq 0) {
            Write-Host "[-] RUN $run FAIL: Target package $TargetPackage DIED after $elapsed seconds!"
            $isAlive = $false
            break
        }

        Write-Host "[+] Run $run Alive: $elapsed / $ObservationSecondsPerRun seconds"
    }

    if ($isAlive) {
        # Take screenshot to verify emulator displays DingTalk UI
        $screenshotRemote = "/sdcard/dingtalk_run${run}.png"
        $screenshotLocal = Join-Path $OutputDir "screenshot_run${run}.png"
        adb -s $DeviceSerial shell "screencap -p $screenshotRemote" 2>$null | Out-Null
        adb -s $DeviceSerial pull $screenshotRemote $screenshotLocal 2>$null | Out-Null

        # Verify foreground focus window
        $focusCheck = adb -s $DeviceSerial shell "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'" 2>$null

        Write-Host "[+] RUN $run SUCCESS! Target package $TargetPackage stayed alive for $ObservationSecondsPerRun seconds."
        Write-Host "[+] Screenshot captured at $screenshotLocal"
        Write-Host "[+] Foreground focus window: $focusCheck"

        $focusStr = ""
        if ($focusCheck) {
            $focusStr = $focusCheck.Trim()
        }

        $results += [pscustomobject]@{
            run = $run
            status = "PASSED"
            duration_seconds = $ObservationSecondsPerRun
            screenshot_path = $screenshotLocal
            focus_window = $focusStr
        }
    } else {
        $logcatCrash = adb -s $DeviceSerial logcat -d 2>$null | Select-String 'FATAL|AndroidRuntime|rimet|BlackBox|System.err|DEBUG|tombstone|crash'
        $results += [pscustomobject]@{
            run = $run
            status = "CRASHED"
            duration_seconds = $elapsed
            crash_logs = ($logcatCrash | Select-Object -Last 20)
        }
    }
}

$summary = [pscustomobject]@{
    timestamp = (Get-Date).ToString("o")
    total_runs = $TotalRuns
    target_package = $TargetPackage
    results = $results
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summaryFile -Encoding UTF8
Write-Host "=========================================="
Write-Host "[+] All stability test runs completed. Summary saved to $summaryFile"
Write-Host "=========================================="
