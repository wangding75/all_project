<#
.SYNOPSIS
    Execute an SX native-crash A/B matrix with fail-fast evidence validation.

.DESCRIPTION
    The script installs the correct APK for each combination, verifies hashes and
    package state, invokes collect-native-crash.ps1, preserves each complete
    result object without field remapping, writes a summary, and runs the gate.
#>

[CmdletBinding()]
param(
    [string]$DeviceSerial = "127.0.0.1:16384",
    [string]$HostPackage = "com.sx.app.debug",
    [string]$TargetPackage = "com.quark.browser",
    [int]$VirtualUserId = 0,
    [ValidateRange(10, 3600)][int]$LaunchTimeoutSeconds = 180,
    [ValidateRange(1, 20)][int]$RunsPerCombo = 3,
    [string[]]$CombosToRun = @("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"),
    [string]$OutputRoot = "artifacts/native-crash",
    [string]$A0ApkPath = "artifacts/native-crash/app-debug-a0.apk",
    [string]$CurrentApkPath = "app/build/outputs/apk/debug/app-debug.apk",
    [string]$A0Commit = "5796121",
    [string]$A0ExpectedSha256,
    [string]$CurrentExpectedSha256,
    [switch]$AttemptAdbRoot,
    [switch]$GenerateBugreport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-ExternalCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [switch]$AllowNonZero
    )
    $output = & $FilePath @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $text = ($output | ForEach-Object { [string]$_ }) -join [Environment]::NewLine
    if (($exitCode -ne 0) -and (-not $AllowNonZero)) {
        throw "Command failed (exit=$exitCode): $FilePath $($Arguments -join ' ')`n$text"
    }
    [pscustomobject]@{ ExitCode = $exitCode; Output = $text }
}

function Invoke-Adb {
    param([string[]]$Arguments, [switch]$AllowNonZero)
    Invoke-ExternalCommand -FilePath "adb" -Arguments $Arguments -AllowNonZero:$AllowNonZero
}

function Invoke-AdbShell {
    param([string]$Command, [switch]$AllowNonZero)
    Invoke-Adb -Arguments @("-s", $DeviceSerial, "shell", "sh", "-c", $Command) -AllowNonZero:$AllowNonZero
}

function Resolve-FromRoot {
    param([string]$Root, [string]$Path)
    if ([IO.Path]::IsPathRooted($Path)) { return $Path }
    Join-Path $Root $Path
}

function Get-ApkMetadata {
    param([string]$Path, [string]$DeclaredCommit)
    if (-not (Test-Path -LiteralPath $Path)) { throw "APK not found: $Path" }
    $file = Get-Item -LiteralPath $Path
    $hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
    [ordered]@{
        path            = $file.FullName
        sha256          = $hash
        size_bytes      = $file.Length
        declared_commit = $DeclaredCommit
    }
}

