# 06_organize.ps1 - Extract and organize core business source code
$WORKSPACE = "d:\github\xh"
$SRC       = "$WORKSPACE\unpack_out\sources"
$CLEAN_DIR = "$WORKSPACE\src_clean"

Write-Host "===== Organizing Source Code =====" -ForegroundColor Cyan

if (Test-Path $CLEAN_DIR) {
    Write-Host "    Removing old clean source directory..." -ForegroundColor Gray
    Remove-Item $CLEAN_DIR -Recurse -Force | Out-Null
}

New-Item -ItemType Directory -Force -Path "$CLEAN_DIR\sources\com" | Out-Null

# The list of packages we want to keep (core business + custom UI/helpers)
$packagesToKeep = @("loc", "tianyu", "hjq", "youth")

Write-Host "    Extracting custom business logic packages..." -ForegroundColor Yellow
foreach ($pkg in $packagesToKeep) {
    $srcPath = "$SRC\com\$pkg"
    $destPath = "$CLEAN_DIR\sources\com\$pkg"
    if (Test-Path $srcPath) {
        Write-Host "      Copying com.$pkg..." -ForegroundColor Cyan
        Copy-Item -Path $srcPath -Destination $destPath -Recurse -Force
    }
}

# Display results
Write-Host ""
Write-Host "===== Clean Source Code organized =====" -ForegroundColor Green
Write-Host "    New Directory : $CLEAN_DIR" -ForegroundColor White
Write-Host "    Core Business : $CLEAN_DIR\sources\com\loc\" -ForegroundColor Yellow
