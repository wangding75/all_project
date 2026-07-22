<#
.SYNOPSIS
    Positive and negative fixtures for validate-native-diagnostics.ps1.
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$sxRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$validator = Join-Path $scriptDir "validate-native-diagnostics.ps1"
$fixtureRootRelative = "artifacts/native-crash-fixtures"
$fixtureRoot = Join-Path $sxRoot $fixtureRootRelative

if (-not (Test-Path -LiteralPath $validator)) { throw "Validator not found: $validator" }

function Assert-ScriptPreflight {
    param([string[]]$ScriptPaths)

    $readOnlyAutomaticVariables = @(
        "PID", "Host", "HOME", "ExecutionContext", "PSVersionTable",
        "PSEdition", "PSHOME", "PWD", "ShellId", "True", "False", "Null",
        "MyInvocation", "PSCommandPath", "PSScriptRoot"
    )

    foreach ($scriptPath in $ScriptPaths) {
        if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
            throw "Preflight script is missing: $scriptPath"
        }

        $tokens = $null
        $parseErrors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile(
            $scriptPath,
            [ref]$tokens,
            [ref]$parseErrors
        )

        if (@($parseErrors).Count -gt 0) {
            $details = @($parseErrors | ForEach-Object {
                "line $($_.Extent.StartLineNumber), column $($_.Extent.StartColumnNumber): $($_.Message)"
            }) -join [Environment]::NewLine
            throw "PowerShell parser rejected '$scriptPath':$([Environment]::NewLine)$details"
        }

        $parameterAsts = @($ast.FindAll({
            param($node)
            $node -is [System.Management.Automation.Language.ParameterAst]
        }, $true))
        foreach ($parameterAst in $parameterAsts) {
            $name = $parameterAst.Name.VariablePath.UserPath
            if ($readOnlyAutomaticVariables -contains $name) {
                throw "Read-only automatic variable '$name' is used as a parameter in '$scriptPath' at line $($parameterAst.Extent.StartLineNumber)"
            }
        }

        $assignmentAsts = @($ast.FindAll({
            param($node)
            $node -is [System.Management.Automation.Language.AssignmentStatementAst]
        }, $true))
        foreach ($assignmentAst in $assignmentAsts) {
            if ($assignmentAst.Left -is [System.Management.Automation.Language.VariableExpressionAst]) {
                $name = $assignmentAst.Left.VariablePath.UserPath
                if ($readOnlyAutomaticVariables -contains $name) {
                    throw "Read-only automatic variable '$name' is assigned in '$scriptPath' at line $($assignmentAst.Extent.StartLineNumber)"
                }
            }
        }
    }
}

$scriptPaths = @(
    $MyInvocation.MyCommand.Definition,
    $validator,
    (Join-Path $scriptDir "collect-native-crash.ps1"),
    (Join-Path $scriptDir "run-native-ab-matrix.ps1")
)
Assert-ScriptPreflight -ScriptPaths $scriptPaths
Write-Host "[+] PowerShell parser and automatic-variable preflight passed." -ForegroundColor Green

if (Test-Path -LiteralPath $fixtureRoot) { Remove-Item -LiteralPath $fixtureRoot -Recurse -Force }
New-Item -ItemType Directory -Path $fixtureRoot -Force | Out-Null

function Clone-Object {
    param($Value)
    $Value | ConvertTo-Json -Depth 50 | ConvertFrom-Json
}

