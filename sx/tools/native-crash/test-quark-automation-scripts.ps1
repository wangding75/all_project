<#
.SYNOPSIS
    Parse every PowerShell script in this package and optionally run fixtures.
#>

[CmdletBinding()]
param(
    [switch]$SyntaxOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$scriptFiles = @(Get-ChildItem -LiteralPath $scriptDir -Filter "*.ps1" -File | Sort-Object Name)
if ($scriptFiles.Count -eq 0) {
    throw "No PowerShell scripts found in $scriptDir"
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
        $preflightFailures.Add("$($file.Name):$($parseError.Extent.StartLineNumber):$($parseError.Extent.StartColumnNumber): $($parseError.Message)")
    }

    $parameterAsts = @($ast.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.ParameterAst]
    }, $true))
    foreach ($parameterAst in $parameterAsts) {
        $name = $parameterAst.Name.VariablePath.UserPath
        if ($readOnlyAutomaticVariables -contains $name) {
            $preflightFailures.Add("$($file.Name):$($parameterAst.Extent.StartLineNumber): read-only automatic variable '$name' is used as a parameter")
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
                $preflightFailures.Add("$($file.Name):$($assignmentAst.Extent.StartLineNumber): read-only automatic variable '$name' is assigned")
            }
        }
    }
}

if ($preflightFailures.Count -gt 0) {
    Write-Host "[!] PowerShell package preflight failed:" -ForegroundColor Red
    $preflightFailures | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    exit 1
}

Write-Host "[+] PowerShell parser and automatic-variable preflight passed for $($scriptFiles.Count) scripts." -ForegroundColor Green

if ($SyntaxOnly) {
    exit 0
}

$fixture = Join-Path $scriptDir "test-gate1-fixtures.ps1"
if (-not (Test-Path -LiteralPath $fixture -PathType Leaf)) {
    throw "Fixture script missing: $fixture"
}

$currentPowerShell = (Get-Process -Id $PID -ErrorAction Stop).Path
$previousPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = "Continue"
    $output = & $currentPowerShell -NoProfile -ExecutionPolicy Bypass -File $fixture 2>&1
    $exitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $previousPreference
}
$output | ForEach-Object { Write-Host ([string]$_) }
if ($exitCode -ne 0) {
    Write-Host "[!] Fixture gate failed with exit code $exitCode" -ForegroundColor Red
    exit 1
}

Write-Host "[+] Quark automation script gate passed." -ForegroundColor Green
exit 0
