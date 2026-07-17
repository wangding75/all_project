# 05_analyze.ps1 - Deep analysis (uses jadx_out if unpack_out missing)
$WORKSPACE = "d:\github\xh"

# Use unpack_out if available, else fall back to jadx_out
if (Test-Path "$WORKSPACE\unpack_out\sources") {
    $SRC = "$WORKSPACE\unpack_out\sources"
} elseif (Test-Path "$WORKSPACE\jadx_out\sources") {
    $SRC = "$WORKSPACE\jadx_out\sources"
    Write-Host "[INFO] Using jadx_out (shell-only, no real business code)" -ForegroundColor Yellow
} else {
    Write-Host "FAIL: no sources found. Run 04_decompile.ps1 first." -ForegroundColor Red
    exit 1
}

$REPORT = (Split-Path $SRC) + "\analysis_report.txt"
Write-Host "===== Source Analysis =====" -ForegroundColor Cyan
Write-Host "    Source: $SRC" -ForegroundColor Gray

# --- Package structure ---
Write-Host ""
Write-Host "[1] Package structure:" -ForegroundColor Yellow
Get-ChildItem $SRC -Directory | ForEach-Object {
    $c = (Get-ChildItem $_.FullName -Recurse -Filter "*.java" -ErrorAction SilentlyContinue).Count
    Write-Host "    $($_.Name)/  ($c classes)" -ForegroundColor Cyan
    Get-ChildItem $_.FullName -Directory | ForEach-Object {
        $c2 = (Get-ChildItem $_.FullName -Recurse -Filter "*.java" -ErrorAction SilentlyContinue).Count
        Write-Host "      $($_.Name)/  ($c2 classes)" -ForegroundColor DarkCyan
    }
}

# --- URL search ---
Write-Host ""
Write-Host "[2] Server URLs (plain text):" -ForegroundColor Yellow
$allJava = Get-ChildItem $SRC -Recurse -Filter "*.java" -ErrorAction SilentlyContinue
$urls = $allJava | Select-String -Pattern 'https?://[a-zA-Z0-9._/:%?=&-]{8,}' -ErrorAction SilentlyContinue |
    ForEach-Object { $_.Matches[0].Value } | Sort-Object -Unique
if ($urls) {
    $urls | Select-Object -First 20 | ForEach-Object { Write-Host "    $_ " -ForegroundColor Yellow }
} else {
    Write-Host "    (none - encrypted or in native .so)" -ForegroundColor DarkGray
}

# --- Key patterns ---
Write-Host ""
Write-Host "[3] Key code patterns:" -ForegroundColor Yellow
$checks = [ordered]@{
    "extends Application"   = "extends Application"
    "extends.*Activity"     = "extends.*Activity"
    "OkHttpClient"          = "OkHttpClient"
    "Retrofit"              = "Retrofit"
    "AES cipher"            = "AES"
    "MockLocation"          = "setTestProviderLocation"
    "TelephonyManager"      = "TelephonyManager"
    "SharedPreferences"     = "getSharedPreferences"
    "native methods"        = "\bnative\b"
    "token/auth"            = "token|Token|Bearer"
}
foreach ($label in $checks.Keys) {
    $cnt = ($allJava | Select-String -Pattern $checks[$label] -ErrorAction SilentlyContinue | Select-Object Path -Unique).Count
    $icon = if ($cnt -gt 0) { "[HIT]" } else { "[---]" }
    $col  = if ($cnt -gt 0) { "Green" } else { "DarkGray" }
    Write-Host ("    $icon {0,-25} : {1} file(s)" -f $label, $cnt) -ForegroundColor $col
}

# --- Observation ---
Write-Host ""
Write-Host "[4] Analysis summary:" -ForegroundColor Yellow
$totalJava  = $allJava.Count
$nativeHits = ($allJava | Select-String "\bnative\b" -ErrorAction SilentlyContinue | Select-Object Path -Unique).Count
Write-Host "    Total Java files : $totalJava" -ForegroundColor White
Write-Host "    Files w/ native  : $nativeHits" -ForegroundColor White

$comXin = Get-ChildItem "$SRC\com\xin" -Recurse -Filter "*.java" -ErrorAction SilentlyContinue
$comLoc = Get-ChildItem "$SRC\com\loc" -Recurse -Filter "*.java" -ErrorAction SilentlyContinue
$realBusinessCount = $comXin.Count + $comLoc.Count

if ($realBusinessCount -le 2) {
    Write-Host ""
    Write-Host "    [!] Core packages (com.xin / com.loc) have only $realBusinessCount Java file(s)" -ForegroundColor Red
    Write-Host "    [!] This confirms 360 Jiagu hides real DEX in libaa.so/libbb.so" -ForegroundColor Red
    Write-Host "    [!] Connect a device and run 03_unpack.ps1 to get real business code" -ForegroundColor Yellow
} else {
    Write-Host "    [OK] Decompilation successful! Found $realBusinessCount core classes (com.xin: $($comXin.Count), com.loc: $($comLoc.Count))." -ForegroundColor Green
}

"Analysis: $SRC | $(Get-Date)" | Out-File $REPORT -Encoding UTF8
Write-Host ""
Write-Host "===== Analysis DONE =====" -ForegroundColor Green
Write-Host "    Report: $REPORT" -ForegroundColor White