function New-BaseResult {
    param(
        [string]$CaseRootRelative,
        [string]$RunLabel = "A1_run1",
        [string]$Combo = "A1",
        [string]$Status = "PASS_TIMEOUT_ALIVE",
        [string]$Mode = "sx_sandbox"
    )

    $runId = "fixture-$RunLabel"
    [ordered]@{
        schema_version       = 3
        commit               = "fixture-commit"
        run_id               = $runId
        combo                = $Combo
        run_label            = $RunLabel
        mode                 = $Mode
        run_directory        = (Join-Path $CaseRootRelative $runId)
        started_at_utc       = "2026-07-21T10:00:00.0000000Z"
        target_bound_at_utc  = "2026-07-21T10:00:01.0000000Z"
        ended_at_utc         = "2026-07-21T10:03:00.0000000Z"
        target_started       = $true
        status               = $Status
        survival_seconds     = 180
        requested_flags      = if ($Mode -eq "system_direct") { 0 } else { 63 }
        applied_flags        = if ($Mode -eq "system_direct") { 0 } else { 63 }
        binding_evidence_source = if ($Mode -eq "system_direct") { "new_exact_system_process" } else { "SX_TARGET_BOUND" }
        flags_evidence_source   = if ($Mode -eq "system_direct") { "system_direct" } else { "SX_TARGET_BOUND" }
        host_package         = "com.sx.app.debug"
        host_uid             = 10047
        target_package       = "com.quark.browser"
        target_process       = [ordered]@{
            pid       = 1234
            ppid      = 1000
            uid       = if ($Mode -eq "system_direct") { 10046 } else { 10047 }
            cmdline   = "com.quark.browser"
            starttime = "777777"
        }
        process_alive_at_end = ($Status -eq "PASS_TIMEOUT_ALIVE" -or $Status -eq "CHILD_NATIVE_CRASH")
        crash_event          = $null
        child_crash_events   = @()
        tombstone            = $null
        guest                = $null
        host                 = $null
        device               = [ordered]@{
            serial        = "fixture-device"
            android       = "12"
            sdk           = "31"
            abi_list      = "x86_64,arm64-v8a"
            native_bridge = "libndk_translation.so"
        }
        artifacts            = [ordered]@{
            launch_log        = "launch.log"
            live_logcat       = "logcat-live.txt"
            full_logcat       = "logcat-all.txt"
            crash_logcat      = "logcat-crash.txt"
            process_before    = "process-before.txt"
            process_after     = "process-after.txt"
            flags             = "applied-flags.txt"
            tombstone_before  = "tombstone-before.json"
            tombstone_after   = "tombstone-after.json"
            matched_tombstone = $null
            dumpsys_activity  = "dumpsys-activity.txt"
        }
        errors               = @()
    }
}

function Set-NativeCrash {
    param($Result, [int]$CrashPid = 1234)
    $Result.status = "NATIVE_CRASH"
    $Result.process_alive_at_end = $false
    $Result.survival_seconds = 30
    $Result.crash_event = [ordered]@{
        kind       = "native"
        pid        = $CrashPid
        tid        = $CrashPid
        signal     = "SIGSEGV"
        signal_num = 11
        fault_addr = "0x0"
        thread     = "CrRendererMain"
        cmdline    = "com.quark.browser"
        fatal_line = "Fatal signal 11 (SIGSEGV), code 1, fault addr 0x0 in tid $CrashPid, pid $CrashPid"
        source     = "crash_buffer"
    }
    $Result
}

function Set-ChildCrash {
    param($Result)
    $event = [ordered]@{
        kind       = "native"
        pid        = 2234
        tid        = 2235
        signal     = "SIGSEGV"
        signal_num = 11
        fault_addr = "0x0"
        thread     = "Renderer"
        cmdline    = "com.quark.browser:renderer"
        fatal_line = "Fatal signal 11 (SIGSEGV), code 1, fault addr 0x0 in tid 2235, pid 2234"
        source     = "crash_buffer"
        process    = [ordered]@{ pid = 2234; ppid = 1234; uid = 10047; starttime = "888888"; cmdline = "com.quark.browser:renderer" }
    }
    $Result.status = "CHILD_NATIVE_CRASH"
    $Result.process_alive_at_end = $true
    $Result.crash_event = $event
    $Result.child_crash_events = @($event)
    $Result
}

function Add-Tombstone {
    param(
        $Result,
        [string]$Identity = "tombstone_01|1|1784629860|1024",
        [long]$Mtime = 1784629860,
        [bool]$IsNew = $true
    )
    $Result.tombstone = [ordered]@{
        path              = "/data/tombstones/tombstone_01"
        identity          = $Identity
        inode             = "1"
        mtime_epoch       = $Mtime
        size              = 1024
        pid               = [int]$Result.crash_event.pid
        is_new_or_changed = $IsNew
        evidence_file     = "matched-tombstone.txt"
    }
    $Result.artifacts.matched_tombstone = "matched-tombstone.txt"
    $Result
}

function Write-RunFiles {
    param([string]$CaseRoot, $Result)
    $runDir = Join-Path $sxRoot $Result.run_directory
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $runDir "launch.log") -Value "launch" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runDir "logcat-live.txt") -Value "live" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runDir "logcat-all.txt") -Value "all" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runDir "logcat-crash.txt") -Value $(if ($Result.crash_event) { $Result.crash_event.fatal_line } else { "" }) -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runDir "process-before.txt") -Value "before" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runDir "process-after.txt") -Value "after" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runDir "applied-flags.txt") -Value "flags" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runDir "tombstone-before.json") -Value "[]" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runDir "tombstone-after.json") -Value "[]" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $runDir "dumpsys-activity.txt") -Value "activity" -Encoding UTF8
    if ($Result.tombstone) {
        Set-Content -LiteralPath (Join-Path $runDir "matched-tombstone.txt") -Value "pid: $($Result.tombstone.pid)" -Encoding UTF8
    }
    $Result | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath (Join-Path $runDir "result.json") -Encoding UTF8
}

