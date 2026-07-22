<#
.SYNOPSIS
    Build a deterministic Quark diagnostic summary from validated matrix outputs.

.DESCRIPTION
    This script does not decide or repair the root cause. It extracts exact run
    status, bound PID/UID, crash evidence, host/guest frames, service-route lines,
    and relevant Quark/SX process lines into JSON and Markdown summaries.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SessionRoot,
    [ValidateRange(1, 5000)][int]$MaximumEvidenceLinesPerRun = 500
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-FromRoot {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )
    if ([IO.Path]::IsPathRooted($Path)) { return $Path }
    return (Join-Path $Root $Path)
}

function Get-NullableValue {
    param(
        [AllowNull()][object]$Object,
        [Parameter(Mandatory = $true)][string]$PropertyName
    )
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$PropertyName]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-RunDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][object]$Result,
        [Parameter(Mandatory = $true)][string]$SummaryDirectory
    )

    $declared = Get-NullableValue -Object $Result -PropertyName "run_directory"
    if (-not [string]::IsNullOrWhiteSpace([string]$declared)) {
        $candidate = Resolve-FromRoot -Root $Root -Path ([string]$declared)
        if (Test-Path -LiteralPath $candidate -PathType Container) { return $candidate }
    }

    $runId = [string](Get-NullableValue -Object $Result -PropertyName "run_id")
    $fallback = Join-Path $SummaryDirectory $runId
    if (Test-Path -LiteralPath $fallback -PathType Container) { return $fallback }
    throw "Cannot resolve run directory for $runId"
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$sxRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$sessionRootFull = Resolve-FromRoot -Root $sxRoot -Path $SessionRoot
if (-not (Test-Path -LiteralPath $sessionRootFull -PathType Container)) {
    throw "Session root not found: $sessionRootFull"
}

$summaryFiles = @(Get-ChildItem -LiteralPath $sessionRootFull -Filter "ab-matrix-summary.json" -File -Recurse | Sort-Object FullName)
if ($summaryFiles.Count -eq 0) {
    throw "No ab-matrix-summary.json files found under $sessionRootFull"
}

$linePattern = "SX_SERVICE_ROUTE|SX_TARGET_BOUND|BindService|resolveService|ProxyService|BActivityManager|BPackageManager|sandboxed|privilege_process|renderer|libwebviewuc|libndk_translation|Fatal signal|FATAL EXCEPTION|UnsatisfiedLinkError|SecurityException|linker|mmap|ashmem|memfd"
$runSummaries = [System.Collections.Generic.List[object]]::new()

foreach ($summaryFile in $summaryFiles) {
    $rawItems = Get-Content -LiteralPath $summaryFile.FullName -Raw | ConvertFrom-Json
    $items = [System.Collections.Generic.List[object]]::new()
    if ($rawItems -is [System.Collections.IEnumerable] -and -not ($rawItems -is [string])) {
        foreach ($item in $rawItems) { $items.Add($item) }
    } elseif ($null -ne $rawItems) {
        $items.Add($rawItems)
    }
    foreach ($result in $items) {
        $runDirectory = Get-RunDirectory -Root $sxRoot -Result $result -SummaryDirectory $summaryFile.Directory.FullName
        $logcatPath = Join-Path $runDirectory "logcat-all.txt"
        $processAfterPath = Join-Path $runDirectory "process-after.txt"

        $evidenceLines = @()
        if (Test-Path -LiteralPath $logcatPath -PathType Leaf) {
            $evidenceLines = @(
                Select-String -LiteralPath $logcatPath -Pattern $linePattern -CaseSensitive:$false |
                    Select-Object -First $MaximumEvidenceLinesPerRun |
                    ForEach-Object { $_.Line }
            )
        }

        $processLines = @()
        if (Test-Path -LiteralPath $processAfterPath -PathType Leaf) {
            $processLines = @(
                Get-Content -LiteralPath $processAfterPath |
                    Where-Object { $_ -match "com\.quark\.browser|com\.sx\.app" }
            )
        }

        $routeEvidencePath = Join-Path $runDirectory "quark-route-evidence.txt"
        $evidenceLines | Set-Content -LiteralPath $routeEvidencePath -Encoding UTF8

        $targetProcess = Get-NullableValue -Object $result -PropertyName "target_process"
        $crashEvent = Get-NullableValue -Object $result -PropertyName "crash_event"
        $guestFrame = Get-NullableValue -Object $result -PropertyName "guest"
        $hostFrame = Get-NullableValue -Object $result -PropertyName "host"

        $runSummaries.Add([ordered]@{
            combo = Get-NullableValue -Object $result -PropertyName "combo"
            run_id = Get-NullableValue -Object $result -PropertyName "run_id"
            run_label = Get-NullableValue -Object $result -PropertyName "run_label"
            mode = Get-NullableValue -Object $result -PropertyName "mode"
            status = Get-NullableValue -Object $result -PropertyName "status"
            survival_seconds = Get-NullableValue -Object $result -PropertyName "survival_seconds"
            target_started = Get-NullableValue -Object $result -PropertyName "target_started"
            requested_flags = Get-NullableValue -Object $result -PropertyName "requested_flags"
            applied_flags = Get-NullableValue -Object $result -PropertyName "applied_flags"
            target_pid = Get-NullableValue -Object $targetProcess -PropertyName "pid"
            target_uid = Get-NullableValue -Object $targetProcess -PropertyName "uid"
            target_cmdline = Get-NullableValue -Object $targetProcess -PropertyName "cmdline"
            target_starttime = Get-NullableValue -Object $targetProcess -PropertyName "starttime"
            crash_kind = Get-NullableValue -Object $crashEvent -PropertyName "kind"
            crash_pid = Get-NullableValue -Object $crashEvent -PropertyName "pid"
            crash_signal = Get-NullableValue -Object $crashEvent -PropertyName "signal"
            crash_thread = Get-NullableValue -Object $crashEvent -PropertyName "thread"
            crash_cmdline = Get-NullableValue -Object $crashEvent -PropertyName "cmdline"
            guest_abi = Get-NullableValue -Object $guestFrame -PropertyName "abi"
            guest_module = Get-NullableValue -Object $guestFrame -PropertyName "module"
            guest_pc = Get-NullableValue -Object $guestFrame -PropertyName "pc"
            host_abi = Get-NullableValue -Object $hostFrame -PropertyName "abi"
            host_module = Get-NullableValue -Object $hostFrame -PropertyName "module"
            host_pc = Get-NullableValue -Object $hostFrame -PropertyName "pc"
            route_evidence_count = $evidenceLines.Count
            route_evidence_file = $routeEvidencePath
            process_lines = @($processLines)
            run_directory = $runDirectory
        })
    }
}

