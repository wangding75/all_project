$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $PSScriptRoot
$agent = Join-Path $packageRoot 'runtime\sys_hlpd'
if (-not $env:MUMU_INSTANCE_NAME) { $env:MUMU_INSTANCE_NAME = 'RD' + [char]0x6D4B + [char]0x8BD5 }
$manager = if ($env:MUMU_MANAGER_PATH) { $env:MUMU_MANAGER_PATH } else { Join-Path ${env:ProgramFiles} 'Netease\MuMu Player 12\shell\MuMuManager.exe' }
if (-not (Test-Path -LiteralPath $manager -PathType Leaf)) { throw "MuMuManager.exe not found: $manager" }
$info = (& $manager info --vmindex all | ConvertFrom-Json)
$matches = @($info.PSObject.Properties.Value | Where-Object { $_.name -eq $env:MUMU_INSTANCE_NAME })
if ($matches.Count -ne 1) { throw "Expected one MuMu instance named '$env:MUMU_INSTANCE_NAME', found $($matches.Count)." }
$adbDevice = "$($matches[0].adb_host_ip):$($matches[0].adb_port)"
if ($matches[0].player_state -ne 'start_finished' -or -not $matches[0].is_android_started) { throw "MuMu instance is not ready: $($matches[0].player_state)" }
if ($env:ADB_DEVICE -and $env:ADB_DEVICE -ne $adbDevice) { throw "ADB_DEVICE '$env:ADB_DEVICE' does not match $env:MUMU_INSTANCE_NAME endpoint '$adbDevice'." }
if (-not (Test-Path -LiteralPath $agent -PathType Leaf)) { throw "Package Frida agent missing: $agent" }
& adb -s $adbDevice push $agent /data/local/tmp/sys_hlpd | Out-Null
& adb -s $adbDevice shell chmod 755 /data/local/tmp/sys_hlpd
& adb -s $adbDevice shell "pkill -f /data/local/tmp/sys_hlpd || true"
& adb -s $adbDevice shell "nohup /data/local/tmp/sys_hlpd -D > /data/local/tmp/sys_hlpd.log 2>&1 &"
Write-Output "FRIDA_AGENT_TARGET=$adbDevice"
Write-Output 'FRIDA_AGENT=PASS'
