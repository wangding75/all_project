<#
.SYNOPSIS
    Collect one trustworthy SX native-crash diagnostic run.

.DESCRIPTION
    This script starts log capture before launch, binds the exact target process,
    monitors PID/starttime/cmdline, associates only current-run crash evidence,
    separates translated host and guest frames, and emits result.json.

    Exit codes:
      0  Valid evidence collected (including a confirmed crash or timeout pass)
      20 Target was not started/bound correctly
      30 Evidence was invalid or a required command failed
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$DeviceSerial = "127.0.0.1:16384",

    [Parameter(Mandatory = $false)]
    [string]$HostPackage = "com.sx.app.debug",

    [Parameter(Mandatory = $false)]
    [string]$TargetPackage = "com.quark.browser",

    [Parameter(Mandatory = $false)]
    [int]$VirtualUserId = 0,

    [Parameter(Mandatory = $false)]
    [ValidateRange(10, 3600)]
    [int]$LaunchTimeoutSeconds = 180,

    [Parameter(Mandatory = $false)]
    [string]$OutputRoot = "artifacts/native-crash",

    [Parameter(Mandatory = $false)]
    [string]$RunLabel = "A1_run1",

    [Parameter(Mandatory = $false)]
    [string]$RunId,

    [Parameter(Mandatory = $false)]
    [ValidateRange(0, 2147483647)]
    [int]$RequestedFlags = 63,

    [Parameter(Mandatory = $false)]
    [switch]$SystemDirect,

    [Parameter(Mandatory = $false)]
    [switch]$LegacySandboxDiscovery,

    [Parameter(Mandatory = $false)]
    [string]$ComboName = "A1",

    [Parameter(Mandatory = $false)]
    [switch]$AttemptAdbRoot,

    [Parameter(Mandatory = $false)]
    [switch]$GenerateBugreport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:ExitCode = 0
$script:LiveLogcatProcess = $null
$script:Errors = [System.Collections.Generic.List[string]]::new()

function Invoke-ExternalCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $false)][string[]]$Arguments = @(),
        [Parameter(Mandatory = $false)][switch]$AllowNonZero
    )

    $output = & $FilePath @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $text = ($output | ForEach-Object { [string]$_ }) -join [Environment]::NewLine

    if (($exitCode -ne 0) -and (-not $AllowNonZero)) {
        throw "Command failed (exit=$exitCode): $FilePath $($Arguments -join ' ')`n$text"
    }

    [pscustomobject]@{
        ExitCode = $exitCode
        Output   = $text
    }
}

function Invoke-Adb {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $false)][switch]$AllowNonZero
    )

    Invoke-ExternalCommand -FilePath "adb" -Arguments $Arguments -AllowNonZero:$AllowNonZero
}

function Invoke-AdbShell {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $false)][switch]$AllowNonZero
    )

    Invoke-Adb -Arguments @("-s", $DeviceSerial, "shell", "sh", "-c", $Command) -AllowNonZero:$AllowNonZero
}

function Write-Utf8Text {
    param([string]$Path, [AllowNull()][string]$Content)
    if ($null -eq $Content) { $Content = "" }
    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
}

function Get-RelativePathPortable {
    param([string]$BasePath, [string]$TargetPath)
    $baseUri = [Uri]((Resolve-Path -LiteralPath $BasePath).Path.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar)
    $targetUri = [Uri](Resolve-Path -LiteralPath $TargetPath).Path
    [Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace('/', [IO.Path]::DirectorySeparatorChar)
}

function Get-PackageUid {
    param([string]$PackageName)
    $result = Invoke-AdbShell -Command "pm list packages -U '$PackageName'" -AllowNonZero
    $match = [regex]::Match($result.Output, "(?m)^package:$([regex]::Escape($PackageName))\s+uid:(\d+)\s*$")
    if (-not $match.Success) {
        return $null
    }
    [int]$match.Groups[1].Value
}

function Get-ProcInfo {
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return $null }

    $command = @"
if [ -r /proc/$ProcessId/stat ] && [ -r /proc/$ProcessId/status ] && [ -r /proc/$ProcessId/cmdline ]; then
  stat_line=`$(cat /proc/$ProcessId/stat 2>/dev/null)
  uid=`$(awk '/^Uid:/{print `$2; exit}' /proc/$ProcessId/status 2>/dev/null)
  cmd=`$(tr '\000' ' ' < /proc/$ProcessId/cmdline 2>/dev/null | sed 's/[[:space:]]*`$//')
  ppid=`$(echo "`$stat_line" | awk '{print `$4}')
  start=`$(echo "`$stat_line" | awk '{print `$22}')
  echo "$ProcessId|`$ppid|`$uid|`$start|`$cmd"
fi
"@

    $result = Invoke-AdbShell -Command $command -AllowNonZero
    if ([string]::IsNullOrWhiteSpace($result.Output)) { return $null }

    $line = ($result.Output -split "\r?\n" | Where-Object { $_ -match "^$ProcessId\|" } | Select-Object -First 1)
    if (-not $line) { return $null }

    $parts = $line -split '\|', 5
    if ($parts.Count -ne 5) { return $null }

    [pscustomobject]@{
        pid       = [int]$parts[0]
        ppid      = [int]$parts[1]
        uid       = [int]$parts[2]
        starttime = [string]$parts[3]
        cmdline   = [string]$parts[4]
    }
}

