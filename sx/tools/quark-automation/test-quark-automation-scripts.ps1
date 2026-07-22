<#
.SYNOPSIS
    Parse the exact PowerShell scripts shipped in the Quark automation package
    and optionally run the evidence fixtures.

.DESCRIPTION
    This gate intentionally validates only the package manifest below. It does
    not parse unrelated or legacy scripts that may exist in the destination
    directory.
#>

[CmdletBinding()]
param(
    [switch]$SyntaxOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

$packageScriptNames = @(
    "collect-native-crash.ps1",
    "run-native-ab-matrix.ps1",
    "validate-native-diagnostics.ps1",
    "test-gate1-fixtures.ps1",
    "run-quark-diagnostics.ps1",
    "summarize-quark-diagnostics.ps1",
    "test-quark-automation-scripts.ps1",
    "test-quark-adb-runtime.ps1"
)

$missingScripts = @(
    $packageScriptNames |
        Where-Object {
            -not (Test-Path -LiteralPath (Join-Path $scriptDir $_) -PathType Leaf)
        }
)

if ($missingScripts.Count -gt 0) {
    Write-Host "[!] Package script manifest is incomplete:" -ForegroundColor Red
    $missingScripts | ForEach-Object {
        Write-Host "    missing: $_" -ForegroundColor Red
    }
    exit 1
}

$scriptFiles = @(
    $packageScriptNames |
        ForEach-Object { Get-Item -LiteralPath (Join-Path $scriptDir $_) } |
        Sort-Object Name
)

$unrelatedScripts = @(
    Get-ChildItem -LiteralPath $scriptDir -Filter "*.ps1" -File |
        Where-Object { $packageScriptNames -notcontains $_.Name } |
        Sort-Object Name
)

if ($unrelatedScripts.Count -gt 0) {
    Write-Host "[i] Ignoring unrelated PowerShell scripts not listed in the package manifest:" -ForegroundColor DarkYellow
    $unrelatedScripts | ForEach-Object {
        Write-Host "    $($_.Name)" -ForegroundColor DarkYellow
    }
}

$readOnlyAutomaticVariables = @(
    "PID", "Host", "HOME", "ExecutionContext", "PSVersionTable",
    "PSEdition", "PSHOME", "PWD", "ShellId", "True", "False", "Null",
    "MyInvocation", "PSCommandPath", "PSScriptRoot"
)

$preflightFailures = [System.Collections.Generic.List[string]]::new()

foreach ($file in $scriptFiles) {
    $tokens = $null
    $parseErrors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile(
        $file.FullName,
        [ref]$tokens,
        [ref]$parseErrors
    )

    foreach ($parseError in @($parseErrors)) {
        $preflightFailures.Add(
            "$($file.Name):$($parseError.Extent.StartLineNumber):$($parseError.Extent.StartColumnNumber): $($parseError.Message)"
        )
    }

    $parameterAsts = @(
        $ast.FindAll({
            param($node)
            $node -is [System.Management.Automation.Language.ParameterAst]
        }, $true)
    )

    foreach ($parameterAst in $parameterAsts) {
        $name = $parameterAst.Name.VariablePath.UserPath
        if ($readOnlyAutomaticVariables -contains $name) {
            $preflightFailures.Add(
                "$($file.Name):$($parameterAst.Extent.StartLineNumber): read-only automatic variable '$name' is used as a parameter"
            )
        }
    }

    $assignmentAsts = @(
        $ast.FindAll({
            param($node)
            $node -is [System.Management.Automation.Language.AssignmentStatementAst]
        }, $true)
    )

    foreach ($assignmentAst in $assignmentAsts) {
        if ($assignmentAst.Left -is [System.Management.Automation.Language.VariableExpressionAst]) {
            $name = $assignmentAst.Left.VariablePath.UserPath
            if ($readOnlyAutomaticVariables -contains $name) {
                $preflightFailures.Add(
                    "$($file.Name):$($assignmentAst.Extent.StartLineNumber): read-only automatic variable '$name' is assigned"
                )
            }
        }
    }
}

# Static assertions
$collectContent = Get-Content -LiteralPath (Join-Path $scriptDir "collect-native-crash.ps1") -Raw
if ($collectContent -match '"shell",\s*"sh",\s*"-c"') {
    $preflightFailures.Add("collect-native-crash.ps1: contains legacy 'shell', 'sh', '-c' transport pattern")
}
if ($collectContent -notmatch '"shell",\s*\$normalizedCommand') {
    $preflightFailures.Add("collect-native-crash.ps1: missing direct single-parameter shell transport")
}
if ($collectContent -notmatch "package-uid-pm-" -or $collectContent -notmatch "package-uid-dumpsys-") {
    $preflightFailures.Add("collect-native-crash.ps1: missing dual level pm and dumpsys UID resolution logging")
}

$driverContent = Get-Content -LiteralPath (Join-Path $scriptDir "run-quark-diagnostics.ps1") -Raw
if ($driverContent -notmatch "test-quark-adb-runtime\.ps1") {
    $preflightFailures.Add("run-quark-diagnostics.ps1: does not invoke test-quark-adb-runtime.ps1")
}

if ($packageScriptNames -notcontains "test-quark-adb-runtime.ps1") {
    $preflightFailures.Add("packageScriptNames does not contain test-quark-adb-runtime.ps1")
}

if ($preflightFailures.Count -gt 0) {
    Write-Host "[!] PowerShell package preflight failed:" -ForegroundColor Red
    $preflightFailures | ForEach-Object {
        Write-Host "    $_" -ForegroundColor Red
    }
    exit 1
}

Write-Host "[+] PowerShell parser and automatic-variable preflight passed for $($scriptFiles.Count) package scripts." -ForegroundColor Green

if ($SyntaxOnly) {
    exit 0
}

$fixture = Join-Path $scriptDir "test-gate1-fixtures.ps1"
$currentPowerShell = (Get-Process -Id $PID -ErrorAction Stop).Path

if ([string]::IsNullOrWhiteSpace($currentPowerShell)) {
    throw "Cannot resolve the current PowerShell executable"
}

$previousPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = "Continue"
    $output = & $currentPowerShell `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $fixture 2>&1
    $exitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $previousPreference
}

$output | ForEach-Object {
    Write-Host ([string]$_)
}

if ($exitCode -ne 0) {
    Write-Host "[!] Fixture gate failed with exit code $exitCode" -ForegroundColor Red
    exit 1
}

Write-Host "[+] Quark automation script gate passed." -ForegroundColor Green
exit 0