function Install-And-VerifyHostApk {
    param(
        [System.Collections.IDictionary]$Metadata,
        [AllowNull()][string]$ExpectedSha256
    )

    if ($ExpectedSha256) {
        $expected = $ExpectedSha256.Replace(" ", "").ToUpperInvariant()
        if ($Metadata.sha256 -ne $expected) {
            throw "APK SHA-256 mismatch. actual=$($Metadata.sha256), expected=$expected"
        }
    }

    $install = Invoke-Adb -Arguments @("-s", $DeviceSerial, "install", "-r", "-d", "-t", $Metadata.path) -AllowNonZero
    if (($install.ExitCode -ne 0) -or ($install.Output -notmatch "(?m)^Success\s*$")) {
        throw "adb install failed for $($Metadata.path): $($install.Output)"
    }

    $pathResult = Invoke-AdbShell -Command "pm path '$HostPackage'"
    if ($pathResult.Output -notmatch "(?m)^package:") {
        throw "Installed host package cannot be resolved: $HostPackage"
    }

    $dump = Invoke-AdbShell -Command "dumpsys package '$HostPackage'"
    $versionCode = $null
    $versionName = $null
    if ($dump.Output -match "versionCode=(\d+)") { $versionCode = $matches[1] }
    if ($dump.Output -match "versionName=([^\s]+)") { $versionName = $matches[1] }

    [ordered]@{
        apk              = $Metadata
        installed_path   = ($pathResult.Output -split "\r?\n" | Select-Object -First 1).Trim()
        version_code     = $versionCode
        version_name     = $versionName
        verified_at_utc  = (Get-Date).ToUniversalTime().ToString("o")
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$sxRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$collector = Join-Path $scriptDir "collect-native-crash.ps1"
$validator = Join-Path $scriptDir "validate-native-diagnostics.ps1"
if (-not (Test-Path -LiteralPath $collector)) { throw "Collector missing: $collector" }
if (-not (Test-Path -LiteralPath $validator)) { throw "Validator missing: $validator" }

$matrixId = "matrix-$(Get-Date -Format 'yyyyMMdd-HHmmssfff')"
$matrixRootRelative = Join-Path $OutputRoot $matrixId
$matrixRoot = Resolve-FromRoot -Root $sxRoot -Path $matrixRootRelative
New-Item -ItemType Directory -Path $matrixRoot -Force | Out-Null

$currentCommit = (Invoke-ExternalCommand -FilePath "git" -Arguments @("-C", $sxRoot, "rev-parse", "HEAD")).Output.Trim()
$a0Metadata = $null
$currentMetadata = $null
if ($CombosToRun -contains "A0") {
    if ([string]::IsNullOrWhiteSpace($A0ExpectedSha256)) {
        throw "A0ExpectedSha256 is required when A0 is included"
    }
    $a0ApkFull = Resolve-FromRoot -Root $sxRoot -Path $A0ApkPath
    $a0Metadata = Get-ApkMetadata -Path $a0ApkFull -DeclaredCommit $A0Commit
}
if (@($CombosToRun | Where-Object { $_ -in @("A1", "A2", "A3", "A4", "A5", "A6") }).Count -gt 0) {
    $currentApkFull = Resolve-FromRoot -Root $sxRoot -Path $CurrentApkPath
    $currentMetadata = Get-ApkMetadata -Path $currentApkFull -DeclaredCommit $currentCommit
}

$connect = Invoke-Adb -Arguments @("connect", $DeviceSerial) -AllowNonZero
if ($connect.ExitCode -ne 0) { throw "adb connect failed: $($connect.Output)" }
$devices = Invoke-Adb -Arguments @("devices")
if ($devices.Output -notmatch "(?m)^$([regex]::Escape($DeviceSerial))\s+device\s*$") {
    throw "Device is not online: $DeviceSerial"
}

$combos = [ordered]@{
    A0 = [ordered]@{ flags = 63; system_direct = $false; apk = "a0" }
    A1 = [ordered]@{ flags = 63; system_direct = $false; apk = "current" }
    A2 = [ordered]@{ flags = 62; system_direct = $false; apk = "current" }
    A3 = [ordered]@{ flags = 61; system_direct = $false; apk = "current" }
    A4 = [ordered]@{ flags = 59; system_direct = $false; apk = "current" }
    A5 = [ordered]@{ flags = 55; system_direct = $false; apk = "current" }
    A6 = [ordered]@{ flags = 47; system_direct = $false; apk = "current" }
    A7 = [ordered]@{ flags = 0;  system_direct = $true;  apk = "none" }
}

foreach ($combo in $CombosToRun) {
    if (-not $combos.Contains($combo)) { throw "Unknown combo: $combo" }
}

$matrixMetadata = [ordered]@{
    schema_version      = 3
    matrix_id           = $matrixId
    started_at_utc      = (Get-Date).ToUniversalTime().ToString("o")
    device_serial       = $DeviceSerial
    host_package        = $HostPackage
    target_package      = $TargetPackage
    runs_per_combo      = $RunsPerCombo
    launch_timeout_sec  = $LaunchTimeoutSeconds
    combos              = @($CombosToRun)
    a0_apk              = $a0Metadata
    current_apk         = $currentMetadata
    installations       = @()
}
$matrixMetadata | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $matrixRoot "matrix-metadata.json") -Encoding UTF8

$results = [System.Collections.Generic.List[object]]::new()
$currentInstalledKind = $null

try {
    foreach ($comboName in $CombosToRun) {
        $cfg = $combos[$comboName]
        Write-Host "`n=== $comboName ===" -ForegroundColor Cyan

        if ($cfg.apk -eq "a0" -and $currentInstalledKind -ne "a0") {
            $installInfo = Install-And-VerifyHostApk -Metadata $a0Metadata -ExpectedSha256 $A0ExpectedSha256
            $installInfo["combo"] = $comboName
            $matrixMetadata.installations += $installInfo
            $currentInstalledKind = "a0"
        } elseif ($cfg.apk -eq "current" -and $currentInstalledKind -ne "current") {
            $installInfo = Install-And-VerifyHostApk -Metadata $currentMetadata -ExpectedSha256 $CurrentExpectedSha256
            $installInfo["combo"] = $comboName
            $matrixMetadata.installations += $installInfo
            $currentInstalledKind = "current"
        }

        for ($run = 1; $run -le $RunsPerCombo; $run++) {
            $runLabel = "${comboName}_run${run}"
            $runId = "$matrixId-$runLabel"
            Write-Host "[*] $runLabel" -ForegroundColor White

            $collectorArgs = @(
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", $collector,
                "-DeviceSerial", $DeviceSerial,
                "-HostPackage", $HostPackage,
                "-TargetPackage", $TargetPackage,
                "-VirtualUserId", "$VirtualUserId",
                "-LaunchTimeoutSeconds", "$LaunchTimeoutSeconds",
                "-OutputRoot", $matrixRootRelative,
                "-RunLabel", $runLabel,
                "-RunId", $runId,
                "-RequestedFlags", "$($cfg.flags)",
                "-ComboName", $comboName
            )
            if ($cfg.system_direct) { $collectorArgs += "-SystemDirect" }
            if ($comboName -eq "A0") { $collectorArgs += "-LegacySandboxDiscovery" }
            if ($AttemptAdbRoot) { $collectorArgs += "-AttemptAdbRoot" }
            if ($GenerateBugreport) { $collectorArgs += "-GenerateBugreport" }

            $collectorRun = Invoke-ExternalCommand -FilePath "powershell" -Arguments $collectorArgs -AllowNonZero
            Write-Host $collectorRun.Output
            if ($collectorRun.ExitCode -ne 0) {
                throw "Collector failed for $runLabel with exit code $($collectorRun.ExitCode)"
            }

            $runDir = Join-Path $matrixRoot $runId
            $resultPath = Join-Path $runDir "result.json"
            if (-not (Test-Path -LiteralPath $resultPath)) { throw "Missing result.json: $resultPath" }
            $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json

            if (-not $result.target_started) { throw "$runLabel did not start the target" }
            if ($result.status -eq "INVALID_EVIDENCE" -or $result.status -eq "TARGET_NOT_STARTED") {
                throw "$runLabel produced invalid evidence: $($result.status)"
            }
            if (-not $cfg.system_direct -and [int]$result.requested_flags -ne [int]$result.applied_flags) {
                throw "$runLabel flags mismatch: requested=$($result.requested_flags), applied=$($result.applied_flags)"
            }

            $results.Add($result)
            @($results) | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath (Join-Path $matrixRoot "ab-matrix-summary.json") -Encoding UTF8

            $partialArgs = @(
                "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $validator,
                "-SummaryPath", (Join-Path $matrixRootRelative "ab-matrix-summary.json"),
                "-ArtifactsDir", $matrixRootRelative,
                "-ExpectedRunsPerCombo", "$RunsPerCombo",
                "-AllowPartial"
            )
            $partialArgs += @("-ExpectedCombos", ($CombosToRun -join ","))
            $partialValidation = Invoke-ExternalCommand -FilePath "powershell" -Arguments $partialArgs -AllowNonZero
            Write-Host $partialValidation.Output
            if ($partialValidation.ExitCode -ne 0) {
                throw "Partial evidence validation failed after $runLabel"
            }
        }
    }

    $summaryRelative = Join-Path $matrixRootRelative "ab-matrix-summary.json"
    $fullArgs = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $validator,
        "-SummaryPath", $summaryRelative,
        "-ArtifactsDir", $matrixRootRelative,
        "-ExpectedRunsPerCombo", "$RunsPerCombo"
    )
    $fullArgs += @("-ExpectedCombos", ($CombosToRun -join ","))
    $fullValidation = Invoke-ExternalCommand -FilePath "powershell" -Arguments $fullArgs -AllowNonZero
    Write-Host $fullValidation.Output
    if ($fullValidation.ExitCode -ne 0) { throw "Final evidence validation failed" }

    $matrixMetadata.ended_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    $matrixMetadata.installations = @($matrixMetadata.installations)
    $matrixMetadata | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $matrixRoot "matrix-metadata.json") -Encoding UTF8

    Write-Host "`n[+] Matrix completed and validated." -ForegroundColor Green
    Write-Host "    $matrixRoot" -ForegroundColor Green
    @($results) | Select-Object combo, run_label, status, survival_seconds, requested_flags, applied_flags, @{n='pid';e={$_.target_process.pid}} | Format-Table -AutoSize
}
catch {
    $matrixMetadata.ended_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    $matrixMetadata.failure = $_.Exception.Message
    $matrixMetadata | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $matrixRoot "matrix-metadata.json") -Encoding UTF8
    Write-Host "[!] Matrix stopped: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

exit 0
