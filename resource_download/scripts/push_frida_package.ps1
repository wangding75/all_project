$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $PSScriptRoot
$agent = Join-Path $packageRoot 'runtime\sys_hlpd'
$adbDevice = if ($env:ADB_DEVICE) { $env:ADB_DEVICE } else { '127.0.0.1:7555' }
if ($adbDevice -eq '127.0.0.1:16384') { throw 'SX target 127.0.0.1:16384 is forbidden.' }
if (-not (Test-Path -LiteralPath $agent -PathType Leaf)) { throw "Package Frida agent missing: $agent" }
& adb -s $adbDevice push $agent /data/local/tmp/sys_hlpd | Out-Null
& adb -s $adbDevice shell chmod 755 /data/local/tmp/sys_hlpd
& adb -s $adbDevice shell "pkill -f /data/local/tmp/sys_hlpd || true"
& adb -s $adbDevice shell "nohup /data/local/tmp/sys_hlpd -D > /data/local/tmp/sys_hlpd.log 2>&1 &"
Write-Output "FRIDA_AGENT_TARGET=$adbDevice"
Write-Output 'FRIDA_AGENT=PASS'
