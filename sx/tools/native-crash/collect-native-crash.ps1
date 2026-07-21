<#
.SYNOPSIS
    Strict Native Crash Evidence Collector for SX Sandbox (SX-EH-02)
#>

param(
    [string]$DeviceSerial = "127.0.0.1:16384",
    [string]$HostPackage = "com.sx.app.debug",
    [string]$TargetPackage = "com.quark.browser",
    [int]$LaunchTimeoutSeconds = 180,
    [string]$OutputRoot = "artifacts/native-crash",
    [string]$RunLabel = "A1_run1",
    [int]$RequestedFlags = 63,
    [bool]$IsA7 = $false,
    [string]$ComboName = "A1"
)

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SxRootDir = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$RunId = "$Timestamp-$RunLabel"
$OutputDir = Join-Path $SxRootDir "$OutputRoot\$RunId"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "[*] Starting Collector for $RunLabel (Combo: $ComboName)..." -ForegroundColor Green

adb connect $DeviceSerial | Out-Null

# 1. Record Git & Device Info
& git -C $SxRootDir log -1 --oneline > "$OutputDir\git.txt"
$gitCommit = (Get-Content "$OutputDir\git.txt" | Select-Object -First 1)

$hostUidRaw = adb -s $DeviceSerial shell "pm list packages -U | grep $HostPackage"
$hostUid = if ($hostUidRaw -match "uid:(\d+)") { $matches[1] } else { "" }

adb -s $DeviceSerial shell getprop > "$OutputDir\device-properties.txt"
$abiList = adb -s $DeviceSerial shell getprop ro.product.cpu.abilist
$nativeBridge = adb -s $DeviceSerial shell getprop ro.dalvik.vm.native.bridge

# 2. Record Pre-run Tombstone List
adb -s $DeviceSerial shell "ls -la /data/tombstones/" > "$OutputDir\tombstone-before.txt" 2>&1

# 3. Configure Flags
if (-not $IsA7) {
    adb -s $DeviceSerial shell setprop debug.sx.native_hook_flags "$RequestedFlags"
    adb -s $DeviceSerial shell setprop debug.sx.run_id "$RunId"
}

# 4. Clear Logcat BEFORE Launch
adb -s $DeviceSerial logcat -c
$runStartTime = Get-Date

# 5. Launch Target
if ($IsA7) {
    Write-Host "    Launching $TargetPackage directly on OS (A7)..." -ForegroundColor Cyan
    adb -s $DeviceSerial shell am force-stop $TargetPackage
    Start-Sleep -Seconds 1
    adb -s $DeviceSerial shell monkey -p $TargetPackage -c android.intent.category.LAUNCHER 1 > "$OutputDir\launch.log" 2>&1
} else {
    Write-Host "    Launching $TargetPackage inside SX sandbox..." -ForegroundColor Cyan
    adb -s $DeviceSerial shell am force-stop $HostPackage
    Start-Sleep -Seconds 1
    adb -s $DeviceSerial shell am start -n "$HostPackage/com.sx.app.ui.sandbox.ShortcutLaunchActivity" --es package_name $TargetPackage --ei user_id 0 > "$OutputDir\launch.log" 2>&1
}

Start-Sleep -Seconds 4

# 6. Verify Target Main Process Binding Strictly
$targetStarted = $false
$targetPid = ""
$virtualProcessName = ""
$appliedFlags = -1
$initialStartTime = ""

$logcatEarly = adb -s $DeviceSerial logcat -d

if ($IsA7) {
    $psOutput = adb -s $DeviceSerial shell "ps -A | grep 'com.quark.browser$'"
    if ($psOutput) {
        $parts = $psOutput -split "\s+"
        $targetStarted = $true
        $targetPid = $parts[1]
        $virtualProcessName = "com.quark.browser"
        $appliedFlags = 0
    }
} else {
    # Strict matching of SX_TARGET_BOUND for main process
    $boundMatch = [regex]::Match($logcatEarly, "SX_TARGET_BOUND: RunId=$RunId virtualPackage=$TargetPackage virtualProcessName=$TargetPackage hostProcessName=([^\s]+) pid=(\d+) uid=(\d+) userId=0 requestedFlags=(\d+) appliedFlags=(\d+)")
    if ($boundMatch.Success) {
        $targetStarted = $true
        $virtualProcessName = $TargetPackage
        $targetPid = $boundMatch.Groups[2].Value
        $appliedFlags = [int]$boundMatch.Groups[5].Value
        "AppliedFlags=$appliedFlags`nRequestedFlags=$RequestedFlags`nPid=$targetPid" > "$OutputDir\applied-flags.txt"
    }
}

