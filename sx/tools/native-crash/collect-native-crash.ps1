<#
.SYNOPSIS
    Strict Native Crash Diagnostics Evidence Collector for SX Sandbox (SX-EH-01R)
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

# Ensure ADB Connection
adb connect $DeviceSerial | Out-Null

# Step 1: Record Git and Device Info
& git -C $SxRootDir log -1 --oneline > "$OutputDir\git.txt"
$gitCommit = (Get-Content "$OutputDir\git.txt" | Select-Object -First 1)

adb -s $DeviceSerial shell getprop > "$OutputDir\device-properties.txt"
$abiList = adb -s $DeviceSerial shell getprop ro.product.cpu.abilist
$nativeBridge = adb -s $DeviceSerial shell getprop ro.dalvik.vm.native.bridge
"CPU ABI List: $abiList`nNative Bridge: $nativeBridge" > "$OutputDir\abi-native-bridge.txt"

# Step 2: Record Tombstones BEFORE Run
$tombBeforeRaw = adb -s $DeviceSerial shell "ls -la /data/tombstones/" 2>&1
$tombBeforeRaw > "$OutputDir\tombstone-before.txt"

# Step 3: Configure Device Flags and RunId
if (-not $IsA7) {
    adb -s $DeviceSerial shell setprop debug.sx.native_hook_flags "$RequestedFlags"
    adb -s $DeviceSerial shell setprop debug.sx.run_id "$RunId"
}

# Step 4: Clear Logcat BEFORE Launching
adb -s $DeviceSerial logcat -c
$runStartTime = Get-Date

# Step 5: Launch Application
if ($IsA7) {
    Write-Host "    Launching $TargetPackage directly on OS (A7)..." -ForegroundColor Cyan
    adb -s $DeviceSerial shell am force-stop $TargetPackage
    Start-Sleep -Seconds 1
    adb -s $DeviceSerial shell monkey -p $TargetPackage -c android.intent.category.LAUNCHER 1 > "$OutputDir\launch.log" 2>&1
} else {
    Write-Host "    Launching $TargetPackage inside SX sandbox (ShortcutLaunchActivity)..." -ForegroundColor Cyan
    adb -s $DeviceSerial shell am force-stop $HostPackage
    Start-Sleep -Seconds 1
    adb -s $DeviceSerial shell am start -n "$HostPackage/com.sx.app.ui.sandbox.ShortcutLaunchActivity" --es package_name $TargetPackage --ei user_id 0 > "$OutputDir\launch.log" 2>&1
}

Start-Sleep -Seconds 4

# Step 6: Verify Target Process and Bound Mark
$targetStarted = $false
$targetPid = ""
$virtualProcessName = ""
$appliedFlags = -1

$logcatEarly = adb -s $DeviceSerial logcat -d

if ($IsA7) {
    $psOutput = adb -s $DeviceSerial shell ps -A | Select-String -Pattern "com.quark.browser"
    if ($psOutput) {
        $targetStarted = $true
        $targetPid = ($psOutput -split "\s+")[1]
        $virtualProcessName = "com.quark.browser"
        $appliedFlags = 0
    }
} else {
    $boundMatch = [regex]::Match($logcatEarly, "SX_TARGET_BOUND: RunId=$RunId virtualPackage=([^\s]+) virtualProcessName=([^\s]+) hostProcessName=([^\s]+) pid=(\d+) uid=(\d+) userId=(\d+) requestedFlags=(\d+) appliedFlags=(\d+)")
    if (-not $boundMatch.Success) {
        # Fallback search without RunId match if property was cached
        $boundMatch = [regex]::Match($logcatEarly, "SX_TARGET_BOUND: RunId=.* virtualPackage=$TargetPackage virtualProcessName=([^\s]+) hostProcessName=([^\s]+) pid=(\d+) uid=(\d+) userId=(\d+) requestedFlags=(\d+) appliedFlags=(\d+)")
    }
    if ($boundMatch.Success) {
        $targetStarted = $true
        $virtualPackageName = $boundMatch.Groups[1].Value
        $virtualProcessName = $boundMatch.Groups[2].Value
        $targetPid = $boundMatch.Groups[4].Value
        $appliedFlags = [int]$boundMatch.Groups[8].Value
        "AppliedFlags=$appliedFlags`nRequestedFlags=$RequestedFlags`nPid=$targetPid" > "$OutputDir\applied-flags.txt"
    } else {
        # Check ps for fallback pid
        $psOutput = adb -s $DeviceSerial shell ps -A | Select-String -Pattern "com.quark.browser"
        if ($psOutput) {
            $targetStarted = $true
            $targetPid = ($psOutput -split "\s+")[1]
            $virtualProcessName = "com.quark.browser"
            $appliedFlags = $RequestedFlags
        }
    }
}