function Get-ExactProcessesByCmdline {
    param([string]$ExactCmdline)

    if ($ExactCmdline.Contains("'")) { throw "Cmdline contains an unsupported single quote" }
    $escaped = $ExactCmdline
    $command = @"
for p in /proc/[0-9]*; do
  [ -r "`$p/cmdline" ] || continue
  cmd=`$(tr '\000' ' ' < "`$p/cmdline" 2>/dev/null | sed 's/[[:space:]]*`$//')
  [ "`$cmd" = '$escaped' ] || continue
  pid=`${p#/proc/}
  stat_line=`$(cat "`$p/stat" 2>/dev/null)
  uid=`$(awk '/^Uid:/{print `$2; exit}' "`$p/status" 2>/dev/null)
  ppid=`$(echo "`$stat_line" | awk '{print `$4}')
  start=`$(echo "`$stat_line" | awk '{print `$22}')
  echo "`$pid|`$ppid|`$uid|`$start|`$cmd"
done
"@

    $result = Invoke-AdbShell -Command $command -AllowNonZero
    $items = @()
    foreach ($line in ($result.Output -split "\r?\n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line -split '\|', 5
        if ($parts.Count -ne 5) { continue }
        $items += [pscustomobject]@{
            pid       = [int]$parts[0]
            ppid      = [int]$parts[1]
            uid       = [int]$parts[2]
            starttime = [string]$parts[3]
            cmdline   = [string]$parts[4]
        }
    }
    @($items)
}

function Get-ProcessesByCmdlinePrefix {
    param([string]$Prefix)

    if ($Prefix.Contains("'")) { throw "Prefix contains an unsupported single quote" }
    $escaped = $Prefix
    $command = @"
for p in /proc/[0-9]*; do
  [ -r "`$p/cmdline" ] || continue
  cmd=`$(tr '\000' ' ' < "`$p/cmdline" 2>/dev/null | sed 's/[[:space:]]*`$//')
  case "`$cmd" in
    '$escaped'*) ;;
    *) continue ;;
  esac
  pid=`${p#/proc/}
  stat_line=`$(cat "`$p/stat" 2>/dev/null)
  uid=`$(awk '/^Uid:/{print `$2; exit}' "`$p/status" 2>/dev/null)
  ppid=`$(echo "`$stat_line" | awk '{print `$4}')
  start=`$(echo "`$stat_line" | awk '{print `$22}')
  echo "`$pid|`$ppid|`$uid|`$start|`$cmd"
done
"@

    $result = Invoke-AdbShell -Command $command -AllowNonZero
    $items = @()
    foreach ($line in ($result.Output -split "\r?\n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line -split '\|', 5
        if ($parts.Count -ne 5) { continue }
        $items += [pscustomobject]@{
            pid       = [int]$parts[0]
            ppid      = [int]$parts[1]
            uid       = [int]$parts[2]
            starttime = [string]$parts[3]
            cmdline   = [string]$parts[4]
        }
    }
    @($items)
}