$allRuns = @($runSummaries)
$q0Runs = @($allRuns | Where-Object { $_.combo -eq "A7" })
$q1Runs = @($allRuns | Where-Object { $_.combo -eq "A1" })
$q2Runs = @($allRuns | Where-Object { $_.combo -eq "A6" })

$totalRouteLines = 0
$hasRouteLines = $false
foreach ($rItem in $allRuns) {
    $cnt = [int]$rItem.route_evidence_count
    $totalRouteLines += $cnt
    if ($cnt -gt 0) { $hasRouteLines = $true }
}

$summary = [ordered]@{
    schema_version = 1
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    session_root = $sessionRootFull
    run_count = $allRuns.Count
    q0_system_direct = [ordered]@{
        run_count = $q0Runs.Count
        statuses = @($q0Runs | ForEach-Object { $_.status })
        baseline_alive = (@($q0Runs | Where-Object { $_.status -eq "PASS_TIMEOUT_ALIVE" }).Count -eq $q0Runs.Count -and $q0Runs.Count -gt 0)
    }
    q1_sx_default = [ordered]@{
        run_count = $q1Runs.Count
        statuses = @($q1Runs | ForEach-Object { $_.status })
    }
    q2_native_master_off = [ordered]@{
        run_count = $q2Runs.Count
        statuses = @($q2Runs | ForEach-Object { $_.status })
    }
    route_evidence = [ordered]@{
        total_matching_lines = $totalRouteLines
        state = if ($hasRouteLines) { "EVIDENCE_COLLECTED" } else { "NO_ROUTE_LOG_LINES" }
    }
    conclusion = "EVIDENCE_ONLY_ROOT_CAUSE_NOT_AUTO_CONFIRMED"
    runs = $allRuns
}

$jsonPath = Join-Path $sessionRootFull "quark-diagnostic-summary.json"
$summary | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$markdown = [System.Collections.Generic.List[string]]::new()
$markdown.Add("# Quark automated diagnostic summary")
$markdown.Add("")
$markdown.Add("- Generated: $($summary.generated_at_utc)")
$markdown.Add("- Session: $sessionRootFull")
$markdown.Add("- Runs: $($summary.run_count)")
$markdown.Add("- Q0 system baseline alive: $($summary.q0_system_direct.baseline_alive)")
$markdown.Add("- Route evidence: $($summary.route_evidence.state), lines=$($summary.route_evidence.total_matching_lines)")
$markdown.Add("- Conclusion: $($summary.conclusion)")
$markdown.Add("")
$markdown.Add("| Combo | Run | Status | Seconds | PID | UID | Flags | Crash PID | Signal | Guest module | Host module | Route lines |")
$markdown.Add("|---|---|---|---:|---:|---:|---|---:|---|---|---|---:|")
foreach ($run in $allRuns) {
    $flagText = "$($run.requested_flags)/$($run.applied_flags)"
    $markdown.Add("| $($run.combo) | $($run.run_label) | $($run.status) | $($run.survival_seconds) | $($run.target_pid) | $($run.target_uid) | $flagText | $($run.crash_pid) | $($run.crash_signal) | $($run.guest_module) | $($run.host_module) | $($run.route_evidence_count) |")
}
$markdown.Add("")
$markdown.Add("## Interpretation boundary")
$markdown.Add("")
$markdown.Add("This file summarizes validated evidence. It does not mark service escape, Native Bridge, UC renderer, mmap, or any hook as the confirmed root cause.")

$markdownPath = Join-Path $sessionRootFull "quark-diagnostic-summary.md"
$markdown | Set-Content -LiteralPath $markdownPath -Encoding UTF8

Write-Host "[+] Quark summary generated." -ForegroundColor Green
Write-Host "    $jsonPath" -ForegroundColor Green
Write-Host "    $markdownPath" -ForegroundColor Green
exit 0
