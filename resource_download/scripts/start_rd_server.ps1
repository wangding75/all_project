$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $PSScriptRoot
$serverExe = Join-Path $packageRoot 'RDServer.exe'
if (-not (Test-Path -LiteralPath $serverExe -PathType Leaf)) {
    throw "RDServer.exe is missing from the release package: $serverExe"
}
if (-not $env:MUMU_INSTANCE_NAME) { $env:MUMU_INSTANCE_NAME = 'RD' + [char]0x6D4B + [char]0x8BD5 }
# RDServer performs fail-closed MuMuManager discovery during runtime bootstrap.
# Do not inject a historical ADB port here.
Start-Process -FilePath $serverExe -WorkingDirectory $packageRoot