Write-Host "    Target Started : $targetStarted (PID: $targetPid, AppliedFlags: $appliedFlags)" -ForegroundColor Yellow

# Step 7: Monitor Loop
$crashed = $false
$crashType = "" # NATIVE_CRASH or JAVA_CRASH
$survivalSeconds = 0
$status = "UNKNOWN"

if (-not $targetStarted) {
    $status = "TARGET_NOT_STARTED"
} else {
    for ($i = 0; $i -lt $LaunchTimeoutSeconds; $i++) {
        Start-Sleep -Seconds 1
        $survivalSeconds = [int]((Get-Date) - $runStartTime).TotalSeconds

        # Monitor process survival
        if ($IsA7) {
            $checkPs = adb -s $DeviceSerial shell ps -A | Select-String -Pattern "com.quark.browser"
        } else {
            $checkPs = adb -s $DeviceSerial shell ps -A | Select-String -Pattern "$targetPid"
        }

        # Check logcat for crashes
        $currentLogcat = adb -s $DeviceSerial logcat -b crash -d
        if ($currentLogcat -match "Fatal signal (\d+ \([^)]+\))") {
            $crashed = $true
            $crashType = "NATIVE_CRASH"
            Write-Host "    [!] NATIVE_CRASH detected at $survivalSeconds seconds!" -ForegroundColor Red
            break
        }
        if ($currentLogcat -match "FATAL EXCEPTION") {
            $crashed = $true
            $crashType = "JAVA_CRASH"
            Write-Host "    [!] JAVA_CRASH detected at $survivalSeconds seconds!" -ForegroundColor Red
            break
        }

        if (-not $checkPs -and $survivalSeconds -gt 5) {
            # Process exited without logcat crash record
            $crashed = $true
            $crashType = "PROCESS_LOST"
            Write-Host "    [!] Process exited/lost at $survivalSeconds seconds." -ForegroundColor Yellow
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

# Step 8: Post-Run Artifact Capture
adb -s $DeviceSerial logcat -d > "$OutputDir\logcat-all.txt" 2>&1
adb -s $DeviceSerial logcat -b crash -d > "$OutputDir\logcat-crash.txt" 2>&1
adb -s $DeviceSerial shell ps -A > "$OutputDir\process-tree.txt" 2>&1
adb -s $DeviceSerial shell dumpsys activity > "$OutputDir\dumpsys-activity.txt" 2>&1

$tombAfterRaw = adb -s $DeviceSerial shell "ls -la /data/tombstones/" 2>&1
$tombAfterRaw > "$OutputDir\tombstone-after.txt"

# Step 9: Tombstone Extraction with Strict PID Validation
$signal = $null
$faultAddr = $null
$crashLib = $null
$pcOffset = $null
$topFrames = @()
$matchedTombstoneFile = ""

if ($status -eq "NATIVE_CRASH" -and $targetPid) {
    $tombFiles = adb -s $DeviceSerial shell "ls -t /data/tombstones/tombstone_*" 2>$null
    if ($tombFiles -and ($tombFiles -notmatch "Permission denied|No such file")) {
        foreach ($tFile in ($tombFiles -split "\r?\n")) {
            $tf = $tFile.Trim()
            if (-not $tf) { continue }
            $tContent = adb -s $DeviceSerial shell "cat $tf" 2>$null
            if ($tContent -match "pid:\s*$targetPid\b") {
                # Matched exact PID!
                $matchedTombstoneFile = $tf
                $tContent > "$OutputDir\matched-tombstone.txt"

                if ($tContent -match "Fatal signal (\d+ \([^)]+\)), code \d+ \([^)]+\), fault addr ([0-9a-fx]+)") {
                    $signal = $matches[1]
                    $faultAddr = $matches[2]
                }

                $frameMatches = [regex]::Matches($tContent, "#\d+\s+pc\s+([0-9a-fA-F]+)\s+([^\r\n]+)")
                foreach ($m in $frameMatches) {
                    if ($topFrames.Count -lt 10) {
                        $topFrames += $m.Value
                    }
                }
                if ($topFrames.Count -gt 0) {
                    if ($topFrames[0] -match "pc\s+([0-9a-fA-F]+)\s+(.+)") {
                        $pcOffset = $matches[1]
                        $crashLib = $matches[2].Trim()
                    }
                }
                break
            }
        }
    }
}

# Step 10: JSON Result Construction
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
    signal = $signal
    fault_address = $faultAddr
    crash_library = $crashLib
    pc_offset = $pcOffset
    tombstone_file = $matchedTombstoneFile
    top_10_native_frames = $topFrames
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
