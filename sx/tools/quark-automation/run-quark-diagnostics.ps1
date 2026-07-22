<#
.SYNOPSIS
    Run the automated Quark diagnostic sequence on an online Android emulator.

.DESCRIPTION
    The driver performs syntax/fixture gates, then executes three evidence-checked
    scenarios with the existing native diagnostic collector:
      Q0/A7 - system-direct Quark baseline, one run.
      Q1/A1 - Quark inside SX with flags 63, three runs by default.
      Q2/A6 - Quark inside SX with flags 47, three runs by default.

    Q3 is an automated analysis pass over Q1 logcat and process evidence. The
    driver does not modify source code, APK contents, or diagnostic scripts.
#>

[CmdletBinding()]
param(
    [string]$DeviceSerial = "127.0.0.1:16384",
    [string]$HostPackage = "com.sx.app.debug",
    [string]$TargetPackage = "com.quark.browser",
    [int]$VirtualUserId = 0,
    [ValidateRange(30, 1800)][int]$ObservationSeconds = 180,
    [ValidateRange(1, 10)][int]$SandboxRuns = 3,
    [string]$CurrentApkPath = "app/build/outputs/apk/debug/app-debug.apk",
    [string]$OutputRoot = "artifacts/quark-automation",
    [switch]$AttemptAdbRoot,
    [switch]$GenerateBugreport,
    [switch]$SkipFixtureGate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-ChildPowerShell {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$PowerShellPath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$StepName
    )

    Write-Host "[*] $StepName" -ForegroundColor Cyan
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & $PowerShellPath @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }

    if ($output) {
        $output | ForEach-Object { Write-Host ([string]$_) }
    }
    if ($exitCode -ne 0) {
        throw "$StepName failed with exit code $exitCode"
    }
}

function Resolve-FromRoot {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )
    if ([IO.Path]::IsPathRooted($Path)) { return $Path }
    return (Join-Path $Root $Path)
}

function Assert-OnlineDevice {
    param([Parameter(Mandatory = $true)][string]$Serial)

    $connectOutput = & adb connect $Serial 2>&1
    $connectExit = $LASTEXITCODE
    if ($connectExit -ne 0) {
        throw "adb connect failed for ${Serial}: $($connectOutput -join [Environment]::NewLine)"
    }

    $deviceOutput = & adb devices 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "adb devices failed: $($deviceOutput -join [Environment]::NewLine)"
    }
    $deviceText = ($deviceOutput | ForEach-Object { [string]$_ }) -join [Environment]::NewLine
    if ($deviceText -notmatch "(?m)^$([regex]::Escape($Serial))\s+device\s*$") {
        throw "Device is not online: $Serial"
    }
}

function Invoke-MatrixScenario {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$PowerShellPath,
        [Parameter(Mandatory = $true)][string]$RunnerPath,
        [Parameter(Mandatory = $true)][string]$ScenarioName,
        [Parameter(Mandatory = $true)][string]$Combo,
        [Parameter(Mandatory = $true)][int]$Runs,
        [Parameter(Mandatory = $true)][string]$ScenarioOutputRoot,
        [Parameter(Mandatory = $true)][string]$ApkPath,
        [AllowNull()][string]$ApkSha256,
        [Parameter(Mandatory = $true)][string]$Serial,
        [Parameter(Mandatory = $true)][string]$HostPackageName,
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][int]$UserId,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds,
        [switch]$UseAdbRoot,
        [switch]$UseBugreport
    )

    $childArgs = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $RunnerPath,
        "-DeviceSerial", $Serial,
        "-HostPackage", $HostPackageName,
        "-TargetPackage", $Target,
        "-VirtualUserId", "$UserId",
        "-LaunchTimeoutSeconds", "$TimeoutSeconds",
        "-RunsPerCombo", "$Runs",
        "-CombosToRun", $Combo,
        "-OutputRoot", $ScenarioOutputRoot,
        "-CurrentApkPath", $ApkPath
    )
    if (-not [string]::IsNullOrWhiteSpace($ApkSha256)) {
        $childArgs += @("-CurrentExpectedSha256", $ApkSha256)
    }
    if ($UseAdbRoot) { $childArgs += "-AttemptAdbRoot" }
    if ($UseBugreport) { $childArgs += "-GenerateBugreport" }

    Invoke-ChildPowerShell -PowerShellPath $PowerShellPath -Arguments $childArgs -StepName $ScenarioName
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$sxRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$runner = Join-Path $scriptDir "run-native-ab-matrix.ps1"
$syntaxTest = Join-Path $scriptDir "test-quark-automation-scripts.ps1"
$runtimeTest = Join-Path $scriptDir "test-quark-adb-runtime.ps1"

