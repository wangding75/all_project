<#
.SYNOPSIS
    Validate SX native-crash evidence and fail closed.

.DESCRIPTION
    The gate validates every summary row against its source result.json, process
    identity, flags, status/evidence consistency, tombstone uniqueness/time,
    guest/host provenance, matrix completeness, and optional report binding.
#>

[CmdletBinding()]
param(
    [string]$SummaryPath = "artifacts/native-crash/ab-matrix-summary.json",
    [string]$ArtifactsDir,
    [string]$ReportPath,
    [string[]]$ExpectedCombos = @("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"),
    [ValidateRange(1, 100)][int]$ExpectedRunsPerCombo = 3,
    [switch]$AllowPartial
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Accept either a real string array or a comma-separated CLI value.
$ExpectedCombos = @(
    $ExpectedCombos |
        ForEach-Object { [string]$_ -split "," } |
        ForEach-Object { $_.Trim() } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
)

function ConvertTo-CanonicalNode {
    param([AllowNull()]$Value)

    if ($null -eq $Value) { return $null }
    if ($Value -is [string] -or $Value -is [ValueType]) { return $Value }

    if ($Value -is [System.Collections.IDictionary]) {
        $ordered = [ordered]@{}
        foreach ($key in @($Value.Keys | Sort-Object)) {
            $ordered[[string]$key] = ConvertTo-CanonicalNode -Value $Value[$key]
        }
        return $ordered
    }

    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $ordered = [ordered]@{}
        foreach ($property in @($Value.PSObject.Properties.Name | Sort-Object)) {
            $ordered[$property] = ConvertTo-CanonicalNode -Value $Value.$property
        }
        return $ordered
    }

    if (($Value -is [System.Collections.IEnumerable]) -and -not ($Value -is [string])) {
        $items = @()
        foreach ($item in $Value) { $items += ,(ConvertTo-CanonicalNode -Value $item) }
        return @($items)
    }

    return [string]$Value
}

function Get-CanonicalJson {
    param([AllowNull()]$Value)
    (ConvertTo-CanonicalNode -Value $Value) | ConvertTo-Json -Depth 100 -Compress
}

function Add-Error {
    param([string]$Message)
    $script:Errors.Add($Message)
}

function Test-StringField {
    param([AllowNull()]$Value, [string]$FieldName, [string]$RunLabel)
    if ($null -eq $Value) { return }
    $text = [string]$Value
    if ($text -match "\r|\n") { Add-Error "${RunLabel}: $FieldName contains a newline" }
    if ($text.Length -gt 512) { Add-Error "${RunLabel}: $FieldName exceeds 512 characters" }
}

function Resolve-FromRoot {
    param([string]$Root, [string]$Path)
    if ([IO.Path]::IsPathRooted($Path)) { return $Path }
    Join-Path $Root $Path
}

$script:Errors = [System.Collections.Generic.List[string]]::new()
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$sxRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$summaryFullPath = Resolve-FromRoot -Root $sxRoot -Path $SummaryPath

if (-not $ArtifactsDir) {
    $ArtifactsDir = Split-Path -Parent $SummaryPath
}
$artifactsFullPath = Resolve-FromRoot -Root $sxRoot -Path $ArtifactsDir

# Accept a comma-separated value from external powershell.exe invocation.
$normalizedCombos = @()
foreach ($entry in @($ExpectedCombos)) {
    foreach ($part in ([string]$entry -split ',')) {
        if (-not [string]::IsNullOrWhiteSpace($part)) { $normalizedCombos += $part.Trim() }
    }
}
$ExpectedCombos = @($normalizedCombos | Select-Object -Unique)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " SX Native Diagnostics Evidence Gate" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath $summaryFullPath)) {
    Add-Error "Summary file is missing: $summaryFullPath"
} elseif (-not (Test-Path -LiteralPath $artifactsFullPath)) {
    Add-Error "Artifacts directory is missing: $artifactsFullPath"
}

