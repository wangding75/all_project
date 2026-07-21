# E0 自动化冒烟与 E2E 聚合脚本 (PowerShell)
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "server"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 1: Running smoke_health.py" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
python "$scriptDir\smoke_health.py"
if ($LASTEXITCODE -ne 0) {
    Write-Error "smoke_health.py failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Step 2: Running e2e_fanqie.py" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
python "$scriptDir\e2e_fanqie.py"
if ($LASTEXITCODE -ne 0) {
    Write-Error "e2e_fanqie.py failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Step 3: Running e2e_hongguo.py" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
python "$scriptDir\e2e_hongguo.py"
if ($LASTEXITCODE -ne 0) {
    Write-Error "e2e_hongguo.py failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "All CI smoke and E2E checks passed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
