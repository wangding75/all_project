<#
.SYNOPSIS
    Gate 1 Self-Check Fixtures Test (SX-EH-02)
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SxRootDir = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

$FixtureDir = Join-Path $SxRootDir "artifacts\native-crash-fixtures"
if (Test-Path $FixtureDir) { Remove-Item $FixtureDir -Recurse -Force }
New-Item -ItemType Directory -Path $FixtureDir -Force | Out-Null

Write-Host "Running Gate 1 Fixture Validation Tests..." -ForegroundColor Cyan

# Test Case 1: Valid Data Fixture
$validRunLabel = "A1_run1"
$validRunDir = Join-Path $FixtureDir "20260721-180000-$validRunLabel"
New-Item -ItemType Directory -Path $validRunDir -Force | Out-Null

$validResult = [ordered]@{
    commit = "422d62f"
    run_id = "20260721-180000-$validRunLabel"
    combo = "A1"
    run_label = $validRunLabel
    target_started = $true
    status = "PASS_TIMEOUT_ALIVE"
    survival_seconds = 180
    requested_flags = 63
    applied_flags = 63
    pid = "1234"
    virtual_process = "com.quark.browser"
    guest_abi = "ARM64"
    guest_signal = $null
    guest_thread = $null
    guest_pc = $null
    guest_module = $null
    guest_module_offset = $null
    guest_build_id = $null
    host_abi = $null
    host_pc = $null
    host_module = $null
    host_function = $null
    host_build_id = $null
    tombstone_file = ""
}

$validResult | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $validRunDir "result.json") -Encoding UTF8
$summaryData = @($validResult)
$summaryPath = Join-Path $FixtureDir "ab-matrix-summary.json"
$summaryData | ConvertTo-Json -Depth 5 | Set-Content $summaryPath -Encoding UTF8

$validatorScript = Join-Path $ScriptDir "validate-native-diagnostics.ps1"
& $validatorScript -SummaryPath "artifacts/native-crash-fixtures/ab-matrix-summary.json" -ArtifactsDir "artifacts/native-crash-fixtures"
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "[+] Gate 1 Fixture Test Passed!" -ForegroundColor Green
} else {
    Write-Host "[!] Gate 1 Fixture Test Failed!" -ForegroundColor Red
    exit 1
}

# Clean up fixture dir
Remove-Item $FixtureDir -Recurse -Force
