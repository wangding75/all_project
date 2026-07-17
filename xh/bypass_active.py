import frida
import sys

def on_message(message, data):
    if message['type'] == 'send':
        print(f"[*] {message['payload']}")
    else:
        print(message)

def main():
    print("[*] Connecting to MuMu Player via Remote Port 29999...")
    try:
        device = frida.get_device_manager().add_remote_device("127.0.0.1:29999")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        return

    print(f"[*] Connected to: {device.name}")
    
    try:
        print("[*] Terminating existing com.xin.h6 process...")
        device.kill("com.xin.h6")
    except:
        pass

    print("[*] Spawning com.xin.h6 (星盒)...")
    try:
        pid = device.spawn(["com.xin.h6"])
        session = device.attach(pid)
    except Exception as e:
        print(f"[!] Spawn failed: {e}")
        return

    # Updated Java execution hook payload targeting both SplashActivity and ActiveCardActivity
    js_code = """
    Java.perform(function () {
        send("Hooking com.loc.va.utils.MyUtil to bypass license activation...");
        var MyUtil = Java.use("com.loc.va.utils.MyUtil");
        
        // Base64 encoded premium license config
        var FAKE_CORE_CONFIG = "eyJ2aXAiOiIxIiwiYWN0aXZlIjoiMSIsInN0YXR1cyI6IjEiLCJhdXRoIjoiMSIsImV4cGlyZSI6IjIwOTktMTItMzEgMjM6NTk6NTkiLCJleHBpcmVfdGltZSI6IjQwOTk4OTg4MDAwMDAiLCJleHBpcmVUaW1lIjoiNDA5OTg5ODgwMDAwMCIsInRpbWUiOiI0MDk5ODk4ODAwMDAwIiwiZGF5IjoiOTk5OTkiLCJjb2RlIjoiYWN0aXZhdGVkIn0=";
        
        MyUtil.getConfig.implementation = function (context, key) {
            send("getConfig called for key: " + key);
            if (key === "CORE") {
                send("Injected fake CORE license config!");
                return FAKE_CORE_CONFIG;
            }
            return this.getConfig(context, key);
        };
        
        MyUtil.getConfig2.implementation = function (context, key) {
            var res = this.getConfig2(context, key);
            send("getConfig2 subkey check: [" + key + "] -> Returned: [" + res + "]");
            return res;
        };

        // Hook SplashActivity to redirect directly to HomeActivity instead of letting it decide to go to ActiveCardActivity
        try {
            var SplashActivity = Java.use("com.loc.va.ui.activity.SplashActivity");
            SplashActivity.onResume.implementation = function () {
                send("SplashActivity.onResume intercepted! Redirecting directly to HomeActivity...");
                var context = this;
                var Intent = Java.use("android.content.Intent");
                var HomeActivityClass = Java.use("com.loc.va.ui.activity.HomeActivity").class;
                var targetIntent = Intent.$new(context, HomeActivityClass);
                context.startActivity(targetIntent);
                context.finish();
            };
        } catch(e) {
            send("SplashActivity Hook error: " + e);
        }
        
        // Target Page Self-Redirection fallback in case Splash is bypassed or skipped
        try {
            var ActiveCardActivity = Java.use("com.loc.va.ui.activity.ActiveCardActivity");
            ActiveCardActivity.onCreate.implementation = function (bundle) {
                send("ActiveCardActivity.onCreate intercepted! Performing direct redirection to HomeActivity...");
                var context = this;
                var Intent = Java.use("android.content.Intent");
                var HomeActivityClass = Java.use("com.loc.va.ui.activity.HomeActivity").class;
                var targetIntent = Intent.$new(context, HomeActivityClass);
                context.startActivity(targetIntent);
                context.finish();
                this.onCreate(bundle);
            };
        } catch(e) {
            send("ActiveCardActivity Hook error: " + e);
        }
    });
    """

    script = session.create_script(js_code)
    script.on('message', on_message)
    script.load()
    
    device.resume(pid)
    print("[*] Application resumed. Keep this script running to maintain the bypass.")
    print("[*] Press Ctrl+C to terminate.")
    
    sys.stdin.read()

if __name__ == '__main__':
    main()