$currentPowerShell = (Get-Process -Id $PID -ErrorAction Stop).Path
if ([string]::IsNullOrWhiteSpace($currentPowerShell) -or -not (Test-Path -LiteralPath $currentPowerShell -PathType Leaf)) {
    throw "Cannot resolve the current PowerShell executable"
}

function Invoke-ValidatorCase {
    param(
        [string]$Name,
        [object[]]$Results,
        [bool]$ShouldPass,
        [scriptblock]$MutateSummary,
        [string]$ReportText,
        [switch]$SkipRunFiles,
        [switch]$CreateRunDirWithoutResult
    )

    $caseRootRelative = Join-Path $fixtureRootRelative $Name
    $caseRoot = Join-Path $sxRoot $caseRootRelative
    New-Item -ItemType Directory -Path $caseRoot -Force | Out-Null

    if (-not $SkipRunFiles) {
        foreach ($result in $Results) { Write-RunFiles -CaseRoot $caseRoot -Result $result }
    } elseif ($CreateRunDirWithoutResult) {
        foreach ($result in $Results) {
            $runDir = Join-Path $sxRoot $result.run_directory
            New-Item -ItemType Directory -Path $runDir -Force | Out-Null
        }
    }

    $summary = @($Results | ForEach-Object { Clone-Object $_ })
    if ($MutateSummary) { & $MutateSummary $summary }
    $summaryPath = Join-Path $caseRoot "ab-matrix-summary.json"
    $summary | ConvertTo-Json -Depth 50 | Set-Content -LiteralPath $summaryPath -Encoding UTF8

    $reportPath = $null
    if ($null -ne $ReportText) {
        $hash = (Get-FileHash -LiteralPath $summaryPath -Algorithm SHA256).Hash.ToUpperInvariant()
        $reportPath = Join-Path $caseRoot "report.md"
        $finalText = "Diagnostic-Summary-SHA256: $hash`n$ReportText"
        Set-Content -LiteralPath $reportPath -Value $finalText -Encoding UTF8
    }

    $combos = @($Results | ForEach-Object { $_.combo } | Select-Object -Unique)
    $expectedRuns = (@($Results | Group-Object combo | Sort-Object Count -Descending | Select-Object -First 1).Count)
    if ($expectedRuns -lt 1) { $expectedRuns = 1 }

    $validatorArgs = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $validator,
        "-SummaryPath", (Join-Path $caseRootRelative "ab-matrix-summary.json"),
        "-ArtifactsDir", $caseRootRelative,
        "-ExpectedCombos", ($combos -join ","),
        "-ExpectedRunsPerCombo", "$expectedRuns"
    )
    if ($reportPath) { $validatorArgs += @("-ReportPath", (Join-Path $caseRootRelative "report.md")) }

    # Negative fixtures intentionally make the validator exit 1. In Windows
    # PowerShell 5.1, redirected native stderr can become a NativeCommandError
    # when the caller uses ErrorActionPreference=Stop, so temporarily use
    # Continue while capturing the child process output and exit code.
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & $currentPowerShell @validatorArgs 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    $actualPass = ($exitCode -eq 0)
    $ok = ($actualPass -eq $ShouldPass)

    [pscustomobject]@{
        Name       = $Name
        Expected   = if ($ShouldPass) { "PASS" } else { "FAIL" }
        Actual     = if ($actualPass) { "PASS" } else { "FAIL" }
        Successful = $ok
        Output     = ($output | ForEach-Object { [string]$_ }) -join [Environment]::NewLine
    }
}

$cases = [System.Collections.Generic.List[object]]::new()

# Positive fixtures.
$base = New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "valid-pass")
$cases.Add((Invoke-ValidatorCase -Name "valid-pass" -Results @($base) -ShouldPass $true))

$native = Set-NativeCrash (New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "valid-native"))
$cases.Add((Invoke-ValidatorCase -Name "valid-native" -Results @($native) -ShouldPass $true))

$child = Set-ChildCrash (New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "valid-child"))
$cases.Add((Invoke-ValidatorCase -Name "valid-child" -Results @($child) -ShouldPass $true))

# Negative fixtures.
$r = Set-NativeCrash (New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "native-missing-signal")); $r.crash_event.signal = $null
$cases.Add((Invoke-ValidatorCase -Name "native-missing-signal" -Results @($r) -ShouldPass $false))

$r = Set-NativeCrash (New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "native-wrong-pid")) -CrashPid 9999
$cases.Add((Invoke-ValidatorCase -Name "native-wrong-pid" -Results @($r) -ShouldPass $false))

$r = Add-Tombstone (Set-NativeCrash (New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "old-tombstone"))) -IsNew $false
$cases.Add((Invoke-ValidatorCase -Name "old-tombstone" -Results @($r) -ShouldPass $false))

