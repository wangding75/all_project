$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$server = Join-Path $root "server"
$targets = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "python|uvicorn" -and
    $_.CommandLine -match "uvicorn app\.main:app" -and
    $_.CommandLine -match "--port 8000"
}
foreach ($target in $targets) {
    Stop-Process -Id ([int]$target.ProcessId) -Force
}
Start-Sleep -Seconds 1
Start-Process -FilePath "python" `
    -ArgumentList @("-u", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $server `
    -WindowStyle Hidden