function Get-ProcessSnapshot {
    $command = @'
for p in /proc/[0-9]*; do
  [ -r "$p/cmdline" ] || continue
  cmd=$(tr '\000' ' ' < "$p/cmdline" 2>/dev/null | sed 's/[[:space:]]*$//')
  [ -n "$cmd" ] || continue
  pid=${p#/proc/}
  stat_line=$(cat "$p/stat" 2>/dev/null)
  uid=$(awk '/^Uid:/{print $2; exit}' "$p/status" 2>/dev/null)
  ppid=$(echo "$stat_line" | awk '{print $4}')
  start=$(echo "$stat_line" | awk '{print $22}')
  echo "$pid|$ppid|$uid|$start|$cmd"
done
'@
    (Invoke-AdbShell -Command $command -AllowNonZero).Output
}

function Get-TombstoneInventory {
    $command = @'
for f in /data/tombstones/tombstone_*; do
  [ -e "$f" ] || continue
  stat -c '%n|%i|%Y|%s' "$f" 2>/dev/null
done
'@
    $result = Invoke-AdbShell -Command $command -AllowNonZero
    $items = @()
    foreach ($line in ($result.Output -split "\r?\n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line -split '\|', 4
        if ($parts.Count -ne 4) { continue }
        $items += [pscustomobject]@{
            path        = [string]$parts[0]
            inode       = [string]$parts[1]
            mtime_epoch = [long]$parts[2]
            size        = [long]$parts[3]
            identity    = "$($parts[0])|$($parts[1])|$($parts[2])|$($parts[3])"
        }
    }
    @($items)
}

function Get-NewOrChangedTombstones {
    param([object[]]$Before, [object[]]$After)
    $beforeByPath = @{}
    foreach ($item in @($Before)) { $beforeByPath[$item.path] = $item }

    $changed = @()
    foreach ($item in @($After)) {
        if (-not $beforeByPath.ContainsKey($item.path)) {
            $changed += $item
            continue
        }
        $old = $beforeByPath[$item.path]
        if (($old.inode -ne $item.inode) -or ($old.mtime_epoch -ne $item.mtime_epoch) -or ($old.size -ne $item.size)) {
            $changed += $item
        }
    }
    @($changed)
}

function Parse-CrashEvents {
    param([AllowNull()][string]$CrashText)
    $nativeEvents = @()
    $javaEvents = @()
    if ([string]::IsNullOrWhiteSpace($CrashText)) {
        return [pscustomobject]@{ native = @(); java = @() }
    }

    $lines = $CrashText -split "\r?\n"
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]

        if ($line -match "Fatal signal\s+(?<number>\d+)\s+\((?<signal>[^)]+)\)(?<tail>.*)") {
            $signalNumber = [int]$matches['number']
            $signalName = $matches['signal']
            $tail = $matches['tail']
            $eventPid = $null
            $tid = $null
            $thread = $null
            $cmdline = $null
            $fault = $null

            if ($tail -match "fault addr\s+(?<fault>0x[0-9a-fA-F]+)") { $fault = $matches['fault'] }
            if ($tail -match "in tid\s+(?<tid>\d+)\s+\((?<thread>[^)]+)\),\s*pid\s+(?<pid>\d+)") {
                $tid = [int]$matches['tid']; $thread = $matches['thread']; $eventPid = [int]$matches['pid']
            } elseif ($tail -match "pid\s+(?<pid>\d+)") {
                $eventPid = [int]$matches['pid']
            }

            $windowEnd = [Math]::Min($lines.Count - 1, $i + 80)
            $window = ($lines[$i..$windowEnd] -join "`n")
            if (-not $eventPid -and $window -match "pid:\s*(?<pid>\d+),\s*tid:\s*(?<tid>\d+),\s*name:\s*(?<thread>.*?)\s+>>>") {
                $eventPid = [int]$matches['pid']; $tid = [int]$matches['tid']; $thread = $matches['thread'].Trim()
            }
            if ($window -match ">>>\s*(?<cmd>[^<]+?)\s*<<<") { $cmdline = $matches['cmd'].Trim() }

            $nativeEvents += [pscustomobject]@{
                kind       = "native"
                pid        = $eventPid
                tid        = $tid
                signal     = $signalName
                signal_num = $signalNumber
                fault_addr = $fault
                thread     = $thread
                cmdline    = $cmdline
                fatal_line = $line.Trim()
                source     = "crash_buffer"
            }
            continue
        }

        if ($line -match "FATAL EXCEPTION:\s*(?<thread>.+)$") {
            $javaThread = $matches['thread'].Trim()
            $windowEnd = [Math]::Min($lines.Count - 1, $i + 40)
            $window = ($lines[$i..$windowEnd] -join "`n")
            if ($window -match "Process:\s*(?<cmd>[^,]+),\s*PID:\s*(?<pid>\d+)") {
                $javaEvents += [pscustomobject]@{
                    kind       = "java"
                    pid        = [int]$matches['pid']
                    tid        = $null
                    signal     = $null
                    signal_num = $null
                    fault_addr = $null
                    thread     = $javaThread
                    cmdline    = $matches['cmd'].Trim()
                    fatal_line = $line.Trim()
                    source     = "logcat"
                }
            }
        }
    }

    [pscustomobject]@{ native = @($nativeEvents); java = @($javaEvents) }
}

function Parse-TombstoneHostFrame {
    param([string]$Content, [int]$ExpectedPid)
    if ([string]::IsNullOrWhiteSpace($Content)) { return $null }
    if ($Content -notmatch "pid:\s*$ExpectedPid\b") { return $null }

    $abi = $null; $signal = $null; $tid = $null; $thread = $null
    if ($Content -match "ABI:\s*'([^']+)'" ) { $abi = $matches[1] }
    if ($Content -match "signal\s+\d+\s+\(([^)]+)\)") { $signal = $matches[1] }
    if ($Content -match "pid:\s*$ExpectedPid,\s*tid:\s*(\d+),\s*name:\s*(.*?)\s+>>>") {
        $tid = [int]$matches[1]; $thread = $matches[2].Trim()
    }

    $frame = [regex]::Match($Content, "(?m)^\s*#00\s+pc\s+([0-9a-fA-F]+)\s+([^\r\n]+)$")
    $pc = $null; $module = $null; $function = $null; $buildId = $null
    if ($frame.Success) {
        $pc = $frame.Groups[1].Value
        $rest = $frame.Groups[2].Value.Trim()
        if ($rest -match "^(?<module>[^\s(]+)(?:\s+\((?<function>[^)]*)\))?(?:.*BuildId:\s*(?<build>[0-9a-fA-F]+))?") {
            $module = $matches['module']
            $function = if ($matches['function']) { $matches['function'] } else { $null }
            $buildId = if ($matches['build']) { $matches['build'] } else { $null }
        }
    }

    [pscustomobject]@{
        evidence_source = "tombstone"
        abi             = $abi
        pid             = $ExpectedPid
        tid             = $tid
        signal          = $signal
        thread          = $thread
        pc              = $pc
        module          = $module
        function        = $function
        build_id        = $buildId
    }
}