$summaryRows = [System.Collections.Generic.List[object]]::new()
if ($script:Errors.Count -eq 0) {
    try {
        $parsedJson = Get-Content -LiteralPath $summaryFullPath -Raw | ConvertFrom-Json
        if ($parsedJson -is [System.Collections.IEnumerable] -and -not ($parsedJson -is [string])) {
            foreach ($item in $parsedJson) { $summaryRows.Add($item) }
        } elseif ($null -ne $parsedJson) {
            $summaryRows.Add($parsedJson)
        }
    } catch {
        Add-Error "Summary JSON cannot be parsed: $($_.Exception.Message)"
    }
}

$seenRunIds = @{}
$seenRunLabels = @{}
$seenRunDirectories = @{}
$seenTombstones = @{}
$countByCombo = @{}

foreach ($row in $summaryRows) {
    $runLabel = [string]$row.run_label
    $runId = [string]$row.run_id
    $combo = [string]$row.combo
    $status = [string]$row.status

    if ([string]::IsNullOrWhiteSpace($runId)) { Add-Error "Summary row has an empty run_id"; continue }
    if ([string]::IsNullOrWhiteSpace($runLabel)) { Add-Error "${runId}: run_label is empty" }
    if ([string]::IsNullOrWhiteSpace($combo)) { Add-Error "${runId}: combo is empty" }

    if ($seenRunIds.ContainsKey($runId)) { Add-Error "Duplicate run_id: $runId" } else { $seenRunIds[$runId] = $true }
    if ($seenRunLabels.ContainsKey($runLabel)) { Add-Error "Duplicate run_label: $runLabel" } else { $seenRunLabels[$runLabel] = $true }

    if (-not $countByCombo.ContainsKey($combo)) { $countByCombo[$combo] = 0 }
    $countByCombo[$combo]++

    $runDirectoryValue = [string]$row.run_directory
    if ([string]::IsNullOrWhiteSpace($runDirectoryValue)) {
        Add-Error "${runLabel}: run_directory is empty"
        continue
    }
    $runDirectory = Resolve-FromRoot -Root $sxRoot -Path $runDirectoryValue
    $normalizedRunDirectory = [IO.Path]::GetFullPath($runDirectory).TrimEnd('\', '/')
    if ($seenRunDirectories.ContainsKey($normalizedRunDirectory)) {
        Add-Error "${runLabel}: run directory is reused by another row"
    } else {
        $seenRunDirectories[$normalizedRunDirectory] = $runLabel
    }

    if (-not (Test-Path -LiteralPath $normalizedRunDirectory -PathType Container)) {
        Add-Error "${runLabel}: run directory is missing: $normalizedRunDirectory"
        continue
    }

    $resultPath = Join-Path $normalizedRunDirectory "result.json"
    if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
        Add-Error "${runLabel}: result.json is missing"
        continue
    }

    try {
        $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
    } catch {
        Add-Error "${runLabel}: result.json cannot be parsed: $($_.Exception.Message)"
        continue
    }

    if ((Get-CanonicalJson -Value $row) -ne (Get-CanonicalJson -Value $result)) {
        Add-Error "${runLabel}: summary row differs from result.json"
    }

    if ($result.schema_version -lt 3) { Add-Error "${runLabel}: unsupported schema_version $($result.schema_version)" }
    if (-not $result.target_started) { Add-Error "${runLabel}: target_started is false" }
    if ($status -eq "INVALID_EVIDENCE" -or $status -eq "TARGET_NOT_STARTED") {
        Add-Error "${runLabel}: invalid status cannot enter a trusted summary: $status"
    }

    $target = $result.target_process
    if ($result.target_started) {
        if ($null -eq $target) {
            Add-Error "${runLabel}: target_process is missing"
        } else {
            if ([int]$target.pid -le 0) { Add-Error "${runLabel}: target PID is invalid" }
            if ([int]$target.uid -lt 0) { Add-Error "${runLabel}: target UID is invalid" }
            if ([string]::IsNullOrWhiteSpace([string]$target.cmdline)) { Add-Error "${runLabel}: target cmdline is empty" }
            if ([string]::IsNullOrWhiteSpace([string]$target.starttime)) { Add-Error "${runLabel}: target starttime is empty" }
        }
    }

    if ($result.mode -eq "sx_sandbox") {
        if ([int]$result.requested_flags -ne [int]$result.applied_flags) {
            Add-Error "${runLabel}: requested/applied flags differ"
        }
        if ($combo -eq "A0") {
            if ($result.binding_evidence_source -ne "new_exact_sandbox_process") {
                Add-Error "${runLabel}: A0 must use exact new-process discovery"
            }
            if ($result.flags_evidence_source -ne "system_property") {
                Add-Error "${runLabel}: A0 flags must be identified as system-property evidence"
            }
        } else {
            if ($result.binding_evidence_source -ne "SX_TARGET_BOUND") {
                Add-Error "${runLabel}: sandbox run lacks SX_TARGET_BOUND evidence"
            }
            if ($result.flags_evidence_source -ne "SX_TARGET_BOUND") {
                Add-Error "${runLabel}: sandbox run lacks process-applied flag evidence"
            }
        }
        if ($null -ne $target -and [int]$target.uid -ne [int]$result.host_uid) {
            Add-Error "${runLabel}: sandbox target UID does not equal host UID"
        }
        if ($null -ne $target -and [string]$target.cmdline -ne [string]$result.target_package) {
            Add-Error "${runLabel}: sandbox target cmdline is not the exact virtual main process"
        }
    } elseif ($result.mode -eq "system_direct") {
        if ($result.binding_evidence_source -ne "new_exact_system_process") {
            Add-Error "${runLabel}: system-direct run lacks exact new-process evidence"
        }
        if ($result.flags_evidence_source -ne "system_direct") {
            Add-Error "${runLabel}: system-direct flags evidence is invalid"
        }
        if ([int]$result.requested_flags -ne 0 -or [int]$result.applied_flags -ne 0) {
            Add-Error "${runLabel}: system-direct flags must both be zero"
        }
        if ($null -ne $target -and [string]$target.cmdline -ne [string]$result.target_package) {
            Add-Error "${runLabel}: A7 cmdline is not the exact target main process"
        }
        if ($null -ne $target -and $null -ne $result.host_uid -and [int]$target.uid -eq [int]$result.host_uid) {
            Add-Error "${runLabel}: A7 is monitoring the host UID instead of the system target UID"
        }
    } else {
        Add-Error "${runLabel}: unknown mode '$($result.mode)'"
    }

    $crashEvent = $result.crash_event
    $childEvents = @($result.child_crash_events)

    switch ($status) {
        "PASS_TIMEOUT_ALIVE" {
            if (-not $result.process_alive_at_end) { Add-Error "${runLabel}: timeout pass but target is not alive at end" }
            if ($null -ne $crashEvent) { Add-Error "${runLabel}: timeout pass contains a crash_event" }
            if ($childEvents.Count -gt 0) { Add-Error "${runLabel}: timeout pass contains child crash events" }
            if ($null -ne $result.tombstone -or $null -ne $result.guest -or $null -ne $result.host) {
                Add-Error "${runLabel}: timeout pass contains crash evidence fields"
            }
        }
        "NATIVE_CRASH" {
            if ($null -eq $crashEvent) {
                Add-Error "${runLabel}: NATIVE_CRASH has no crash_event"
            } else {
                if ($crashEvent.kind -ne "native") { Add-Error "${runLabel}: NATIVE_CRASH event kind is not native" }
                if ([int]$crashEvent.pid -ne [int]$target.pid) { Add-Error "${runLabel}: native crash PID does not equal target PID" }
                if ([string]::IsNullOrWhiteSpace([string]$crashEvent.signal)) { Add-Error "${runLabel}: native crash has no signal" }
                if ([string]::IsNullOrWhiteSpace([string]$crashEvent.fatal_line)) { Add-Error "${runLabel}: native crash has no fatal line" }
                if ($crashEvent.source -ne "crash_buffer" -and $crashEvent.source -ne "tombstone") {
                    Add-Error "${runLabel}: unsupported native crash evidence source"
                }
            }
        }
        "CHILD_NATIVE_CRASH" {
            if ($null -eq $crashEvent) {
                Add-Error "${runLabel}: CHILD_NATIVE_CRASH has no crash_event"
            } else {
                if ($crashEvent.kind -ne "native") { Add-Error "${runLabel}: child event kind is not native" }
                if ([int]$crashEvent.pid -eq [int]$target.pid) { Add-Error "${runLabel}: child crash PID equals target PID" }
                if (-not ([string]$crashEvent.cmdline).StartsWith([string]$result.target_package)) {
                    Add-Error "${runLabel}: child crash cmdline is unrelated to target package"
                }
                if ($null -eq $crashEvent.process) {
                    Add-Error "${runLabel}: child crash lacks observed process metadata"
                } else {
                    if ([int]$crashEvent.process.pid -ne [int]$crashEvent.pid) { Add-Error "${runLabel}: child process metadata PID mismatch" }
                    if ([int]$crashEvent.process.uid -ne [int]$target.uid) { Add-Error "${runLabel}: child crash UID differs from virtual target UID" }
                    if (-not ([string]$crashEvent.process.cmdline).StartsWith([string]$result.target_package)) { Add-Error "${runLabel}: child process metadata cmdline is unrelated" }
                }
                if ([string]::IsNullOrWhiteSpace([string]$crashEvent.signal)) { Add-Error "${runLabel}: child native crash has no signal" }
            }
            if ($childEvents.Count -eq 0) { Add-Error "${runLabel}: child status has no child_crash_events collection" }
        }
        "JAVA_CRASH" {
            if ($null -eq $crashEvent -or $crashEvent.kind -ne "java") { Add-Error "${runLabel}: JAVA_CRASH lacks a Java crash event" }
            elseif ([int]$crashEvent.pid -ne [int]$target.pid) { Add-Error "${runLabel}: Java crash PID does not equal target PID" }
        }
        "PROCESS_LOST" {
            if ($null -ne $crashEvent) { Add-Error "${runLabel}: PROCESS_LOST contains a crash_event" }
            if ($null -ne $result.tombstone -or $null -ne $result.guest -or $null -ne $result.host) {
                Add-Error "${runLabel}: PROCESS_LOST contains crash evidence fields"
            }
        }
        default {
            Add-Error "${runLabel}: unsupported status '$status'"
        }
    }

    if ($null -ne $result.tombstone) {
        $tomb = $result.tombstone
        if (-not $tomb.is_new_or_changed) { Add-Error "${runLabel}: tombstone is not marked new/changed" }
        if ([string]::IsNullOrWhiteSpace([string]$tomb.identity)) { Add-Error "${runLabel}: tombstone identity is empty" }
        if ($seenTombstones.ContainsKey([string]$tomb.identity)) {
            Add-Error "${runLabel}: tombstone identity is reused by $($seenTombstones[[string]$tomb.identity])"
        } else {
            $seenTombstones[[string]$tomb.identity] = $runLabel
        }
        if ($null -ne $crashEvent -and [int]$tomb.pid -ne [int]$crashEvent.pid) {
            Add-Error "${runLabel}: tombstone PID differs from crash-event PID"
        }

        try {
            $startEpoch = [DateTimeOffset]::Parse([string]$result.started_at_utc).ToUnixTimeSeconds()
            $endEpoch = [DateTimeOffset]::Parse([string]$result.ended_at_utc).ToUnixTimeSeconds()
            if ([long]$tomb.mtime_epoch -lt ($startEpoch - 10) -or [long]$tomb.mtime_epoch -gt ($endEpoch + 10)) {
                Add-Error "${runLabel}: tombstone mtime lies outside the run window"
            }
        } catch {
            Add-Error "${runLabel}: timestamps cannot be parsed for tombstone validation"
        }

        $evidencePath = Join-Path $normalizedRunDirectory ([string]$tomb.evidence_file)
        if (-not (Test-Path -LiteralPath $evidencePath -PathType Leaf)) {
            Add-Error "${runLabel}: matched tombstone evidence file is missing"
        }
    }

    if ($null -ne $result.guest) {
        if ($result.guest.evidence_source -ne "guest_minidump" -and $result.guest.evidence_source -ne "native_bridge_guest_log") {
            Add-Error "${runLabel}: guest evidence has an invalid source"
        }
        Test-StringField -Value $result.guest.module -FieldName "guest.module" -RunLabel $runLabel
    }
    if ($null -ne $result.host) {
        if ($result.host.evidence_source -ne "tombstone" -and $result.host.evidence_source -ne "debuggerd") {
            Add-Error "${runLabel}: host evidence has an invalid source"
        }
        Test-StringField -Value $result.host.module -FieldName "host.module" -RunLabel $runLabel
    }

    if ($null -ne $result.guest -and $result.guest.evidence_source -eq "tombstone") {
        Add-Error "${runLabel}: guest and host evidence sources are mixed"
    }
    if ($null -ne $result.host -and $result.host.evidence_source -eq "guest_minidump") {
        Add-Error "${runLabel}: host and guest evidence sources are mixed"
    }

    if ($null -ne $crashEvent) {
        $crashLogPath = Join-Path $normalizedRunDirectory "logcat-crash.txt"
        if (-not (Test-Path -LiteralPath $crashLogPath -PathType Leaf)) {
            Add-Error "${runLabel}: crash event exists but logcat-crash.txt is missing"
        }
    }
}

