# Push and start sys_hlpd on MuMu (run after emulator is up + root)
param(
    # 新版 MuMu 6.x 默认路径；旧版 Player 12 可用 -Adb 覆盖
    [string]$Adb = "D:\install\Netease\MuMu\nx_main\adb.exe",
    [string]$Device = "127.0.0.1:16384"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path (Join-Path $Root "server"))) {
    $Root = Split-Path -Parent $PSScriptRoot
}
$ServerBin = Join-Path $PSScriptRoot "sys_hlpd"

if (-not (Test-Path $Adb)) {
    Write-Error "adb not found: $Adb  (install MuMu or pass -Adb path)"
}
if (-not (Test-Path $ServerBin)) {
    Write-Error "missing $ServerBin"
}

Write-Host "connect $Device ..."
& $Adb connect $Device | Out-Null

Write-Host "adb root ..."
& $Adb -s $Device root 2>$null
Start-Sleep -Seconds 1
& $Adb connect $Device | Out-Null

Write-Host "push sys_hlpd ..."
& $Adb -s $Device push $ServerBin /data/local/tmp/sys_hlpd
& $Adb -s $Device shell "chmod 755 /data/local/tmp/sys_hlpd"

Write-Host "start sys_hlpd ..."
& $Adb -s $Device shell "pkill -9 sys_hlpd" 2>$null
& $Adb -s $Device shell "/data/local/tmp/sys_hlpd -D &"
Start-Sleep -Seconds 2
& $Adb -s $Device forward tcp:27042 tcp:27042

Write-Host "host frida version:"
$py = Join-Path $Root "server\.venv\Scripts\python.exe"
if (Test-Path $py) {
    & $py -c "import frida; print(frida.__version__)"
}
Write-Host "sys_hlpd processes:"
& $Adb -s $Device shell "ps -A | grep sys_hlpd"
Write-Host "Done. Next: install/open com.dragon.read then extract config.json"
