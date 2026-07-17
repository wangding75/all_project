# 星盒 (com.xin.h6) Frida Hook 自动挂载脚本 (PowerShell 版)
#
# 启动步骤：
# 1. 自动强制停止并冷启动 com.xin.h6，确保绕过 360 壳的闪退检测。
# 2. 等待 3 秒让壳程序完成内存解密和初始化。
# 3. 动态获取 com.xin.h6 主进程的 PID。
# 4. 调用官方 frida.exe 命令行工具进行 attach 注入。
#
# 好处：官方 frida.exe 会自动处理 frida-java-bridge，避免 Python 接口下的 "Java is not defined" 报错！

$FRIDA_PATH = "C:\Users\wangding\AppData\Local\Python\pythoncore-3.14-64\Scripts\frida.exe"
$JS_PATH = "D:\github\xh\tools\activation_bypass.js"

# 1. 首先彻底停止 frida-server 避开星盒的冷启动环境扫描
Write-Host "[*] EVASION: Stopping frida-server to bypass launch detection..." -ForegroundColor Yellow
adb shell "pkill frida-server; pkill frida"
Start-Sleep -Seconds 1

Write-Host "[*] Terminating existing com.xin.h6 process..." -ForegroundColor Yellow
adb shell am force-stop com.xin.h6
Start-Sleep -Seconds 1

# 2. 启动应用
Write-Host "[*] Launching com.xin.h6 (星盒) without debugging environment..." -ForegroundColor Cyan
adb shell monkey -p com.xin.h6 -c android.intent.category.LAUNCHER 1 > $null

# 3. 等待应用完全进入前台
Write-Host "[*] Waiting 3 seconds for app to fully initialize and display UI..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# 4. 动态在设备后台拉起 frida-server，并配置端口转发
Write-Host "[*] EVASION: Starting frida-server dynamically..." -ForegroundColor Green
adb shell "nohup /data/local/tmp/frida-server -l 0.0.0.0:27042 >/dev/null 2>&1 &"
Start-Sleep -Seconds 2
adb forward tcp:27042 tcp:27042

# 获取主进程 PID
Write-Host "[*] Detecting process PID..." -ForegroundColor Cyan
$ps_line = adb shell "ps -A | grep 'xin.h6'" | Out-String
if ($ps_line -match '\s+(\d+)\s+\d+\s+.*com\.xin\.h6\s*$') {
    $target_pid = $Matches[1]
    Write-Host "[*] Found target process com.xin.h6 PID: $target_pid" -ForegroundColor Green
    Write-Host "[*] Injecting hooks via Frida CLI..." -ForegroundColor Green
    Write-Host "[*] Press Ctrl+C in this terminal window to stop hooking." -ForegroundColor Yellow
    
    # 启动 frida.exe CLI 并进行挂载注入，配合 < NUL 避免 REPL 退出
    cmd.exe /c "`"$FRIDA_PATH`" -U -p $target_pid -l `"$JS_PATH`" < NUL"
} else {
    # 兜底：如果直接匹配不成功，尝试粗暴提取第一个数字
    $ps_clean = $ps_line.Trim()
    if ($ps_clean -match '^\S+\s+(\d+)\s+') {
        $target_pid = $Matches[1]
        Write-Host "[*] Found target process com.xin.h6 PID (fallback): $target_pid" -ForegroundColor Green
        cmd.exe /c "`"$FRIDA_PATH`" -U -p $target_pid -l `"$JS_PATH`" < NUL"
    } else {
        Write-Error "[!] com.xin.h6 is not running. Could not detect PID."
    }
}
