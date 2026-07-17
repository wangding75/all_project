# 01_check_env.ps1 - Environment check (warnings only, no hard exit)
$WORKSPACE = "d:\github\xh"

Write-Host "===== Environment Check =====" -ForegroundColor Cyan

Write-Host ""
Write-Host "[1] ADB:" -ForegroundColor Yellow
$v = adb version 2>&1 | Select-String "Android Debug Bridge"
if ($v) { Write-Host "    OK: $v" -ForegroundColor Green }
else     { Write-Host "    WARN: adb not found" -ForegroundColor Red }

Write-Host ""
Write-Host "[2] Connected devices:" -ForegroundColor Yellow
adb devices
$devs = (adb devices 2>&1) | Where-Object { $_ -match "`t(device|emulator)" }
if ($devs.Count -gt 0) {
    $abi = (adb shell getprop ro.product.cpu.abi 2>&1).Trim()
    $ver = (adb shell getprop ro.build.version.release 2>&1).Trim()
    $mdl = (adb shell getprop ro.product.model 2>&1).Trim()
    Write-Host "    Model  : $mdl" -ForegroundColor Cyan
    Write-Host "    Android: $ver" -ForegroundColor Cyan
    Write-Host "    ABI    : $abi" -ForegroundColor Cyan
    if ($abi -match "arm64|x86_64") { Write-Host "    Use: BlackDex64.apk" -ForegroundColor Magenta }
    else                            { Write-Host "    Use: BlackDex32.apk" -ForegroundColor Magenta }
} else {
    Write-Host "    WARN: no device -> unpack steps will be skipped" -ForegroundColor Yellow
    Write-Host "    Nox:     adb connect 127.0.0.1:62001" -ForegroundColor DarkGray
    Write-Host "    LDPlayer:adb connect 127.0.0.1:5555"  -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "[3] Files:" -ForegroundColor Yellow
@("xh.apk","tools\apktool.jar","tools\jadx\bin\jadx.bat") | ForEach-Object {
    $p = "$WORKSPACE\$_"
    if (Test-Path $p) {
        $sz = [math]::Round((Get-Item $p).Length/1MB,1)
        Write-Host "    OK: $_ ($sz MB)" -ForegroundColor Green
    } else {
        Write-Host "    MISS: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "[4] Java:" -ForegroundColor Yellow
$jv = java -version 2>&1 | Select-Object -First 1
Write-Host "    $jv" -ForegroundColor Green

Write-Host ""
Write-Host "===== Check done =====" -ForegroundColor Cyan
