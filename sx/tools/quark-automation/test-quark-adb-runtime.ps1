<#
.SYNOPSIS
    Real ADB Runtime Preflight for Quark Automation Diagnostics.

.DESCRIPTION
    Executes real runtime verification checks against an online Android emulator:
      A. Device online check (adb devices -l)
      B. Simple command check (getprop ro.build.version.sdk)
      C. Shell variable & pipeline tr case conversion
      D. Command substitution
      E. Multiline command execution
      F. /proc reading (/proc/self/status, /proc/self/stat, /proc/self/cmdline)
      G. Host & Target package UID resolution (pm list packages -U vs dumpsys package)
      H. Artifact generation (adb-runtime-preflight.json, adb-runtime-preflight.log)
#>

[CmdletBinding()]
param(
    [string]$DeviceSerial = "127.0.0.1:7555",
    [string]$HostPackage = "com.sx.app.debug",
    [string]$TargetPackage = "com.quark.browser",
    [string]$OutputDirectory = "artifacts/quark-automation-preflight"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8Text {
    param([string]$Path, [AllowNull()][string]$Content)
    if ($null -eq $Content) { $Content = "" }
    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
}

function Invoke-ExternalCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $false)][string[]]$Arguments = @(),
        [Parameter(Mandatory = $false)][switch]$AllowNonZero
    )

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    if ($Arguments.Count -gt 0) {
        $psi.Arguments = ($Arguments | ForEach-Object {
            if ($_ -match '\s') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
        }) -join ' '
    }
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $psi
    $process.Start() | Out-Null

    $stdOut = $process.StandardOutput.ReadToEnd()
    $stdErr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    $exitCode = $process.ExitCode
    $combined = ($stdOut + [Environment]::NewLine + $stdErr).Trim()

    if (($exitCode -ne 0) -and (-not $AllowNonZero)) {
        throw "Command failed (exit=$exitCode): $FilePath $($Arguments -join ' ')`n$combined"
    }

    [pscustomobject]@{
        ExitCode = $exitCode
        Output   = $combined
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
        [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$Command,
        [Parameter(Mandatory = $false)][switch]$AllowNonZero
    )

    $normalizedCommand = $Command.Replace("`r`n", "`n").Replace("`r", "`n")
    Invoke-Adb -Arguments @("-s", $DeviceSerial, "shell", $normalizedCommand) -AllowNonZero:$AllowNonZero
}

function Resolve-PackageUidDual {
    param([string]$PackageName)

    $safePkg = $PackageName -replace '[^a-zA-Z0-9_\-.]', '_'

    # Level 1: pm list packages -U <package>
    $pmRes = Invoke-Adb -Arguments @("-s", $DeviceSerial, "shell", "pm", "list", "packages", "-U", $PackageName) -AllowNonZero
    $pmUid = $null
    if ($pmRes.ExitCode -eq 0 -and $pmRes.Output) {
        $escapedPkg = [regex]::Escape($PackageName)
        $match = [regex]::Match($pmRes.Output, "(?m)^package:${escapedPkg}\s+uid:(?<uid>\d+)\s*$")
        if ($match.Success) {
            $pmUid = [int]$match.Groups['uid'].Value
        }
    }

    # Level 2: dumpsys package <package>
    $dumpRes = Invoke-Adb -Arguments @("-s", $DeviceSerial, "shell", "dumpsys", "package", $PackageName) -AllowNonZero
    $dumpUid = $null
    if ($dumpRes.ExitCode -eq 0 -and $dumpRes.Output) {
        $match = [regex]::Match($dumpRes.Output, "(?m)^\s*userId=(?<uid>\d+)\s*$")
        if ($match.Success) {
            $dumpUid = [int]$match.Groups['uid'].Value
        }
    }

    [pscustomobject]@{
        pm_uid      = $pmUid
        dumpsys_uid = $dumpUid
    }
}

$startedAt = (Get-Date).ToUniversalTime().ToString("o")
$logLines = [System.Collections.Generic.List[string]]::new()
$errors = [System.Collections.Generic.List[string]]::new()

function Log-Info([string]$msg) {
    $line = "[*] $msg"
    Write-Host $line -ForegroundColor Cyan
    $logLines.Add($line)
}

function Log-Error([string]$msg) {
    $line = "[!] $msg"
    Write-Host $line -ForegroundColor Red
    $logLines.Add($line)
    $errors.Add($msg)
}

if (-not [IO.Path]::IsPathRooted($OutputDirectory)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $sxRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
    $OutputDirectory = Join-Path $sxRoot $OutputDirectory
}
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

Log-Info "Starting Real ADB Runtime Preflight for $DeviceSerial"

# A. Device Online
$deviceOnline = $false
try {
    $connect = Invoke-Adb -Arguments @("connect", $DeviceSerial) -AllowNonZero
    $devRes = Invoke-Adb -Arguments @("devices", "-l")
    if ($devRes.Output -match "(?m)^$([regex]::Escape($DeviceSerial))\s+device\b") {
        $deviceOnline = $true
        Log-Info "Device is online: $DeviceSerial"
    } else {
        Log-Error "Device is not online in 'adb devices -l': $DeviceSerial"
    }
} catch {
    Log-Error "Device online check failed: $_"
}

# B. Simple command
$sdk = $null
try {
    $sdkRes = Invoke-AdbShell -Command "getprop ro.build.version.sdk" -AllowNonZero
    $sdkText = $sdkRes.Output.Trim()
    if ($sdkText -match "^\d+$") {
        $sdk = [int]$sdkText
        Log-Info "SDK version: $sdk"
    } else {
        Log-Error "ro.build.version.sdk did not return digits: '$sdkText'"
    }
} catch {
    Log-Error "SDK getprop failed: $_"
}