function Parse-GuestMiniDump {
    param([string]$Content, [int]$ExpectedPid)
    if ([string]::IsNullOrWhiteSpace($Content)) { return $null }

    $pattern = "(?is)ABI:\s*'(?<abi>arm64|armeabi-v7a|x86|x86_64)'.{0,2500}?pid:\s*$ExpectedPid,\s*tid:\s*(?<tid>\d+),\s*name:\s*(?<thread>.*?)\s+>>>.*?<<<.{0,2500}?signal\s+\d+\s+\((?<signal>[^)]+)\).{0,5000}?^\s*#00\s+pc\s+(?<pc>[0-9a-fA-F]+)\s+(?<module>[^\r\n (]+)(?<tail>[^\r\n]*)$"
    $match = [regex]::Match($Content, $pattern, [Text.RegularExpressions.RegexOptions]::Multiline)
    if (-not $match.Success) { return $null }

    $buildId = $null
    if ($match.Groups['tail'].Value -match "BuildId:\s*([0-9a-fA-F]+)") { $buildId = $matches[1] }

    [pscustomobject]@{
        evidence_source = "guest_minidump"
        abi             = $match.Groups['abi'].Value
        pid             = $ExpectedPid
        tid             = [int]$match.Groups['tid'].Value
        signal          = $match.Groups['signal'].Value
        thread          = $match.Groups['thread'].Value.Trim()
        pc              = $match.Groups['pc'].Value
        module          = $match.Groups['module'].Value.Trim()
        module_offset   = $match.Groups['pc'].Value
        build_id        = $buildId
    }
}

function Assert-ModuleField {
    param([AllowNull()][string]$Value, [string]$Name)
    if ($null -eq $Value) { return }
    if ($Value -match "\r|\n") { throw "$Name contains a newline" }
    if ($Value.Length -gt 512) { throw "$Name exceeds 512 characters" }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$sxRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = "$(Get-Date -Format 'yyyyMMdd-HHmmssfff')-$RunLabel"
}

