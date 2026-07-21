<#
.SYNOPSIS
    Native Crash Diagnostics Evidence Collector for SX Sandbox
.DESCRIPTION
    Collects runtime evidence, tombstones, maps, logcat, process state, and symbolicated stack traces.
#>

param(
    [string]$DeviceSerial = "127.0.0.1:16384",
    [string]$HostPackage = "com.sx.app.debug",
    [string]$TargetPackage = "com.quark.browser",
    [int]$LaunchTimeoutSeconds = 120,
    [string]$OutputRoot = "artifacts/native-crash",
    [string]$RunLabel = "A0",
    [bool]$TryAdbRoot = $true,
    [bool]$GenerateBugreport = $false
)

$ErrorActionPreference = "Continue"

# 1. Locate sx root directory automatically
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SxRootDir = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$OutputDir = Join-Path $SxRootDir "$OutputRoot\$Timestamp-$RunLabel"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "[*] SX Native Crash Collector starting..." -ForegroundColor Green
Write-Host "    SX Root    : $SxRootDir"
Write-Host "    Output Dir : $OutputDir"
Write-Host "    Device     : $DeviceSerial"
Write-Host "    Run Label  : $RunLabel"

# Ensure ADB connection
adb connect $DeviceSerial | Out-Null

# 2. Collect Environment Metadata
Write-Host "[*] Collecting git, device, package, and lib metadata..." -ForegroundColor Cyan

# git.txt
& git -C $SxRootDir log -1 --oneline > "$OutputDir\git.txt"
& git -C $SxRootDir status --short >> "$OutputDir\git.txt"

# device-properties.txt
adb -s $DeviceSerial shell getprop > "$OutputDir\device-properties.txt"

# abi-native-bridge.txt
$abiList = adb -s $DeviceSerial shell getprop ro.product.cpu.abilist
$nativeBridge = adb -s $DeviceSerial shell getprop ro.dalvik.vm.native.bridge
"CPU ABI List: $abiList`nNative Bridge: $nativeBridge" > "$OutputDir\abi-native-bridge.txt"

# packages.txt
adb -s $DeviceSerial shell pm list packages > "$OutputDir\packages.txt"

# host-apk-libs.txt
$hostPath = (adb -s $DeviceSerial shell pm path $HostPackage) -replace "^package:", ""
if ($hostPath) {
    $hostLibDir = ($hostPath.Trim() -replace "/base\.apk$", "") + "/lib"
    adb -s $DeviceSerial shell "ls -laR $hostLibDir" > "$OutputDir\host-apk-libs.txt" 2>&1
} else {
    "Host package $HostPackage not found" > "$OutputDir\host-apk-libs.txt"
}

# target-apk-libs.txt
$targetPath = (adb -s $DeviceSerial shell pm path $TargetPackage) -replace "^package:", ""
if ($targetPath) {
    $targetLibDir = ($targetPath.Trim() -replace "/base\.apk$", "") + "/lib"
    adb -s $DeviceSerial shell "ls -laR $targetLibDir" > "$OutputDir\target-apk-libs.txt" 2>&1
} else {
    "Target package $TargetPackage not found" > "$OutputDir\target-apk-libs.txt"
}

# dumpsys package
adb -s $DeviceSerial shell dumpsys package $HostPackage > "$OutputDir\dumpsys-package-host.txt" 2>&1
adb -s $DeviceSerial shell dumpsys package $TargetPackage > "$OutputDir\dumpsys-package-target.txt" 2>&1
adb -s $DeviceSerial shell dumpsys activity > "$OutputDir\dumpsys-activity.txt" 2>&1

# 3. Clear Logcat and Monitor Runtime Execution
Write-Host "[*] Clearing logcat and monitoring execution ($LaunchTimeoutSeconds seconds)..." -ForegroundColor Cyan
adb -s $DeviceSerial logcat -c

$startTime = Get-Date

# Find initial process list
adb -s $DeviceSerial shell ps -A > "$OutputDir\process-list.txt"

# Try getting maps before crash if process is running
$targetPids = adb -s $DeviceSerial shell "ps -A | grep $HostPackage | grep -v grep | awk '{print `$2}'"
if ($targetPids) {
    $pid1 = ($targetPids -split "\r?\n")[0].Trim()
    if ($pid1) {
        adb -s $DeviceSerial shell "cat /proc/$pid1/maps" > "$OutputDir\maps-before-crash.txt" 2>&1
    }
}

# Monitor execution
$crashed = $false
$survivalSeconds = 0
$crashThread = ""
$signal = ""
$faultAddr = ""
$crashLib = ""
$pcOffset = ""
$topFrames = @()

for ($i = 0; $i -lt $LaunchTimeoutSeconds; $i++) {
    Start-Sleep -Seconds 1
    $elapsed = [int]((Get-Date) - $startTime).TotalSeconds
    $survivalSeconds = $elapsed

    # Check if host process or crashed thread appeared in logcat crash buffer
    $crashLog = adb -s $DeviceSerial logcat -b crash -d
    if ($crashLog -match "FATAL EXCEPTION|SIGSEGV|SIGABRT|backtrace:") {
        $crashed = $true
        Write-Host "[!] Native crash detected at $elapsed seconds!" -ForegroundColor Red
        break
    }

    # Check if process unexpectedly died
    $currentPids = adb -s $DeviceSerial shell "ps -A | grep $HostPackage | grep -v grep | awk '{print `$2}'"
    if (-not $currentPids -and $elapsed -gt 5) {
        # Process exited
        $crashed = $true
        Write-Host "[!] Host process exited after $elapsed seconds." -ForegroundColor Yellow
        break
    }
}

$endTime = Get-Date

