<#
.SYNOPSIS
    Gate 1 Integrity Validator for SX-EH-02 Native Crash Diagnostics
#>

param(
    [string]$SummaryPath = "artifacts/native-crash/ab-matrix-summary.json",
    [string]$ReportPath = "docs/crash-analysis/native-heavy-app-root-cause.md",
    [string]$ArtifactsDir = "artifacts/native-crash"
)

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SxRootDir = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

$SummaryFullPath = Join-Path $SxRootDir $SummaryPath
$ReportFullPath = Join-Path $SxRootDir $ReportPath
$ArtifactsFullPath = Join-Path $SxRootDir $ArtifactsDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " SX Native Diagnostics Gate 1 Integrity Validator (SX-EH-02)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$errors = @()

if (-not (Test-Path $SummaryFullPath)) {
    $errors += "Summary file missing: $SummaryFullPath"
} else {
    $summaryData = Get-Content $SummaryFullPath -Raw | ConvertFrom-Json
    $seenTombstones = @{}

    foreach ($item in $summaryData) {
        $runLabel = if ($item.run_label) { $item.run_label } else { $item.RunLabel }
        $status = if ($item.status) { $item.status } else { $item.Status }
        $combo = if ($item.combo) { $item.combo } else { $item.Combo }
        $requestedFlags = if ($item.requested_flags -ne $null) { $item.requested_flags } else { $item.RequestedFlags }
        $appliedFlags = if ($item.applied_flags -ne $null) { $item.applied_flags } else { $item.AppliedFlags }
        $targetStarted = if ($item.target_started -ne $null) { $item.target_started } else { $item.TargetStarted }
        $tombstoneFile = if ($item.tombstone_file) { $item.tombstone_file } else { $item.TombstoneFile }
        $hostModule = if ($item.host_module) { $item.host_module } else { $item.HostModule }

        # 1. Run Directory & result.json Check
        $runDirs = Get-ChildItem -Path $ArtifactsFullPath -Directory | Where-Object { $_.Name -like "*-$runLabel" }
        if (-not $runDirs) {
            $errors += "Run directory missing for label $($runLabel)"
            continue
        }
        $runDir = $runDirs[0].FullName
        $resJsonPath = Join-Path $runDir "result.json"
        if (-not (Test-Path $resJsonPath)) {
            $errors += "result.json missing in $($runDir)"
        } else {
            $resJson = Get-Content $resJsonPath -Raw | ConvertFrom-Json
            # Check summary row equals result.json
            if ($resJson.status -ne $status) {
                $errors += "Status mismatch between summary ($status) and result.json ($($resJson.status)) in $($runLabel)"
            }
        }

        # 2. Flag Alignment Check for A1..A6
        if ($combo -ne "A7" -and $targetStarted) {
            if ($requestedFlags -ne $appliedFlags) {
                $errors += "Flags mismatch in $($runLabel): requested=$($requestedFlags), applied=$($appliedFlags)"
            }
        }

        # 3. Crash Field Consistency Check
        if ($status -eq "PROCESS_LOST" -or $status -eq "PASS_TIMEOUT_ALIVE" -or $status -eq "TARGET_NOT_STARTED") {
            if ($hostModule -or $tombstoneFile) {
                $errors += "Non-crash run $($runLabel) (status: $($status)) has populated crash fields! hostModule='$($hostModule)', tombstone='$($tombstoneFile)'"
            }
        }

        # 4. Crash Module String Length & Format Check
        if ($hostModule) {
            if ($hostModule -match "\r|\n") {
                $errors += "Crash module in $($runLabel) contains newlines!"
            }
            if ($hostModule.Length -gt 512) {
                $errors += "Crash module in $($runLabel) exceeds 512 characters ($($hostModule.Length) chars)!"
            }
        }

        # 5. Tombstone Uniqueness Check
        if ($tombstoneFile) {
            if ($seenTombstones.ContainsKey($tombstoneFile)) {
                $errors += "Tombstone file $($tombstoneFile) reused across runs! ($($runLabel) vs $($seenTombstones[$tombstoneFile]))"
            } else {
                $seenTombstones[$tombstoneFile] = $runLabel
            }
        }
    }
}

if ($errors.Count -eq 0) {
    Write-Host "[+] GATE 1 PASSED: All diagnostic data integrity constraints satisfied." -ForegroundColor Green
    exit 0
} else {
    Write-Host "[!] GATE 1 FAILED ($($errors.Count) errors found):" -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host "    - $err" -ForegroundColor Red
    }
    exit 1
}
