$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path -Parent $PSScriptRoot
$serverExe = Join-Path $packageRoot 'RDServer.exe'
if (-not (Test-Path -LiteralPath $serverExe -PathType Leaf)) {
    throw "RDServer.exe is missing from the release package: $serverExe"
}
if ($env:ADB_DEVICE -and $env:ADB_DEVICE -eq '127.0.0.1:16384') {
    throw 'SX target 127.0.0.1:16384 is not permitted for the RD release gate.'
}
if (-not $env:ADB_DEVICE) { $env:ADB_DEVICE = '127.0.0.1:7555' }
Start-Process -FilePath $serverExe -WorkingDirectory $packageRoot
