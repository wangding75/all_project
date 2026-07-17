# run_all.ps1 - xh.apk unpack demo (BlackDex + jadx)
$WORKSPACE = "d:\github\xh"
$SCRIPTS   = "$WORKSPACE\scripts"

Write-Host ""
Write-Host "  =====================================" -ForegroundColor Magenta
Write-Host "   xh.apk BlackDex Unpack Demo" -ForegroundColor Magenta
Write-Host "   Target: com.xin.h6 (360 Jiagu)" -ForegroundColor Magenta
Write-Host "  =====================================" -ForegroundColor Magenta
Write-Host ""

$devs = (adb devices 2>&1) | Where-Object { $_ -match "`t(device|emulator)" }
$hasDevice = ($devs.Count -gt 0)

if (-not $hasDevice) {
    Write-Host "  [WARN] No device connected." -ForegroundColor Yellow
    Write-Host "  Steps 02+03 (BlackDex install/unpack) will be skipped." -ForegroundColor Yellow
    Write-Host "  Steps 04+05 (jadx decompile+analyze) will run on existing output." -ForegroundColor Yellow
    Write-Host ""
}

$steps = @(
    @{ s = "01_check_env.ps1";  n = "Check Env";    dev = $false; fatal = $false },
    @{ s = "02_setup.ps1";      n = "Install Tools"; dev = $true;  fatal = $true  },
    @{ s = "03_unpack.ps1";     n = "Unpack DEX";    dev = $true;  fatal = $true  },
    @{ s = "04_decompile.ps1";  n = "Decompile";     dev = $false; fatal = $true  },
    @{ s = "05_analyze.ps1";    n = "Analyze";       dev = $false; fatal = $false }
)

$totalStart = Get-Date

foreach ($step in $steps) {
    if ($step.dev -and -not $hasDevice) {
        Write-Host "--- [SKIP] $($step.n) (needs device) ---" -ForegroundColor DarkGray
        continue
    }
    Write-Host ""
    Write-Host ("--- [" + $step.n + "] " + ("-" * 38)) -ForegroundColor Cyan
    $t = Get-Date
    & "$SCRIPTS\$($step.s)"
    $ec = $LASTEXITCODE
    $elapsed = [math]::Round(((Get-Date)-$t).TotalSeconds, 1)
    if ($ec -gt 0 -and $step.fatal) {
        Write-Host "FAILED: $($step.n)" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK: $($step.n) ($($elapsed)s)" -ForegroundColor Green
}

$total = [math]::Round(((Get-Date)-$totalStart).TotalSeconds, 0)
Write-Host ""
Write-Host "  =====================================" -ForegroundColor Green
Write-Host "   DONE! Total: ${total}s" -ForegroundColor Green
if ($hasDevice) { Write-Host "   DEX  : $WORKSPACE\blackdex_out\" -ForegroundColor White }
Write-Host "   Java : $WORKSPACE\unpack_out\sources\" -ForegroundColor White
Write-Host "   Open : code $WORKSPACE\unpack_out" -ForegroundColor Yellow
Write-Host "  =====================================" -ForegroundColor Green