if ($targetStarted -and $targetPid) {
    $statOutput = adb -s $DeviceSerial shell "cat /proc/$targetPid/stat 2>/dev/null"
    if ($statOutput) {
        $statParts = $statOutput -split "\s+"
        if ($statParts.Count -gt 21) {
            $initialStartTime = $statParts[21]
        }
    }
}

Write-Host "    Target Main Process Started: $targetStarted (PID: $targetPid, StartTime: $initialStartTime, AppliedFlags: $appliedFlags)" -ForegroundColor Yellow

# 7. Monitor Execution Loop
$crashed = $false
$crashType = ""
$survivalSeconds = 0
$status = "UNKNOWN"

if (-not $targetStarted) {
    $status = "TARGET_NOT_STARTED"
} else {
    for ($i = 0; $i -lt $LaunchTimeoutSeconds; $i++) {
        Start-Sleep -Seconds 1
        $survivalSeconds = [int]((Get-Date) - $runStartTime).TotalSeconds

        # Strict Process Survival Check
        $statCheck = adb -s $DeviceSerial shell "cat /proc/$targetPid/stat 2>/dev/null"
        $cmdCheck = adb -s $DeviceSerial shell "cat /proc/$targetPid/cmdline 2>/dev/null"
        
        $isAlive = $false
        if ($statCheck -and $cmdCheck -match "com.quark.browser") {
            $currentParts = $statCheck -split "\s+"
            if ($currentParts.Count -gt 21 -and $currentParts[21] -eq $initialStartTime) {
                $isAlive = $true
            }
        }

        # Strict Logcat Crash Check for exact target PID
        $currentLogcat = adb -s $DeviceSerial logcat -b crash -d
        if ($currentLogcat -match "Fatal signal.*pid\s+$targetPid\b|Fatal signal.*>>> $TargetPackage <<<") {
            $crashed = $true
            $crashType = "NATIVE_CRASH"
            Write-Host "    [!] NATIVE_CRASH confirmed for PID $targetPid at $survivalSeconds seconds!" -ForegroundColor Red
            break
        }
        if ($currentLogcat -match "FATAL EXCEPTION.*pid\s+$targetPid\b") {
            $crashed = $true
            $crashType = "JAVA_CRASH"
            Write-Host "    [!] JAVA_CRASH confirmed for PID $targetPid at $survivalSeconds seconds!" -ForegroundColor Red
            break
        }

        if (-not $isAlive -and $survivalSeconds -gt 5) {
            $crashed = $true
            $crashType = "PROCESS_LOST"
            Write-Host "    [!] Main process $targetPid exited/lost at $survivalSeconds seconds." -ForegroundColor Yellow
            break
        }
    }

    if (-not $crashed) {
        $status = "PASS_TIMEOUT_ALIVE"
    } else {
        if ($crashType -eq "NATIVE_CRASH") {
            $status = "NATIVE_CRASH"
        } elseif ($crashType -eq "JAVA_CRASH") {
            $status = "JAVA_CRASH"
        } else {
            $status = "PROCESS_LOST"
        }
    }
}

$runEndTime = Get-Date

# 8. Post-run Artifact Capture
adb -s $DeviceSerial logcat -d > "$OutputDir\logcat-all.txt" 2>&1
adb -s $DeviceSerial logcat -b crash -d > "$OutputDir\logcat-crash.txt" 2>&1
adb -s $DeviceSerial shell ps -A > "$OutputDir\process-tree.txt" 2>&1
adb -s $DeviceSerial shell dumpsys activity > "$OutputDir\dumpsys-activity.txt" 2>&1
adb -s $DeviceSerial shell "ls -la /data/tombstones/" > "$OutputDir\tombstone-after.txt" 2>&1