if (-not $AllowPartial) {
    foreach ($combo in $ExpectedCombos) {
        $actual = if ($countByCombo.ContainsKey($combo)) { [int]$countByCombo[$combo] } else { 0 }
        if ($actual -ne $ExpectedRunsPerCombo) {
            Add-Error "Combo $combo has $actual runs; expected $ExpectedRunsPerCombo"
        }
    }
    foreach ($actualCombo in $countByCombo.Keys) {
        if ($ExpectedCombos -notcontains $actualCombo) { Add-Error "Unexpected combo in summary: $actualCombo" }
    }
} else {
    foreach ($actualCombo in $countByCombo.Keys) {
        if ($ExpectedCombos -notcontains $actualCombo) { Add-Error "Unexpected combo in partial summary: $actualCombo" }
        if ([int]$countByCombo[$actualCombo] -gt $ExpectedRunsPerCombo) {
            Add-Error "Partial summary has too many runs for $actualCombo"
        }
    }
}

if ($ReportPath) {
    $reportFullPath = Resolve-FromRoot -Root $sxRoot -Path $ReportPath
    if (-not (Test-Path -LiteralPath $reportFullPath -PathType Leaf)) {
        Add-Error "Report file is missing: $reportFullPath"
    } else {
        $summaryHash = (Get-FileHash -LiteralPath $summaryFullPath -Algorithm SHA256).Hash.ToUpperInvariant()
        $reportText = Get-Content -LiteralPath $reportFullPath -Raw
        $hashMatch = [regex]::Match($reportText, "(?im)^Diagnostic-Summary-SHA256:\s*([0-9a-f]{64})\s*$")
        if (-not $hashMatch.Success) {
            Add-Error "Report does not contain Diagnostic-Summary-SHA256"
        } elseif ($hashMatch.Groups[1].Value.ToUpperInvariant() -ne $summaryHash) {
            Add-Error "Report is bound to a different summary SHA-256"
        }

        $hasBoundaryCombos = ($countByCombo.ContainsKey("C1") -and $countByCombo.ContainsKey("C2") -and $countByCombo.ContainsKey("C3"))
        if (-not $hasBoundaryCombos -and $reportText -match "(?i)CONFIRMED_SERVICE_ESCAPE|CONFIRMED[_ ]ROOT[_ ]CAUSE|已确认服务逃逸") {
            Add-Error "Report claims a confirmed service escape/root cause without valid C1-C3 evidence"
        }
    }
}

if ($script:Errors.Count -eq 0) {
    Write-Host "[+] EVIDENCE GATE PASSED" -ForegroundColor Green
    exit 0
}

Write-Host "[!] EVIDENCE GATE FAILED: $($script:Errors.Count) error(s)" -ForegroundColor Red
foreach ($errorMessage in $script:Errors) {
    Write-Host "    - $errorMessage" -ForegroundColor Red
}
exit 1
