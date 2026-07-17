# 03_unpack.ps1 - BlackDex unpack via ADB intent
$WORKSPACE  = "d:\github\xh"
$PKG        = "com.xin.h6"
$OUT        = "$WORKSPACE\blackdex_out"
$DEV_OUT    = "/sdcard/BlackDex/$PKG"

Write-Host "===== BlackDex Unpack: $PKG =====" -ForegroundColor Cyan

$abi    = (adb shell getprop ro.product.cpu.abi 2>&1).Trim()
$use64  = ($abi -match "arm64|x86_64")
$bdPkg  = if ($use64) { "top.niunaijun.blackdex64" } else { "top.niunaijun.blackdex32" }
$bdAct  = "$bdPkg/.MainActivity"
$bdName = if ($use64) { "BlackDex64" } else { "BlackDex32" }

Write-Host ""
Write-Host "[1] Using: $bdName (ABI=$abi)" -ForegroundColor Yellow

# Clean old dump
Write-Host ""
Write-Host "[2] Clean previous dump on device..." -ForegroundColor Yellow
adb shell "rm -rf $DEV_OUT" 2>&1 | Out-Null
Write-Host "    Cleaned: $DEV_OUT" -ForegroundColor Gray

# Stop target app
Write-Host ""
Write-Host "[3] Force-stop target app..." -ForegroundColor Yellow
adb shell am force-stop $PKG 2>&1 | Out-Null
Start-Sleep -Milliseconds 800
Write-Host "    Stopped: $PKG" -ForegroundColor Gray

# Launch BlackDex with intent
Write-Host ""
Write-Host "[4] Trigger unpack via ADB intent..." -ForegroundColor Yellow
$cmd = "am start -n $bdAct -a android.intent.action.VIEW --es packageName $PKG"
Write-Host "    $cmd" -ForegroundColor DarkGray
adb shell $cmd 2>&1 | Out-Null

# Wait for DEX output
Write-Host "    Waiting for DEX output..." -ForegroundColor Yellow
$max = 90; $step = 3; $t = 0; $done = $false
while ($t -lt $max) {
    Start-Sleep -Seconds $step
    $t += $step
    $ls = adb shell "ls $DEV_OUT 2>/dev/null" 2>&1
    if ($ls -match "\.dex") {
        $done = $true
        Write-Host "    DEX found after ${t}s!" -ForegroundColor Green
        break
    }
    Write-Host "    ... ${t}s / ${max}s" -ForegroundColor DarkGray
}

if (-not $done) {
    Write-Host ""
    Write-Host "  Auto-detect timeout. Manual steps:" -ForegroundColor Yellow
    Write-Host "  1. Open $bdName on device" -ForegroundColor Yellow
    Write-Host "  2. Tap 'com.xin.h6' in the list" -ForegroundColor Yellow
    Write-Host "  3. Wait for success toast" -ForegroundColor Yellow
    Write-Host "  Press Enter when done..." -ForegroundColor Cyan
    Read-Host | Out-Null
    $ls2 = adb shell "ls $DEV_OUT 2>/dev/null" 2>&1
    if ($ls2 -match "\.dex") { $done = $true }
    else { Write-Host "  FAIL: no DEX found" -ForegroundColor Red; exit 1 }
}

# List DEX on device
Write-Host ""
Write-Host "[5] DEX files on device:" -ForegroundColor Yellow
adb shell "ls -lh $DEV_OUT" 2>&1 | Write-Host -ForegroundColor Cyan

# Pull to local
Write-Host ""
Write-Host "[6] Pull DEX to local..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $OUT | Out-Null
$pr = adb pull $DEV_OUT $OUT 2>&1
Write-Host $pr -ForegroundColor Gray

# Show local DEX
Write-Host ""
Write-Host "[7] Local DEX files:" -ForegroundColor Yellow
Get-ChildItem $OUT -Recurse -Filter "*.dex" | ForEach-Object {
    $sz = [math]::Round($_.Length/1MB, 2)
    Write-Host "    $($_.Name)  [$sz MB]" -ForegroundColor Green
}

Write-Host ""
Write-Host "===== Unpack DONE =====" -ForegroundColor Green
Write-Host "    Output: $OUT" -ForegroundColor White