$r = Add-Tombstone (Set-NativeCrash (New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "tombstone-outside-window"))) -Mtime 1000
$cases.Add((Invoke-ValidatorCase -Name "tombstone-outside-window" -Results @($r) -ShouldPass $false))

$caseRel = Join-Path $fixtureRootRelative "reused-tombstone"
$r1 = Add-Tombstone (Set-NativeCrash (New-BaseResult -CaseRootRelative $caseRel -RunLabel "A1_run1")) -Identity "same-id"
$r2 = Add-Tombstone (Set-NativeCrash (New-BaseResult -CaseRootRelative $caseRel -RunLabel "A1_run2")) -Identity "same-id"
$r2.run_id = "fixture-A1_run2"; $r2.run_directory = Join-Path $caseRel $r2.run_id; $r2.target_process.pid = 1235; $r2.crash_event.pid = 1235; $r2.crash_event.tid = 1235; $r2.tombstone.pid = 1235
$cases.Add((Invoke-ValidatorCase -Name "reused-tombstone" -Results @($r1, $r2) -ShouldPass $false))

$r = New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "flags-mismatch"); $r.applied_flags = 62
$cases.Add((Invoke-ValidatorCase -Name "flags-mismatch" -Results @($r) -ShouldPass $false))

$r = New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "target-uid-mismatch"); $r.target_process.uid = 10046
$cases.Add((Invoke-ValidatorCase -Name "target-uid-mismatch" -Results @($r) -ShouldPass $false))

$r = New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "summary-pid-mismatch")
$cases.Add((Invoke-ValidatorCase -Name "summary-pid-mismatch" -Results @($r) -ShouldPass $false -MutateSummary { param($s) $s[0].target_process.pid = 8888 }))

$r = New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "summary-survival-mismatch")
$cases.Add((Invoke-ValidatorCase -Name "summary-survival-mismatch" -Results @($r) -ShouldPass $false -MutateSummary { param($s) $s[0].survival_seconds = 99 }))

$r = Set-NativeCrash (New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "guest-host-source-mixed")); $r.guest = [ordered]@{ evidence_source = "tombstone"; abi = "arm64"; pid = 1234; tid = 1234; signal = "SIGSEGV"; thread = "x"; pc = "1"; module = "libx.so"; module_offset = "1"; build_id = $null }
$cases.Add((Invoke-ValidatorCase -Name "guest-host-source-mixed" -Results @($r) -ShouldPass $false))

$r = Set-NativeCrash (New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "module-newline")); $r.host = [ordered]@{ evidence_source = "tombstone"; abi = "x86_64"; pid = 1234; tid = 1234; signal = "SIGSEGV"; thread = "x"; pc = "1"; module = "libx.so`nextra"; function = $null; build_id = $null }
$cases.Add((Invoke-ValidatorCase -Name "module-newline" -Results @($r) -ShouldPass $false))

$r = New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "a7-host-pid") -Combo "A7" -Mode "system_direct"; $r.target_process.uid = 10047
$cases.Add((Invoke-ValidatorCase -Name "a7-host-pid" -Results @($r) -ShouldPass $false))

$r = Set-NativeCrash (New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "child-marked-main")) -CrashPid 2234; $r.crash_event.cmdline = "com.quark.browser:renderer"
$cases.Add((Invoke-ValidatorCase -Name "child-marked-main" -Results @($r) -ShouldPass $false))

$r = New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "confirmed-without-c1-c3")
$cases.Add((Invoke-ValidatorCase -Name "confirmed-without-c1-c3" -Results @($r) -ShouldPass $false -ReportText "CONFIRMED_SERVICE_ESCAPE"))

$r = New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "missing-run-directory")
$cases.Add((Invoke-ValidatorCase -Name "missing-run-directory" -Results @($r) -ShouldPass $false -SkipRunFiles))

$r = New-BaseResult -CaseRootRelative (Join-Path $fixtureRootRelative "missing-result-json")
$cases.Add((Invoke-ValidatorCase -Name "missing-result-json" -Results @($r) -ShouldPass $false -SkipRunFiles -CreateRunDirWithoutResult))

$failedCases = @($cases | Where-Object { -not $_.Successful })
$cases | Select-Object Name, Expected, Actual, Successful | Format-Table -AutoSize

if ($failedCases.Count -gt 0) {
    Write-Host "[!] Fixture suite failed:" -ForegroundColor Red
    foreach ($case in $failedCases) {
        Write-Host "--- $($case.Name) ---" -ForegroundColor Red
        Write-Host $case.Output
    }
    exit 1
}

Write-Host "[+] All $($cases.Count) fixture cases passed." -ForegroundColor Green
Remove-Item -LiteralPath $fixtureRoot -Recurse -Force
exit 0