# 9. Guest & Host Tombstone Separation
$guestAbi = $null
$guestSignal = $null
$guestThread = $null
$guestPc = $null
$guestModule = $null
$guestModuleOffset = $null
$guestBuildId = $null

$hostAbi = $null
$hostPc = $null
$hostModule = $null
$hostFunction = $null
$hostBuildId = $null
$matchedTombstoneFile = ""

if ($status -eq "NATIVE_CRASH" -and $targetPid) {
    $tombFiles = adb -s $DeviceSerial shell "ls -t /data/tombstones/tombstone_*" 2>$null
    if ($tombFiles -and ($tombFiles -notmatch "Permission denied|No such file")) {
        foreach ($tFile in ($tombFiles -split "\r?\n")) {
            $tf = $tFile.Trim()
            if (-not $tf) { continue }
            $tContent = adb -s $DeviceSerial shell "cat $tf" 2>$null
            if ($tContent -match "pid:\s*$targetPid\b") {
                $matchedTombstoneFile = $tf
                $tContent > "$OutputDir\matched-tombstone.txt"

                if ($tContent -match "ABI:\s*'([^']+)'") {
                    $hostAbi = $matches[1]
                }
                if ($tContent -match "signal\s+\d+\s+\(([^)]+)\)") {
                    $guestSignal = $matches[1]
                }
                if ($tContent -match "name:\s*([^\s]+)\s+>>>\s*com\.quark\.browser\s*<<<") {
                    $guestThread = $matches[1]
                }

                $frameMatches = [regex]::Matches($tContent, "#\d+\s+pc\s+([0-9a-fA-F]+)\s+([^\r\n]+)")
                if ($frameMatches.Count -gt 0) {
                    $firstFrame = $frameMatches[0].Value
                    if ($firstFrame -match "pc\s+([0-9a-fA-F]+)\s+([^(]+)(\([^)]+\))?") {
                        $hostPc = $matches[1]
                        $modStr = $matches[2].Trim()
                        if ($modStr.Length -gt 500) { $modStr = $modStr.Substring(0, 500) }
                        $hostModule = $modStr
                        if ($matches.Count -ge 4) { $hostFunction = $matches[3] }
                    }
                }
                break
            }
        }
    }
}

# 10. Result JSON Output
$resultObj = [ordered]@{
    commit = $gitCommit
    run_id = $RunId
    combo = $ComboName
    run_label = $RunLabel
    target_started = $targetStarted
    status = $status
    survival_seconds = $survivalSeconds
    requested_flags = $RequestedFlags
    applied_flags = $appliedFlags
    pid = $targetPid
    virtual_process = $virtualProcessName
    guest_abi = "ARM64"
    guest_signal = $guestSignal
    guest_thread = $guestThread
    guest_pc = $guestPc
    guest_module = $guestModule
    guest_module_offset = $guestModuleOffset
    guest_build_id = $guestBuildId
    host_abi = $hostAbi
    host_pc = $hostPc
    host_module = $hostModule
    host_function = $hostFunction
    host_build_id = $hostBuildId
    tombstone_file = $matchedTombstoneFile
}

$metadataObj = [ordered]@{
    run_id = $RunId
    combo = $ComboName
    run_label = $RunLabel
    commit = $gitCommit
    device_serial = $DeviceSerial
    host_package = $HostPackage
    target_package = $TargetPackage
    start_time = $runStartTime.ToString("yyyy-MM-dd HH:mm:ss")
    end_time = $runEndTime.ToString("yyyy-MM-dd HH:mm:ss")
    cpu_abi_list = $abiList
    native_bridge = $nativeBridge
}

$metadataObj | ConvertTo-Json -Depth 5 | Set-Content "$OutputDir\metadata.json" -Encoding UTF8
$resultObj | ConvertTo-Json -Depth 5 | Set-Content "$OutputDir\result.json" -Encoding UTF8

Write-Host "    Completed $RunLabel - Status: $status (Survival: ${survivalSeconds}s)" -ForegroundColor Green
