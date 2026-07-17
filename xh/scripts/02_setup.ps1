# 02_setup.ps1 - Download BlackDex + install APKs
$WORKSPACE = "d:\github\xh"
$TOOLS     = "$WORKSPACE\tools"
$APK       = "$WORKSPACE\xh.apk"
$PKG       = "com.xin.h6"
$URL64     = "https://github.com/CodingGay/BlackDex/releases/download/v3.2/BlackDex64_v3.2.0.apk"
$URL32     = "https://github.com/CodingGay/BlackDex/releases/download/v3.2/BlackDex32_v3.2.0.apk"

Write-Host "===== Setup: Install BlackDex + xh.apk =====" -ForegroundColor Cyan

# Detect ABI
$abi = (adb shell getprop ro.product.cpu.abi 2>&1).Trim()
$use64 = ($abi -match "arm64|x86_64")
$bdApk = if ($use64) { "$TOOLS\BlackDex64.apk" } else { "$TOOLS\BlackDex32.apk" }
$bdUrl = if ($use64) { $URL64 } else { $URL32 }
$bdPkg = if ($use64) { "top.niunaijun.blackdex64" } else { "top.niunaijun.blackdex32" }
$bdName = if ($use64) { "BlackDex64" } else { "BlackDex32" }

Write-Host ""
Write-Host "[1] Device ABI: $abi -> using $bdName" -ForegroundColor Yellow

# Download if needed
Write-Host ""
Write-Host "[2] BlackDex APK:" -ForegroundColor Yellow
if (-not (Test-Path $bdApk)) {
    Write-Host "    Downloading $bdName from GitHub..." -ForegroundColor Yellow
    try {
        (New-Object System.Net.WebClient).DownloadFile($bdUrl, $bdApk)
        Write-Host "    OK: downloaded to $bdApk" -ForegroundColor Green
    } catch {
        Write-Host "    FAIL: $_" -ForegroundColor Red
        Write-Host "    Manual: $bdUrl" -ForegroundColor Yellow
        exit 1
    }
} else {
    $sz = [math]::Round((Get-Item $bdApk).Length/1MB,1)
    Write-Host "    Already exists: $bdApk ($sz MB)" -ForegroundColor Green
}

# Install BlackDex
Write-Host ""
Write-Host "[3] Install ${bdName}:" -ForegroundColor Yellow
$inst = adb shell pm list packages $bdPkg 2>&1
if ($inst -match $bdPkg) {
    Write-Host "    Already installed, skip" -ForegroundColor Cyan
} else {
    $r = adb install -r $bdApk 2>&1
    if ($r -match "Success") { Write-Host "    OK: installed" -ForegroundColor Green }
    else { Write-Host "    FAIL: $r" -ForegroundColor Red; exit 1 }
}

# Install xh.apk
Write-Host ""
Write-Host "[4] Install xh.apk (com.xin.h6):" -ForegroundColor Yellow
$inst2 = adb shell pm list packages $PKG 2>&1
if ($inst2 -match $PKG) {
    Write-Host "    Already installed, skip" -ForegroundColor Cyan
} else {
    Write-Host "    Installing (~18MB)..." -ForegroundColor Yellow
    $r2 = adb install -r $APK 2>&1
    if ($r2 -match "Success") { Write-Host "    OK: installed" -ForegroundColor Green }
    else { Write-Host "    FAIL: $r2" -ForegroundColor Red; exit 1 }
}

# Push APK to sdcard (fallback for uninstalled unpack)
Write-Host ""
Write-Host "[5] Push xh.apk to /sdcard/:" -ForegroundColor Yellow
$pr = adb push $APK /sdcard/xh.apk 2>&1
Write-Host "    $pr" -ForegroundColor Gray

# Create output dirs
New-Item -ItemType Directory -Force -Path "$WORKSPACE\blackdex_out" | Out-Null
New-Item -ItemType Directory -Force -Path "$WORKSPACE\unpack_out"   | Out-Null
Write-Host ""
Write-Host "===== Setup DONE =====" -ForegroundColor Green