foreach ($required in @($runner, $syntaxTest, $summarizer, $fixtureScript, $runtimeTest)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required script missing: $required"
    }
}

$currentPowerShell = (Get-Process -Id $PID -ErrorAction Stop).Path
if ([string]::IsNullOrWhiteSpace($currentPowerShell)) {
    throw "Cannot resolve the current PowerShell executable"
}

$syntaxArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $syntaxTest, "-SyntaxOnly")
Invoke-ChildPowerShell -PowerShellPath $currentPowerShell -Arguments $syntaxArgs -StepName "PowerShell syntax gate"

if (-not $SkipFixtureGate) {
    $fixtureArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $fixtureScript)
    Invoke-ChildPowerShell -PowerShellPath $currentPowerShell -Arguments $fixtureArgs -StepName "Evidence fixture gate"
}

Assert-OnlineDevice -Serial $DeviceSerial

$preflightTmpDir = Join-Path $OutputRoot "preflight-$(Get-Date -Format 'yyyyMMdd-HHmmssfff')"
$preflightTmpDirFull = Resolve-FromRoot -Root $sxRoot -Path $preflightTmpDir
$runtimeArgs = @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $runtimeTest,
    "-DeviceSerial", $DeviceSerial,
    "-HostPackage", $HostPackage,
    "-TargetPackage", $TargetPackage,
    "-OutputDirectory", $preflightTmpDirFull
)
Invoke-ChildPowerShell -PowerShellPath $currentPowerShell -Arguments $runtimeArgs -StepName "Real ADB Runtime Preflight"

$preflightJsonPath = Join-Path $preflightTmpDirFull "adb-runtime-preflight.json"
if (-not (Test-Path -LiteralPath $preflightJsonPath -PathType Leaf)) {
    throw "Runtime Preflight JSON missing at $preflightJsonPath"
}
$preflightSha256 = (Get-FileHash -LiteralPath $preflightJsonPath -Algorithm SHA256).Hash.ToUpperInvariant()
Write-Host "[+] ADB Runtime Preflight passed: $preflightJsonPath (SHA256: $preflightSha256)" -ForegroundColor Green

$apkFullPath = Resolve-FromRoot -Root $sxRoot -Path $CurrentApkPath
if (-not (Test-Path -LiteralPath $apkFullPath -PathType Leaf)) {
    throw "Current SX APK not found: $apkFullPath"
}
$currentApkSha256 = (Get-FileHash -LiteralPath $apkFullPath -Algorithm SHA256).Hash.ToUpperInvariant()

$sessionId = "quark-session-$(Get-Date -Format 'yyyyMMdd-HHmmssfff')"
$sessionRootRelative = Join-Path $OutputRoot $sessionId
$sessionRoot = Resolve-FromRoot -Root $sxRoot -Path $sessionRootRelative
New-Item -ItemType Directory -Path $sessionRoot -Force | Out-Null

$startedAt = (Get-Date).ToUniversalTime().ToString("o")
$manifest = [ordered]@{
    schema_version = 1
    session_id = $sessionId
    started_at_utc = $startedAt
    ended_at_utc = $null
    device_serial = $DeviceSerial
    host_package = $HostPackage
    target_package = $TargetPackage
    virtual_user_id = $VirtualUserId
    observation_seconds = $ObservationSeconds
    sandbox_runs = $SandboxRuns
    sx_apk_path = $apkFullPath
    sx_apk_sha256 = $currentApkSha256
    runtime_preflight_json = $preflightJsonPath
    runtime_preflight_sha256 = $preflightSha256
    scenarios = @()
    status = "RUNNING"
    error = $null
}
$manifestPath = Join-Path $sessionRoot "session-manifest.json"
$manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