# 4. Post-Crash Evidence Capture
Write-Host "[*] Capturing post-crash diagnostic data..." -ForegroundColor Cyan

# logcat
adb -s $DeviceSerial logcat -d > "$OutputDir\logcat-all.txt" 2>&1
adb -s $DeviceSerial logcat -b crash -d > "$OutputDir\logcat-crash.txt" 2>&1

# process status & cmdline & mountinfo & fds
$finalPids = adb -s $DeviceSerial shell "ps -A | grep $HostPackage | grep -v grep | awk '{print `$2}'"
if ($finalPids) {
    $fpid = ($finalPids -split "\r?\n")[0].Trim()
    if ($fpid) {
        adb -s $DeviceSerial shell "cat /proc/$fpid/status" > "$OutputDir\process-status.txt" 2>&1
        adb -s $DeviceSerial shell "cat /proc/$fpid/cmdline" > "$OutputDir\cmdline.txt" 2>&1
        adb -s $DeviceSerial shell "cat /proc/$fpid/maps" > "$OutputDir\maps-at-crash.txt" 2>&1
        adb -s $DeviceSerial shell "cat /proc/$fpid/smaps_rollup" > "$OutputDir\smaps-rollup.txt" 2>&1
        adb -s $DeviceSerial shell "ls -l /proc/$fpid/fd" > "$OutputDir\fd-list.txt" 2>&1
        adb -s $DeviceSerial shell "cat /proc/$fpid/mountinfo" > "$OutputDir\mountinfo.txt" 2>&1
    }
}

# 5. Tombstone Extraction & Parsing
Write-Host "[*] Extracting Tombstone..." -ForegroundColor Cyan

$tombstonePath = "$OutputDir\tombstone.txt"
$tombstoneExtracted = $false

if ($TryAdbRoot) {
    adb -s $DeviceSerial root | Out-Null
    Start-Sleep -Seconds 2
    adb connect $DeviceSerial | Out-Null
}

# Attempt direct pull from /data/tombstones
$tombList = adb -s $DeviceSerial shell "ls -t /data/tombstones/tombstone_*" 2>$null
if ($tombList -and ($tombList -notmatch "Permission denied|No such file")) {
    $latestTomb = ($tombList -split "\r?\n")[0].Trim()
    if ($latestTomb) {
        adb -s $DeviceSerial shell "cat $latestTomb" > $tombstonePath 2>&1
        $tombstoneExtracted = $true
        Write-Host "    Extracted tombstone from $latestTomb" -ForegroundColor Green
    }
}

if (-not $tombstoneExtracted -and $GenerateBugreport) {
    Write-Host "    Generating adb bugreport..." -ForegroundColor Yellow
    $bugZip = "$OutputDir\bugreport.zip"
    adb -s $DeviceSerial bugreport $bugZip | Out-Null
    if (Test-Path $bugZip) {
        # Extract tombstone from zip if possible
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($bugZip)
        $tombEntry = $zip.Entries | Where-Object { $_.FullName -like "*tombstone*" } | Select-Object -First 1
        if ($tombEntry) {
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($tombEntry, $tombstonePath, $true)
            $tombstoneExtracted = $true
        }
        $zip.Dispose()
    }
}

if (-not $tombstoneExtracted) {
    # Fallback to logcat-crash
    Get-Content "$OutputDir\logcat-crash.txt" > $tombstonePath
}

# 6. Parse Tombstone/Logcat for Stack & Root Cause Evidence
if (Test-Path $tombstonePath) {
    $content = Get-Content $tombstonePath -Raw
    if ($content -match "Fatal signal (\d+ \([^)]+\)), code \d+ \([^)]+\), fault addr ([0-9a-fx]+)") {
        $signal = $matches[1]
        $faultAddr = $matches[2]
    }
    if ($content -match "name: ([^\n\r]+)") {
        $crashThread = $matches[1]
    }
    
    $frameMatches = [regex]::Matches($content, "#\d+\s+pc\s+([0-9a-fA-F]+)\s+([^\r\n]+)")
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
}

# Build Result Objects
$gitCommit = (Get-Content "$OutputDir\git.txt" -ErrorAction SilentlyContinue | Select-Object -First 1)

$metadataObj = @{
    commit = $gitCommit
    device_serial = $DeviceSerial
    host_package = $HostPackage
    target_package = $TargetPackage
    run_label = $RunLabel
    timestamp = $Timestamp
    start_time = $startTime.ToString("yyyy-MM-dd HH:mm:ss")
    end_time = $endTime.ToString("yyyy-MM-dd HH:mm:ss")
    cpu_abi_list = $abiList
    native_bridge = $nativeBridge
}

$resultObj = @{
    commit = $gitCommit
    run_label = $RunLabel
    reproduced = $crashed
    survival_seconds = $survivalSeconds
    signal = $signal
    fault_address = $faultAddr
    crash_thread = $crashThread
    crash_library = $crashLib
    pc_offset = $pcOffset
    top_10_native_frames = $topFrames
    tombstone_extracted = $tombstoneExtracted
}

$metadataObj | ConvertTo-Json -Depth 5 | Set-Content "$OutputDir\metadata.json" -Encoding UTF8
$resultObj | ConvertTo-Json -Depth 5 | Set-Content "$OutputDir\result.json" -Encoding UTF8

Write-Host "[+] Evidence collection complete: $OutputDir" -ForegroundColor Green
Write-Host "    Reproduced       : $crashed"
Write-Host "    Survival Seconds : $survivalSeconds"
Write-Host "    Signal           : $signal"
Write-Host "    Fault Address    : $faultAddr"
Write-Host "    Crash Library    : $crashLib"
