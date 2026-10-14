# E0 自动化冒烟与 E2E 聚合脚本 (PowerShell)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$env:PYTHONPATH = Join-Path $repoRoot "server"
Push-Location $repoRoot
try {

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 1: Running smoke_health.py" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
python "$scriptDir\smoke_health.py"
if ($LASTEXITCODE -ne 0) {
    Write-Error "smoke_health.py failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Step 2: Running deterministic quality gate" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
python "$scriptDir\quality_gate.py"
if ($LASTEXITCODE -ne 0) {
    Write-Error "quality_gate.py failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "CI smoke and deterministic quality checks passed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
} finally {
    Pop-Location
}
