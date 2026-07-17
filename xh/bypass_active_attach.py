import frida
import sys
import time
import subprocess
import re

# 打印日志回调
def on_message(message, data):
    if message['type'] == 'send':
        print(f"[*] {message['payload']}")
    else:
        print(f"[Frida System] {message}")

def get_target_pid():
    try:
        # 使用 adb shell ps 获取 PID
        result = subprocess.run(["adb", "shell", "ps", "-A"], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if "com.xin.h6" in line and not line.endswith("com.xin.h6:"):
                # 解析 PID (通常是第二列)
                parts = re.split(r'\s+', line.strip())
                if len(parts) > 1:
                    pid = int(parts[1])
                    return pid
    except Exception as e:
        print(f"[!] Error getting PID via ADB: {e}")
    return None

def start_app():
    print("[*] Launching com.xin.h6 (星盒) via Monkey...")
    try:
        subprocess.run([
            "adb", "shell", "monkey", 
            "-p", "com.xin.h6", 
            "-c", "android.intent.category.LAUNCHER", "1"
        ], capture_output=True, check=True)
    except Exception as e:
        print(f"[!] Failed to launch app: {e}")

def main():
    # 1. EVASION: 彻底停止 frida-server 避开星盒冷启动扫描
    print("[*] EVASION: Stopping frida-server to bypass launch detection...")
    try:
        subprocess.run(["adb", "shell", "pkill frida-server; pkill frida"], check=True)
    except:
        pass
        
    time.sleep(1)

    print("[*] Terminating existing com.xin.h6 process...")
    try:
        subprocess.run(["adb", "shell", "am", "force-stop", "com.xin.h6"], check=True)
    except:
        pass
        
    time.sleep(1)

    # 2. 启动 App
    start_app()
    
    # 3. 给 360 壳 3 秒的初始化与解壳时间
    wait_time = 3.0
    print(f"[*] Waiting {wait_time}s for app to fully initialize and display UI...")
    time.sleep(wait_time)

    # 4. EVASION: 动态在设备后台拉起 frida-server，并配置端口转发
    print("[*] EVASION: Starting frida-server dynamically...")
    try:
        subprocess.run(["adb", "shell", "nohup /data/local/tmp/frida-server -l 0.0.0.0:27042 >/dev/null 2>&1 &"], check=True)
    except Exception as e:
        print(f"[!] Failed to start frida-server: {e}")
        
    time.sleep(2)
    
    try:
        subprocess.run(["adb", "forward", "tcp:27042", "tcp:27042"], check=True)
    except:
        pass

    # 5. 获取运行 PID
    pid = get_target_pid()
    if not pid:
        print("[!] com.xin.h6 is not running. Failed to find PID.")
        return

    print(f"[*] Found target process PID: {pid}")

    # 4. 连接设备并 Attach
    print("[*] Connecting to remote device 127.0.0.1:27042...")
    try:
        device = frida.get_device_manager().add_remote_device("127.0.0.1:27042")
        print(f"[*] Connected to: {device.name}")
        session = device.attach(pid)
    except Exception as e:
        print(f"[!] Frida connection or attach failed: {e}")
        print("[*] Tip: Make sure adb forward tcp:27042 tcp:27042 was run and frida-server is running on your simulator")
        return

    # 5. 读取我们已经写好的 JavaScript Hook 脚本
    script_path = "D:\\github\\xh\\tools\\activation_bypass.js"
    print(f"[*] Loading Hook script: {script_path}")
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            js_code = f.read()
    except Exception as e:
        print(f"[!] Failed to read hook script file: {e}")
        return

    # 6. 载入并运行
    try:
        script = session.create_script(js_code)
        script.on('message', on_message)
        script.load()
        print("[*] Hooks injected successfully!")
        print("[*] Live logs from ActivationBypass will show below. Press Ctrl+C to stop.")
        
        # 替代 stdin.read() 以免在后台任务中挂起
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[*] Detaching from process and exiting...")
    except Exception as e:
        print(f"[!] Runtime error: {e}")
    finally:
        try:
            session.detach()
        except:
            pass

if __name__ == '__main__':
    main()
