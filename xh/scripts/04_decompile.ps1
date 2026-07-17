# 04_decompile.ps1 - Decompile unpacked DEX (or fall back to existing jadx_out)
$WORKSPACE = "d:\github\xh"
$DEX_DIR   = "$WORKSPACE\blackdex_out"
$JADX      = "$WORKSPACE\tools\jadx\bin\jadx.bat"
$OUT       = "$WORKSPACE\unpack_out"
$APK       = "$WORKSPACE\xh.apk"

Write-Host "===== Decompile with jadx =====" -ForegroundColor Cyan

# Find DEX files from BlackDex output
$dexFiles = Get-ChildItem $DEX_DIR -Recurse -Filter "*.dex" -ErrorAction SilentlyContinue

if ($dexFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "[Mode] Unpacked DEX detected -> decompile DEX" -ForegroundColor Green
    $dexFiles | ForEach-Object {
        $sz = [math]::Round($_.Length/1MB, 2)
        Write-Host "    Found: $($_.Name) ($sz MB)" -ForegroundColor Cyan
    }
    # Filter out tiny/dummy DEX files (e.g., < 10KB) which are likely empty or corrupt placeholders
    $validDexFiles = $dexFiles | Where-Object { $_.Length -gt 10KB }
    if ($validDexFiles.Count -eq 0) {
        Write-Host "    WARN: No DEX files larger than 10KB found, attempting to use all files." -ForegroundColor Yellow
        $validDexFiles = $dexFiles
    }

    Write-Host "    Selected $($validDexFiles.Count) valid DEX files for decompilation." -ForegroundColor Magenta

    if (Test-Path $OUT) { Remove-Item $OUT -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $OUT | Out-Null

    Write-Host ""
    Write-Host "[jadx] Decompiling all valid DEX files..." -ForegroundColor Yellow
    $t = Get-Date
    
    # Pass all full paths as an array to JADX and disable checksum verification
    $dexPaths = $validDexFiles | ForEach-Object { $_.FullName }
    & $JADX "-Pdex-input.verify-checksum=no" $dexPaths -d $OUT --threads-count 4 --show-bad-code
    
    $elapsed = [math]::Round(((Get-Date)-$t).TotalSeconds,1)
    Write-Host "    Done in ${elapsed}s" -ForegroundColor Green

} else {
    Write-Host ""
    Write-Host "[Mode] No unpacked DEX -> decompile xh.apk directly (shell visible only)" -ForegroundColor Yellow
    Write-Host "       (To see real code, connect device and run 03_unpack.ps1 first)" -ForegroundColor DarkGray

    $existing = "$WORKSPACE\jadx_out\sources"
    if (Test-Path $existing) {
        Write-Host "    Reusing existing jadx_out from previous run." -ForegroundColor Cyan
        $OUT = "$WORKSPACE\jadx_out"
    } else {
        Write-Host "    Running jadx on xh.apk..." -ForegroundColor Yellow
        if (Test-Path $OUT) { Remove-Item $OUT -Recurse -Force }
        New-Item -ItemType Directory -Force -Path $OUT | Out-Null
        $t = Get-Date
        & $JADX $APK -d $OUT --threads-count 4 --show-bad-code
        $elapsed = [math]::Round(((Get-Date)-$t).TotalSeconds,1)
        Write-Host "    Done in ${elapsed}s" -ForegroundColor Green
    }
}

# Stats
$srcDir = "$OUT\sources"
Write-Host ""
Write-Host "===== Results =====" -ForegroundColor Yellow
$javaFiles = Get-ChildItem $srcDir -Recurse -Filter "*.java" -ErrorAction SilentlyContinue
$pkgs      = Get-ChildItem $srcDir -Directory -ErrorAction SilentlyContinue
Write-Host "    Java files : $($javaFiles.Count)" -ForegroundColor Green
Write-Host "    Top pkgs   : $($pkgs.Count)" -ForegroundColor Green
$pkgs | ForEach-Object {
    $c = (Get-ChildItem $_.FullName -Recurse -Filter "*.java" -ErrorAction SilentlyContinue).Count
    Write-Host "      $($_.Name)/ -> $c classes" -ForegroundColor Cyan
}

# Key patterns
Write-Host ""
Write-Host "===== Key Patterns =====" -ForegroundColor Yellow
$patterns = @{
    "Application class"  = "extends Application"
    "Activity class"     = "extends.*Activity"
    "OkHttp/Retrofit"    = "OkHttpClient|Retrofit"
    "Server URL (http)"  = 'https?://[a-zA-Z0-9._/]'
    "AES encryption"     = "AES"
    "MockLocation"       = "setTestProviderLocation|addTestProvider"
    "TelephonyManager"   = "TelephonyManager"
    "SharedPreferences"  = "getSharedPreferences"
    "Native methods"     = "public.*native "
}
foreach ($k in $patterns.Keys) {
    $cnt = (Get-ChildItem $srcDir -Recurse -Filter "*.java" -ErrorAction SilentlyContinue |
        Select-String $patterns[$k] -ErrorAction SilentlyContinue | Select-Object Path -Unique).Count
    $icon = if ($cnt -gt 0) { "[HIT]" } else { "[---]" }
    $col  = if ($cnt -gt 0) { "Green" } else { "DarkGray" }
    Write-Host "    $icon $k : $cnt files" -ForegroundColor $col
}

Write-Host ""
Write-Host "===== Decompile DONE =====" -ForegroundColor Green
Write-Host "    Source: $OUT\sources\" -ForegroundColor White