$outputRootFull = if ([IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot } else { Join-Path $sxRoot $OutputRoot }
$outputDir = Join-Path $outputRootFull $RunId
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$result = [ordered]@{
    schema_version       = 3
    commit               = $null
    run_id               = $RunId
    combo                = $ComboName
    run_label            = $RunLabel
    mode                 = if ($SystemDirect) { "system_direct" } else { "sx_sandbox" }
    run_directory        = $null
    started_at_utc       = $null
    target_bound_at_utc  = $null
    ended_at_utc         = $null
    target_started       = $false
    status               = "INVALID_EVIDENCE"
    survival_seconds     = 0
    requested_flags      = if ($SystemDirect) { 0 } else { $RequestedFlags }
    applied_flags        = $null
    binding_evidence_source = $null
    flags_evidence_source   = $null
    host_package         = $HostPackage
    host_uid             = $null
    target_package       = $TargetPackage
    target_process       = $null
    process_alive_at_end = $false
    crash_event          = $null
    child_crash_events   = @()
    tombstone            = $null
    guest                = $null
    host                 = $null
    device               = $null
    artifacts            = [ordered]@{}
    errors               = @()
}

try {
    Write-Host "[*] SX native diagnostic run: $RunId" -ForegroundColor Cyan

    $connect = Invoke-Adb -Arguments @("connect", $DeviceSerial) -AllowNonZero
    if ($connect.ExitCode -ne 0) { throw "adb connect failed: $($connect.Output)" }
    $devices = Invoke-Adb -Arguments @("devices")
    if ($devices.Output -notmatch "(?m)^$([regex]::Escape($DeviceSerial))\s+device\s*$") {
        throw "Device is not online: $DeviceSerial"
    }

    if ($AttemptAdbRoot) {
        Invoke-Adb -Arguments @("-s", $DeviceSerial, "root") -AllowNonZero | Out-Null
        Start-Sleep -Seconds 1
    }

    $git = Invoke-ExternalCommand -FilePath "git" -Arguments @("-C", $sxRoot, "rev-parse", "HEAD")
    $result.commit = $git.Output.Trim()
    Write-Utf8Text -Path (Join-Path $outputDir "git.txt") -Content $git.Output

    $hostUid = Get-PackageUid -PackageName $HostPackage
    $targetSystemUid = Get-PackageUid -PackageName $TargetPackage
    if (-not $SystemDirect -and $null -eq $hostUid) { throw "Cannot resolve host UID for $HostPackage" }
    if ($SystemDirect -and $null -eq $targetSystemUid) { throw "Cannot resolve target UID for $TargetPackage" }
    $result.host_uid = $hostUid

    $abilist = (Invoke-AdbShell -Command "getprop ro.product.cpu.abilist" -AllowNonZero).Output.Trim()
    $nativeBridge = (Invoke-AdbShell -Command "getprop ro.dalvik.vm.native.bridge" -AllowNonZero).Output.Trim()
    $androidRelease = (Invoke-AdbShell -Command "getprop ro.build.version.release" -AllowNonZero).Output.Trim()
    $sdk = (Invoke-AdbShell -Command "getprop ro.build.version.sdk" -AllowNonZero).Output.Trim()
    $result.device = [ordered]@{
        serial        = $DeviceSerial
        android       = $androidRelease
        sdk           = $sdk
        abi_list      = $abilist
        native_bridge = $nativeBridge
    }

    Write-Utf8Text -Path (Join-Path $outputDir "device-properties.txt") -Content (Invoke-AdbShell -Command "getprop" -AllowNonZero).Output
    Write-Utf8Text -Path (Join-Path $outputDir "process-before.txt") -Content (Get-ProcessSnapshot)

    $tombBefore = @(Get-TombstoneInventory)
    $tombBefore | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outputDir "tombstone-before.json") -Encoding UTF8

    if (-not $SystemDirect) {
        Invoke-AdbShell -Command "setprop debug.sx.native_hook_flags '$RequestedFlags'" | Out-Null
        Invoke-AdbShell -Command "setprop debug.sx.run_id '$RunId'" | Out-Null
    }

    Invoke-Adb -Arguments @("-s", $DeviceSerial, "logcat", "-c") | Out-Null

    $liveStdout = Join-Path $outputDir "logcat-live.txt"
    $liveStderr = Join-Path $outputDir "logcat-live.err.txt"
    $script:LiveLogcatProcess = Start-Process -FilePath "adb" -ArgumentList @("-s", $DeviceSerial, "logcat", "-v", "threadtime") -RedirectStandardOutput $liveStdout -RedirectStandardError $liveStderr -PassThru -WindowStyle Hidden

    $result.started_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    $launchStart = Get-Date

    $beforeDirect = @()
    $beforeVirtual = @()
    if ($SystemDirect) {
        Invoke-AdbShell -Command "am force-stop '$TargetPackage'" -AllowNonZero | Out-Null
        Start-Sleep -Seconds 2
        $beforeDirect = @(Get-ExactProcessesByCmdline -ExactCmdline $TargetPackage)
        $launch = Invoke-AdbShell -Command "monkey -p '$TargetPackage' -c android.intent.category.LAUNCHER 1" -AllowNonZero
    } else {
        Invoke-AdbShell -Command "am force-stop '$HostPackage'" -AllowNonZero | Out-Null
        Start-Sleep -Seconds 2
        $beforeVirtual = @(Get-ExactProcessesByCmdline -ExactCmdline $TargetPackage | Where-Object { $_.uid -eq $hostUid })
        $component = "$HostPackage/com.sx.app.ui.sandbox.ShortcutLaunchActivity"
        $launch = Invoke-AdbShell -Command "am start -W -n '$component' --es package_name '$TargetPackage' --ei user_id '$VirtualUserId'"
    }
    Write-Utf8Text -Path (Join-Path $outputDir "launch.log") -Content $launch.Output

    $targetProc = $null
    $appliedFlags = if ($SystemDirect) { 0 } else { $null }
    if ($SystemDirect) {
        $result.binding_evidence_source = "new_exact_system_process"
        $result.flags_evidence_source = "system_direct"
    }
    $bindDeadline = (Get-Date).AddSeconds([Math]::Min(45, $LaunchTimeoutSeconds))

    while ((Get-Date) -lt $bindDeadline -and $null -eq $targetProc) {
        Start-Sleep -Milliseconds 500

        if ($SystemDirect) {
            $after = @(Get-ExactProcessesByCmdline -ExactCmdline $TargetPackage)
            $beforeKeys = @{}
            foreach ($p in $beforeDirect) { $beforeKeys["$($p.pid)|$($p.starttime)"] = $true }
            $candidates = @($after | Where-Object {
                $_.uid -eq $targetSystemUid -and -not $beforeKeys.ContainsKey("$($_.pid)|$($_.starttime)")
            })
            if ($candidates.Count -eq 1) {
                $targetProc = $candidates[0]
            } elseif ($candidates.Count -gt 1) {
                throw "A7 produced multiple new exact main-process candidates: $($candidates | ConvertTo-Json -Compress)"
            }
        } elseif ($LegacySandboxDiscovery) {
            $afterVirtual = @(Get-ExactProcessesByCmdline -ExactCmdline $TargetPackage | Where-Object { $_.uid -eq $hostUid })
            $beforeKeys = @{}
            foreach ($p in $beforeVirtual) { $beforeKeys["$($p.pid)|$($p.starttime)"] = $true }
            $candidates = @($afterVirtual | Where-Object { -not $beforeKeys.ContainsKey("$($_.pid)|$($_.starttime)") })
            if ($candidates.Count -eq 1) {
                $targetProc = $candidates[0]
                $propertyValue = (Invoke-AdbShell -Command "getprop debug.sx.native_hook_flags" -AllowNonZero).Output.Trim()
                if ($propertyValue -notmatch '^\d+$') { throw "Legacy discovery could not read native_hook_flags property" }
                $appliedFlags = [int]$propertyValue
                if ($appliedFlags -ne $RequestedFlags) { throw "Legacy discovery flags mismatch: property=$appliedFlags expected=$RequestedFlags" }
                $result.binding_evidence_source = "new_exact_sandbox_process"
                $result.flags_evidence_source = "system_property"
            } elseif ($candidates.Count -gt 1) {
                throw "Legacy sandbox discovery produced multiple exact main-process candidates: $($candidates | ConvertTo-Json -Compress)"
            }
        } else {
            $earlyLog = (Invoke-Adb -Arguments @("-s", $DeviceSerial, "logcat", "-d", "-v", "brief") -AllowNonZero).Output
            $runEsc = [regex]::Escape($RunId)
            $pkgEsc = [regex]::Escape($TargetPackage)
            $pattern = "SX_TARGET_BOUND:\s*RunId=$runEsc\s+virtualPackage=$pkgEsc\s+virtualProcessName=$pkgEsc\s+hostProcessName=(?<host>\S+)\s+pid=(?<pid>\d+)\s+uid=(?<uid>\d+)\s+userId=$VirtualUserId\s+requestedFlags=(?<requested>\d+)\s+appliedFlags=(?<applied>\d+)"
            $matchesFound = [regex]::Matches($earlyLog, $pattern)
            if ($matchesFound.Count -gt 0) {
                $bound = $matchesFound[$matchesFound.Count - 1]
                $boundPid = [int]$bound.Groups['pid'].Value
                $boundUid = [int]$bound.Groups['uid'].Value
                $boundRequested = [int]$bound.Groups['requested'].Value
                $boundApplied = [int]$bound.Groups['applied'].Value

                if ($boundUid -ne $hostUid) { throw "SX_TARGET_BOUND UID mismatch: log=$boundUid host=$hostUid" }
                if ($boundRequested -ne $RequestedFlags) { throw "SX_TARGET_BOUND requestedFlags mismatch: log=$boundRequested expected=$RequestedFlags" }
                if ($boundApplied -ne $RequestedFlags) { throw "SX_TARGET_BOUND appliedFlags mismatch: applied=$boundApplied expected=$RequestedFlags" }

                $proc = Get-ProcInfo -ProcessId $boundPid
                if ($null -eq $proc) { continue }
                if ($proc.uid -ne $hostUid) { throw "Bound PID UID mismatch: proc=$($proc.uid) host=$hostUid" }
                if ($proc.cmdline -ne $TargetPackage) { throw "Bound PID cmdline mismatch: '$($proc.cmdline)'" }

                $targetProc = $proc
                $appliedFlags = $boundApplied
                $result.binding_evidence_source = "SX_TARGET_BOUND"
                $result.flags_evidence_source = "SX_TARGET_BOUND"
            }
        }
    }

    if ($null -eq $targetProc) {
        $result.status = "TARGET_NOT_STARTED"
        $script:ExitCode = 20
        throw "Target process did not bind within the allowed window"
    }

    $result.target_started = $true
    $result.applied_flags = $appliedFlags
    $result.target_bound_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    $result.target_process = [ordered]@{
        pid       = $targetProc.pid
        ppid      = $targetProc.ppid
        uid       = $targetProc.uid
        cmdline   = $targetProc.cmdline
        starttime = $targetProc.starttime
    }

    Write-Utf8Text -Path (Join-Path $outputDir "applied-flags.txt") -Content "requested=$($result.requested_flags)`napplied=$($result.applied_flags)`npid=$($targetProc.pid)`nuid=$($targetProc.uid)`ncmdline=$($targetProc.cmdline)`nstarttime=$($targetProc.starttime)"

    $status = "PASS_TIMEOUT_ALIVE"
    $crashEvent = $null
    $childCrashEvents = @()
    $observedTargetProcesses = @{}
    foreach ($observed in @(Get-ProcessesByCmdlinePrefix -Prefix $TargetPackage)) {
        $observedTargetProcesses[[int]$observed.pid] = $observed
    }
    $deadline = (Get-Date).AddSeconds($LaunchTimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 1
        $result.survival_seconds = [int]((Get-Date) - $launchStart).TotalSeconds

        $crashText = (Invoke-Adb -Arguments @("-s", $DeviceSerial, "logcat", "-b", "crash", "-d", "-v", "threadtime") -AllowNonZero).Output
        $events = Parse-CrashEvents -CrashText $crashText

        $nativeTarget = @($events.native | Where-Object { $_.pid -eq $targetProc.pid } | Select-Object -First 1)
        $javaTarget = @($events.java | Where-Object { $_.pid -eq $targetProc.pid } | Select-Object -First 1)

        if ($nativeTarget.Count -gt 0) {
            $status = "NATIVE_CRASH"
            $crashEvent = $nativeTarget[0]
            break
        }
        if ($javaTarget.Count -gt 0) {
            $status = "JAVA_CRASH"
            $crashEvent = $javaTarget[0]
            break
        }

        $currentProc = Get-ProcInfo -ProcessId $targetProc.pid
        $isSameProcess = ($null -ne $currentProc) -and
            ($currentProc.starttime -eq $targetProc.starttime) -and
            ($currentProc.cmdline -eq $targetProc.cmdline) -and
            ($currentProc.uid -eq $targetProc.uid)

        foreach ($observed in @(Get-ProcessesByCmdlinePrefix -Prefix $TargetPackage)) {
            $observedTargetProcesses[[int]$observed.pid] = $observed
        }

        $knownChildEvents = @($events.native | Where-Object {
            if ($null -eq $_.pid -or $_.pid -eq $targetProc.pid) { return $false }
            if (-not $observedTargetProcesses.ContainsKey([int]$_.pid)) { return $false }
            $meta = $observedTargetProcesses[[int]$_.pid]
            return (([int]$meta.uid -eq [int]$targetProc.uid) -and ([string]$meta.cmdline).StartsWith($TargetPackage))
        })
        foreach ($event in $knownChildEvents) {
            if (-not ($childCrashEvents | Where-Object { $_.pid -eq $event.pid -and $_.fatal_line -eq $event.fatal_line })) {
                $meta = $observedTargetProcesses[[int]$event.pid]
                $event.cmdline = $meta.cmdline
                $event | Add-Member -NotePropertyName process -NotePropertyValue ([ordered]@{
                    pid = $meta.pid; ppid = $meta.ppid; uid = $meta.uid; starttime = $meta.starttime; cmdline = $meta.cmdline
                }) -Force
                $childCrashEvents += $event
            }
        }

        if (-not $isSameProcess) {
            $finalCrashText = (Invoke-Adb -Arguments @("-s", $DeviceSerial, "logcat", "-b", "crash", "-d", "-v", "threadtime") -AllowNonZero).Output
            $finalEvents = Parse-CrashEvents -CrashText $finalCrashText
            $exact = @($finalEvents.native | Where-Object { $_.pid -eq $targetProc.pid } | Select-Object -First 1)
            if ($exact.Count -gt 0) {
                $status = "NATIVE_CRASH"
                $crashEvent = $exact[0]
            } else {
                $exactJava = @($finalEvents.java | Where-Object { $_.pid -eq $targetProc.pid } | Select-Object -First 1)
                if ($exactJava.Count -gt 0) {
                    $status = "JAVA_CRASH"
                    $crashEvent = $exactJava[0]
                } else {
                    $status = "PROCESS_LOST"
                }
            }
            break
        }
    }

    if ($status -eq "PASS_TIMEOUT_ALIVE" -and $childCrashEvents.Count -gt 0) {
        $status = "CHILD_NATIVE_CRASH"
        $crashEvent = $childCrashEvents[0]
    }

    $result.status = $status
    $result.crash_event = $crashEvent
    $result.child_crash_events = @($childCrashEvents)

    $currentAtEnd = Get-ProcInfo -ProcessId $targetProc.pid
    $result.process_alive_at_end = ($null -ne $currentAtEnd) -and
        ($currentAtEnd.starttime -eq $targetProc.starttime) -and
        ($currentAtEnd.cmdline -eq $targetProc.cmdline)

    $result.ended_at_utc = (Get-Date).ToUniversalTime().ToString("o")

    $allLog = (Invoke-Adb -Arguments @("-s", $DeviceSerial, "logcat", "-d", "-v", "threadtime") -AllowNonZero).Output
    $crashLog = (Invoke-Adb -Arguments @("-s", $DeviceSerial, "logcat", "-b", "crash", "-d", "-v", "threadtime") -AllowNonZero).Output
    Write-Utf8Text -Path (Join-Path $outputDir "logcat-all.txt") -Content $allLog
    Write-Utf8Text -Path (Join-Path $outputDir "logcat-crash.txt") -Content $crashLog
    Write-Utf8Text -Path (Join-Path $outputDir "process-after.txt") -Content (Get-ProcessSnapshot)
    Write-Utf8Text -Path (Join-Path $outputDir "dumpsys-activity.txt") -Content (Invoke-AdbShell -Command "dumpsys activity" -AllowNonZero).Output

    if ($targetProc) {
        Write-Utf8Text -Path (Join-Path $outputDir "maps-after.txt") -Content (Invoke-AdbShell -Command "cat /proc/$($targetProc.pid)/maps" -AllowNonZero).Output
        Write-Utf8Text -Path (Join-Path $outputDir "fd-list.txt") -Content (Invoke-AdbShell -Command "ls -l /proc/$($targetProc.pid)/fd" -AllowNonZero).Output
        Write-Utf8Text -Path (Join-Path $outputDir "mountinfo.txt") -Content (Invoke-AdbShell -Command "cat /proc/$($targetProc.pid)/mountinfo" -AllowNonZero).Output
    }

    $tombAfter = @(Get-TombstoneInventory)
    $tombAfter | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outputDir "tombstone-after.json") -Encoding UTF8
    $changedTombstones = @(Get-NewOrChangedTombstones -Before $tombBefore -After $tombAfter)

    $runStartEpoch = [DateTimeOffset]::Parse($result.started_at_utc).ToUnixTimeSeconds()
    $runEndEpoch = [DateTimeOffset]::Parse($result.ended_at_utc).ToUnixTimeSeconds()
    $candidatePids = @($targetProc.pid)
    foreach ($childEvent in $childCrashEvents) {
        if ($childEvent.pid) { $candidatePids += [int]$childEvent.pid }
    }
    $candidatePids = @($candidatePids | Select-Object -Unique)

    foreach ($tomb in $changedTombstones) {
        if (($tomb.mtime_epoch -lt ($runStartEpoch - 10)) -or ($tomb.mtime_epoch -gt ($runEndEpoch + 10))) { continue }
        $contentResult = Invoke-AdbShell -Command "cat '$($tomb.path)'" -AllowNonZero
        if ($contentResult.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($contentResult.Output)) { continue }

        $matchedPid = $null
        foreach ($candidatePid in $candidatePids) {
            if ($contentResult.Output -match "pid:\s*$candidatePid\b") {
                $matchedPid = $candidatePid
                break
            }
        }
        if ($null -eq $matchedPid) { continue }

        $matchedPath = Join-Path $outputDir "matched-tombstone.txt"
        Write-Utf8Text -Path $matchedPath -Content $contentResult.Output
        $result.tombstone = [ordered]@{
            path              = $tomb.path
            identity          = $tomb.identity
            inode             = $tomb.inode
            mtime_epoch       = $tomb.mtime_epoch
            size              = $tomb.size
            pid               = $matchedPid
            is_new_or_changed = $true
            evidence_file     = "matched-tombstone.txt"
        }
        $result.host = Parse-TombstoneHostFrame -Content $contentResult.Output -ExpectedPid $matchedPid
        break
    }

    if ($result.status -eq "NATIVE_CRASH" -or $result.status -eq "CHILD_NATIVE_CRASH") {
        $crashPid = [int]$result.crash_event.pid
        $result.guest = Parse-GuestMiniDump -Content $allLog -ExpectedPid $crashPid
    }

    if ($result.guest) { Assert-ModuleField -Value $result.guest.module -Name "guest.module" }
    if ($result.host) { Assert-ModuleField -Value $result.host.module -Name "host.module" }

    if ($GenerateBugreport -and ($result.status -match "CRASH|PROCESS_LOST")) {
        $bugreportPath = Join-Path $outputDir "bugreport.zip"
        $bug = Invoke-Adb -Arguments @("-s", $DeviceSerial, "bugreport", $bugreportPath) -AllowNonZero
        Write-Utf8Text -Path (Join-Path $outputDir "bugreport-command.txt") -Content $bug.Output
    }

    if ($result.status -eq "NATIVE_CRASH") {
        if ($null -eq $result.crash_event -or $result.crash_event.pid -ne $targetProc.pid -or [string]::IsNullOrWhiteSpace([string]$result.crash_event.signal)) {
            throw "NATIVE_CRASH lacks an exact target-PID crash event"
        }
    }
    if ($result.status -eq "CHILD_NATIVE_CRASH") {
        if ($null -eq $result.crash_event -or $result.crash_event.pid -eq $targetProc.pid) {
            throw "CHILD_NATIVE_CRASH lacks a distinct child PID"
        }
    }
    if ($result.status -eq "PASS_TIMEOUT_ALIVE" -and -not $result.process_alive_at_end) {
        throw "PASS_TIMEOUT_ALIVE but the original target PID/starttime is no longer alive"
    }
}
catch {
    $message = $_.Exception.Message
    $script:Errors.Add($message)
    if ($result.status -ne "TARGET_NOT_STARTED") {
        $result.status = "INVALID_EVIDENCE"
        $script:ExitCode = 30
    }
    if (-not $result.ended_at_utc) { $result.ended_at_utc = (Get-Date).ToUniversalTime().ToString("o") }
    Write-Host "[!] $message" -ForegroundColor Red
}
finally {
    if ($script:LiveLogcatProcess) {
        try {
            if (-not $script:LiveLogcatProcess.HasExited) {
                Stop-Process -Id $script:LiveLogcatProcess.Id -Force -ErrorAction SilentlyContinue
            }
        } catch { }
    }

    try {
        $result.run_directory = Get-RelativePathPortable -BasePath $sxRoot -TargetPath $outputDir
    } catch {
        $result.run_directory = $outputDir
    }
    $result.errors = @($script:Errors)
    if (-not $result.ended_at_utc) { $result.ended_at_utc = (Get-Date).ToUniversalTime().ToString("o") }

    $result.artifacts = [ordered]@{
        launch_log          = "launch.log"
        live_logcat         = "logcat-live.txt"
        full_logcat         = "logcat-all.txt"
        crash_logcat        = "logcat-crash.txt"
        process_before      = "process-before.txt"
        process_after       = "process-after.txt"
        flags               = "applied-flags.txt"
        tombstone_before    = "tombstone-before.json"
        tombstone_after     = "tombstone-after.json"
        matched_tombstone   = if ($result.tombstone) { "matched-tombstone.txt" } else { $null }
        dumpsys_activity    = "dumpsys-activity.txt"
    }

    $resultPath = Join-Path $outputDir "result.json"
    $result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Host "[*] Result: $resultPath" -ForegroundColor Cyan
    Write-Host "[*] Status: $($result.status)" -ForegroundColor Cyan
}

exit $script:ExitCode