# C. Shell variables & pipeline
$varPipelinePass = $false
try {
    $cmdC = 'probe=SX_ADB_SHELL_PROBE' + "`n" + 'printf ''%s\n'' "$probe" | tr ''A-Z'' ''a-z'''
    $resC = Invoke-AdbShell -Command $cmdC -AllowNonZero
    if ($resC.Output.Trim() -eq "sx_adb_shell_probe") {
        $varPipelinePass = $true
        Log-Info "Shell variable & pipeline test passed"
    } else {
        Log-Error "Shell variable & pipeline test failed, output: '$($resC.Output)'"
    }
} catch {
    Log-Error "Shell variable & pipeline exception: $_"
}

# D. Command substitution
$cmdSubPass = $false
try {
    $cmdD = 'printf ''prefix-%s\n'' "$(printf suffix)"'
    $resD = Invoke-AdbShell -Command $cmdD -AllowNonZero
    if ($resD.Output.Trim() -eq "prefix-suffix") {
        $cmdSubPass = $true
        Log-Info "Command substitution test passed"
    } else {
        Log-Error "Command substitution test failed, output: '$($resD.Output)'"
    }
} catch {
    Log-Error "Command substitution exception: $_"
}

# E. Multiline command
$multilinePass = $false
try {
    $cmdE = "a=first`nb=second`nprintf '%s\n%s\n' `"`$a`" `"`$b`""
    $resE = Invoke-AdbShell -Command $cmdE -AllowNonZero
    $linesE = ($resE.Output -split "\r?\n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($linesE.Count -ge 2 -and $linesE[0] -eq "first" -and $linesE[1] -eq "second") {
        $multilinePass = $true
        Log-Info "Multiline command test passed"
    } else {
        Log-Error "Multiline command test failed, output: '$($resE.Output)'"
    }
} catch {
    Log-Error "Multiline command exception: $_"
}

# F. /proc reading
$procReadPass = $false
try {
    $cmdF = "cat /proc/self/status; cat /proc/self/stat; cat /proc/self/cmdline"
    $resF = Invoke-AdbShell -Command $cmdF -AllowNonZero
    $txtF = $resF.Output
    $hasUid = ($txtF -match "(?m)^Uid:\s+\d+")
    $hasCmd = ([string]::IsNullOrWhiteSpace($txtF) -eq $false)
    if ($hasUid -and $hasCmd) {
        $procReadPass = $true
        Log-Info "/proc read test passed"
    } else {
        Log-Error "/proc read test failed: Uid found=$hasUid, content empty=$(-not $hasCmd)"
    }
} catch {
    Log-Error "/proc read exception: $_"
}

# G. Package UIDs
$hostDual = Resolve-PackageUidDual -PackageName $HostPackage
$targetDual = Resolve-PackageUidDual -PackageName $TargetPackage

Log-Info "Host ($HostPackage) UID: pm=$($hostDual.pm_uid), dumpsys=$($hostDual.dumpsys_uid)"
Log-Info "Target ($TargetPackage) UID: pm=$($targetDual.pm_uid), dumpsys=$($targetDual.dumpsys_uid)"

if ($null -eq $hostDual.pm_uid -or $null -eq $hostDual.dumpsys_uid -or $hostDual.pm_uid -ne $hostDual.dumpsys_uid) {
    Log-Error "HostPackage UID dual resolution failed or mismatched for $HostPackage"
}

if ($null -eq $targetDual.pm_uid -or $null -eq $targetDual.dumpsys_uid -or $targetDual.pm_uid -ne $targetDual.dumpsys_uid) {
    Log-Error "TargetPackage UID dual resolution failed or mismatched for $TargetPackage"
}

$endedAt = (Get-Date).ToUniversalTime().ToString("o")
$overallPass = ($deviceOnline -and ($null -ne $sdk) -and $varPipelinePass -and $cmdSubPass -and $multilinePass -and $procReadPass -and ($errors.Count -eq 0))
$status = if ($overallPass) { "PASS" } else { "FAIL" }

$preflightJson = [ordered]@{
    schema_version                = 1
    device_serial                 = $DeviceSerial
    device_online                 = $deviceOnline
    sdk                           = $sdk
    shell_variable_pipeline_pass  = $varPipelinePass
    command_substitution_pass     = $cmdSubPass
    multiline_pass                = $multilinePass
    proc_read_pass                = $procReadPass
    host_package                  = $HostPackage
    host_uid_pm                   = $hostDual.pm_uid
    host_uid_dumpsys              = $hostDual.dumpsys_uid
    target_package                = $TargetPackage
    target_uid_pm                 = $targetDual.pm_uid
    target_uid_dumpsys            = $targetDual.dumpsys_uid
    status                        = $status
    errors                        = @($errors)
    started_at_utc                = $startedAt
    ended_at_utc                  = $endedAt
}

$jsonPath = Join-Path $OutputDirectory "adb-runtime-preflight.json"
$logPath = Join-Path $OutputDirectory "adb-runtime-preflight.log"

$preflightJson | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
Write-Utf8Text -Path $logPath -Content ($logLines -join [Environment]::NewLine)

Log-Info "Runtime Preflight finished with status: $status"
Log-Info "Report written to: $jsonPath"

if ($status -ne "PASS") {
    exit 1
}
exit 0
