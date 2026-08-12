$ErrorActionPreference = 'Stop'
$base = if ($env:RD_BASE_URL) { $env:RD_BASE_URL.TrimEnd('/') } else { 'http://127.0.0.1:8000' }
$response = Invoke-WebRequest -UseBasicParsing -Uri "$base/health" -TimeoutSec 10
if ($response.StatusCode -ne 200) { throw "RD health failed: HTTP $($response.StatusCode)" }
Write-Output 'RD_HEALTH=PASS'
