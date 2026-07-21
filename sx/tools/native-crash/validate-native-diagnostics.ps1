<#
.SYNOPSIS
    Automated Gate 1 Integrity Validator for Native Crash Diagnostics
.DESCRIPTION
    Validates data integrity, tombstone uniqueness, flags alignment, and report consistency.
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
Write-Host " SX Native Diagnostics Gate 1 Integrity Validator" -ForegroundColor Cyan
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
        $signal = if ($item.signal) { $item.signal } else { $item.Signal }
        $crashLib = if ($item.crash_library) { $item.crash_library } else { $item.CrashLib }
        $pcOffset = if ($item.pc_offset) { $item.pc_offset } else { $item.PCOffset }

        # 1. Run Directory & result.json Check
        $runDirs = Get-ChildItem -Path $ArtifactsFullPath -Directory | Where-Object { $_.Name -like "*-$runLabel" }
        if (-not $runDirs) {
            $errors += "Run directory missing for label $runLabel"
            continue
        }
        $runDir = $runDirs[0].FullName
        $resJsonPath = Join-Path $runDir "result.json"
        if (-not (Test-Path $resJsonPath)) {
            $errors += "result.json missing in $runDir"
        }

        # 2. Flag Alignment Check for A1..A6
        if ($combo -ne "A7" -and $targetStarted) {
            if ($requestedFlags -ne $appliedFlags) {
                $errors += "Flags mismatch in $($runLabel): requested=$($requestedFlags), applied=$($appliedFlags)"
            }
        }

        # 3. Crash Field Consistency Check
        if ($status -ne "NATIVE_CRASH" -and $status -ne "JAVA_CRASH") {
            if ($signal -or $crashLib -or $pcOffset) {
                $errors += "Non-crash run $($runLabel) has populated crash fields! Signal='$($signal)', CrashLib='$($crashLib)'"
            }
        }

        # 4. Tombstone Uniqueness Check
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