try {
    $q0Root = Join-Path $sessionRootRelative "Q0-system-direct"
    Invoke-MatrixScenario `
        -PowerShellPath $currentPowerShell `
        -RunnerPath $runner `
        -ScenarioName "Q0 system-direct Quark baseline" `
        -Combo "A7" `
        -Runs 1 `
        -ScenarioOutputRoot $q0Root `
        -ApkPath $CurrentApkPath `
        -ApkSha256 $null `
        -Serial $DeviceSerial `
        -HostPackageName $HostPackage `
        -Target $TargetPackage `
        -UserId $VirtualUserId `
        -TimeoutSeconds $ObservationSeconds `
        -UseAdbRoot:$AttemptAdbRoot `
        -UseBugreport:$GenerateBugreport
    $manifest.scenarios += [ordered]@{ name = "Q0"; combo = "A7"; runs = 1; output_root = $q0Root }
    $manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

    $q1Root = Join-Path $sessionRootRelative "Q1-sx-default"
    Invoke-MatrixScenario `
        -PowerShellPath $currentPowerShell `
        -RunnerPath $runner `
        -ScenarioName "Q1 SX Quark with flags 63" `
        -Combo "A1" `
        -Runs $SandboxRuns `
        -ScenarioOutputRoot $q1Root `
        -ApkPath $CurrentApkPath `
        -ApkSha256 $currentApkSha256 `
        -Serial $DeviceSerial `
        -HostPackageName $HostPackage `
        -Target $TargetPackage `
        -UserId $VirtualUserId `
        -TimeoutSeconds $ObservationSeconds `
        -UseAdbRoot:$AttemptAdbRoot `
        -UseBugreport:$GenerateBugreport
    $manifest.scenarios += [ordered]@{ name = "Q1"; combo = "A1"; runs = $SandboxRuns; output_root = $q1Root }
    $manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

    $q2Root = Join-Path $sessionRootRelative "Q2-sx-native-master-off"
    Invoke-MatrixScenario `
        -PowerShellPath $currentPowerShell `
        -RunnerPath $runner `
        -ScenarioName "Q2 SX Quark with flags 47" `
        -Combo "A6" `
        -Runs $SandboxRuns `
        -ScenarioOutputRoot $q2Root `
        -ApkPath $CurrentApkPath `
        -ApkSha256 $currentApkSha256 `
        -Serial $DeviceSerial `
        -HostPackageName $HostPackage `
        -Target $TargetPackage `
        -UserId $VirtualUserId `
        -TimeoutSeconds $ObservationSeconds `
        -UseAdbRoot:$AttemptAdbRoot `
        -UseBugreport:$GenerateBugreport
    $manifest.scenarios += [ordered]@{ name = "Q2"; combo = "A6"; runs = $SandboxRuns; output_root = $q2Root }
    $manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

    $summaryArgs = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $summarizer,
        "-SessionRoot", $sessionRootRelative
    )
    Invoke-ChildPowerShell -PowerShellPath $currentPowerShell -Arguments $summaryArgs -StepName "Q3 automated route and crash summary"

    $manifest.status = "PASS"
    $manifest.ended_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    $manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

    Write-Host "[+] Quark automation completed." -ForegroundColor Green
    Write-Host "    Session: $sessionRoot" -ForegroundColor Green
    Write-Host "    Summary: $(Join-Path $sessionRoot 'quark-diagnostic-summary.md')" -ForegroundColor Green
}
catch {
    $manifest.status = "FAILED"
    $manifest.error = $_.Exception.Message
    $manifest.ended_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    $manifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Write-Host "[!] Quark automation stopped: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

exit 0
