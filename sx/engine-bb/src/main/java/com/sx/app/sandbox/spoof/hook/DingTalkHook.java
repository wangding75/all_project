package com.sx.app.sandbox.spoof.hook;

import android.app.Activity;
import android.os.Handler;
import android.os.Looper;
import android.os.Process;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XC_MethodReplacement;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;

/**
 * DingTalk survival hooks. Complements native anti-suicide (SI_USER SIGSEGV ignore).
 */
public final class DingTalkHook {
    private static final String TAG = "SX-DingTalkHook";
    public static final String PACKAGE = "com.alibaba.android.rimet";
    private static volatile boolean sInstalled;
    private static volatile boolean sPackagesCleaned;
    private static final List<String> BLOCKED_SERVICES = java.util.Arrays.asList(
            "va_", "bb_", "ding_service", "vservermanager", "vservermanager2"
    );

    private DingTalkHook() {
    }

    public static void install(ClassLoader cl, String packageName) {
        if (sInstalled || !PACKAGE.equals(packageName)) {
            return;
        }
        sInstalled = true; // Mark installed immediately so partial failures don't cause infinite retry loops

        // hookPrivacyPreferences(); // Disabled: Pine trampoline on SharedPreferencesImpl triggers Alibaba Security ART memory scan
        // hookPrivacyMethods(cl); // Disabled: Pine trampoline triggers Alibaba Security ART memory scan
        // hookExportedActivityUtils(cl); // Disabled: Pine trampoline triggers Alibaba Security ART memory scan
        // hookSystemExit(); // Disabled: Handled natively by BoxCore kill/tgkill hooks
        // hookProcessKill(); // Disabled: Handled natively by BoxCore kill/tgkill hooks
        // hookPrivacyPolicyUi(cl); // Disabled: Pine trampoline triggers Alibaba Security ART memory scan
        
        // hookSafeGuardMain(cl); // Disabled: Pine trampoline triggers Alibaba Security ART memory scan (SIGSEGV code 128)
        // hookSafeGuardInterface(cl); // Disabled: Pine trampoline triggers Alibaba Security ART memory scan (SIGSEGV code 128)

        Log.i(TAG, "DingTalk hooks installed (framework level only - zero Pine ART method hooks)");
    }

    private static void hookSafeGuardMain(ClassLoader cl) {
        try {
            Class<?> clazz = XposedHelpers.findClass("com.alibaba.dingtalk.safeguard.SafeGuardMain", cl);
            for (Method m : clazz.getDeclaredMethods()) {
                if ("getSecur".equals(m.getName()) || "doUploadBasicData".equals(m.getName())) {
                    XposedBridge.hookMethod(m, new XC_MethodReplacement() {
                        @Override
                        protected Object replaceHookedMethod(XC_MethodHook.MethodHookParam param) {
                            Log.i(TAG, "[xh-align] SafeGuardMain." + param.method.getName() + " intercepted");
                            return null;
                        }
                    });
                    Log.i(TAG, "[xh-align] SafeGuardMain." + m.getName() + " hooked");
                }
            }
        } catch (Throwable t) {
            Log.w(TAG, "[xh-align] SafeGuardMain hook fail: " + t.getMessage());
        }
    }

    private static void hookSafeGuardInterface(ClassLoader cl) {
        try {
            Class<?> clazz = XposedHelpers.findClass("com.alibaba.dingtalk.safeguard.SafeGuardInterface$CppProxy", cl);
            for (Method m : clazz.getDeclaredMethods()) {
                if ("execCmd".equals(m.getName()) || "execCmdNative".equals(m.getName())) {
                    XposedBridge.hookMethod(m, new XC_MethodReplacement() {
                        @Override
                        protected Object replaceHookedMethod(XC_MethodHook.MethodHookParam param) {
                            Log.i(TAG, "[xh-align] SafeGuardInterface." + param.method.getName() + " intercepted");
                            return 0;
                        }
                    });
                }
            }
        } catch (Throwable t) {
            Log.w(TAG, "[xh-align] SafeGuardInterface hook fail: " + t.getMessage());
        }
    }

    private static void hookServiceManager(ClassLoader cl) {
        try {
            Class<?> clazz = XposedHelpers.findClass("android.os.ServiceManager", cl);
            XposedHelpers.findAndHookMethod(clazz, "getService", String.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    String name = (String) param.args[0];
                    if (name != null) {
                        String lower = name.toLowerCase();
                        for (String blocked : BLOCKED_SERVICES) {
                            if (lower.startsWith(blocked) || lower.equals(blocked)) {
                                Log.i(TAG, "[xh-align] ServiceManager.getService(" + name + ") blocked");
                                param.setResult(null);
                                return;
                            }
                        }
                    }
                }
            });
        } catch (Throwable t) {
            Log.w(TAG, "[xh-align] ServiceManager hook fail: " + t.getMessage());
        }
    }

    private static void hookActivityThread(ClassLoader cl) {
        try {
            Class<?> clazz = XposedHelpers.findClass("android.app.ActivityThread", cl);
            XposedHelpers.findAndHookMethod(clazz, "currentActivityThread", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    // Only run once — this method is called frequently, reflection is expensive
                    if (sPackagesCleaned) return;
                    Object thread = param.getResult();
                    if (thread == null) return;
                    sPackagesCleaned = true;
                    try {
                        java.lang.reflect.Field f = thread.getClass().getDeclaredField("mPackages");
                        f.setAccessible(true);
                        @SuppressWarnings("unchecked")
                        java.util.Map<String, ?> map = (java.util.Map<String, ?>) f.get(thread);
                        if (map != null) {
                            synchronized (map) {
                                java.util.Iterator<String> it = map.keySet().iterator();
                                while (it.hasNext()) {
                                    String pkg = it.next();
                                    if (pkg != null && (pkg.contains("com.sx") || pkg.contains("blackbox"))) {
                                        it.remove();
                                        Log.i(TAG, "[xh-align] Cleaned sandbox package from mPackages: " + pkg);
                                    }
                                }
                            }
                        }
                    } catch (Throwable t) {
                        Log.w(TAG, "[xh-align] mPackages cleanup fail: " + t.getMessage());
                    }
                }
            });
        } catch (Throwable t) {
            Log.w(TAG, "[xh-align] ActivityThread hook fail: " + t.getMessage());
        }
    }

    private static void hookBaseDexClassLoader(ClassLoader cl) {
        try {
            Class<?> clazz = ClassLoader.getSystemClassLoader().loadClass("dalvik.system.BaseDexClassLoader");
            XposedHelpers.findAndHookMethod(clazz, "toString", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    String res = (String) param.getResult();
                    if (res != null) {
                        String sanitized = res;
                        if (sanitized.contains("blackbox")) sanitized = sanitized.replace("blackbox", "system");
                        if (sanitized.contains("com.sx.app")) sanitized = sanitized.replace("com.sx.app", "com.android.system");
                        if (sanitized.contains("engine-bb")) sanitized = sanitized.replace("engine-bb", "framework");
                        if (!sanitized.equals(res)) {
                            param.setResult(sanitized);
                            Log.i(TAG, "[xh-align] BaseDexClassLoader.toString sanitized sandbox paths");
                        }
                    }
                }
            });
        } catch (Throwable t) {
            Log.w(TAG, "[xh-align] BaseDexClassLoader hook fail: " + t.getMessage());
        }
    }

    private static void hookMtopRequest(ClassLoader cl) {
        try {
            Class<?> clazz = XposedHelpers.findClass("mtopsdk.mtop.domain.MtopRequest", cl);
            XposedHelpers.findAndHookMethod(clazz, "setData", String.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    String data = (String) param.args[0];
                    if (data != null) {
                        String sanitized = data
                                .replaceAll("(\"isRoot\"\\s*:\\s*)\"?true\"?", "$1\"false\"")
                                .replaceAll("(\"isEmulator\"\\s*:\\s*)\"?true\"?", "$1\"false\"")
                                .replaceAll("(\"xposed\"\\s*:\\s*)\"?true\"?", "$1\"false\"")
                                .replaceAll("(\"isVirtualEnv\"\\s*:\\s*)\"?true\"?", "$1\"false\"");
                        if (!sanitized.equals(data)) {
                            param.args[0] = sanitized;
                            Log.i(TAG, "[xh-align] MtopRequest.setData sanitized environment risk flags");
                        }
                    }
                }
            });
        } catch (Throwable t) {
            Log.w(TAG, "[xh-align] MtopRequest hook fail: " + t.getMessage());
        }
    }

    private static void hookDimensionValueSet(ClassLoader cl) {
        try {
            Class<?> clazz = XposedHelpers.findClass("com.alibaba.mtl.appmonitor.model.DimensionValueSet", cl);
            XposedHelpers.findAndHookMethod(clazz, "setValue", String.class, String.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    String key = (String) param.args[0];
                    if (key != null) {
                        String k = key.toLowerCase();
                        if (k.contains("sandbox") || k.contains("root") || k.contains("xposed")
                                || k.contains("container") || k.contains("emulator") || k.contains("virtual")) {
                            param.args[1] = "0";
                            Log.i(TAG, "[xh-align] DimensionValueSet.setValue sanitized risk metric key=" + key);
                        }
                    }
                }
            });
        } catch (Throwable t) {
            Log.w(TAG, "[xh-align] DimensionValueSet hook fail: " + t.getMessage());
        }
    }

    private static void hookLauncherPlugin(ClassLoader cl) {
        try {
            Class<?> clazz = XposedHelpers.findClass("com.alibaba.lightapp.runtime.plugin.device.Launcher", cl);
            XposedHelpers.findAndHookMethod(clazz, "checkShowItem", String.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    Log.i(TAG, "[xh-align] Launcher.checkShowItem forced false");
                    param.setResult(false);
                }
            });
        } catch (Throwable t) {
            Log.w(TAG, "[xh-align] Launcher plugin hook fail: " + t.getMessage());
        }
    }

    private static void hookSplitCompat(ClassLoader cl) {
        String[] splitCompatClasses = {
                "com.google.android.play.core.splitcompat.SplitCompat",
                "com.alibaba.appbundle.splitcompat.SplitCompat",
                "com.alibaba.android.rimet.splitcompat.SplitCompat"
        };
        for (String className : splitCompatClasses) {
            try {
                Class<?> clazz = XposedHelpers.findClass(className, cl);
                for (Method m : clazz.getDeclaredMethods()) {
                    if (m.getName().startsWith("install") || "a".equals(m.getName())) {
                        XposedBridge.hookMethod(m, new XC_MethodHook() {
                            @Override
                            protected void beforeHookedMethod(MethodHookParam param) {
                                Log.i(TAG, "[xh-align] SplitCompat." + m.getName() + " intercepted");
                                if (m.getReturnType() == boolean.class || m.getReturnType() == Boolean.class) {
                                    param.setResult(true);
                                } else {
                                    param.setResult(null);
                                }
                            }
                        });
                    }
                }
                Log.i(TAG, "[xh-align] SplitCompat hooked: " + className);
            } catch (Throwable ignored) {
            }
        }
    }

    public static void initPrivacyPreferencesOnDisk(android.content.Context context, String packageName, int userId) {
        if (context == null || !PACKAGE.equals(packageName)) return;
        try {
            java.io.File prefsDir = new java.io.File(context.getDataDir(), "virtual/users/" + userId + "/packages/" + packageName + "/shared_prefs");
            if (!prefsDir.exists()) {
                prefsDir.mkdirs();
            }
            writePrivacyXml(new java.io.File(prefsDir, "com.alibaba.android.rimet_preferences.xml"));
            writePrivacyXml(new java.io.File(prefsDir, "privacy_shared_preference.xml"));
            writePrivacyXml(new java.io.File(prefsDir, "privacy_dialog_prefs.xml"));
            writePrivacyXml(new java.io.File(prefsDir, "rimet_privacy.xml"));
            Log.i(TAG, "Privacy preferences written to disk XML files successfully.");
        } catch (Throwable t) {
            Log.w(TAG, "initPrivacyPreferencesOnDisk fail: " + t.getMessage());
        }
    }

    private static void writePrivacyXml(java.io.File file) {
        try (java.io.FileWriter fw = new java.io.FileWriter(file)) {
            fw.write("<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n" +
                     "<map>\n" +
                     "    <boolean name=\"privacy_dialog_has_shown\" value=\"true\" />\n" +
                     "    <boolean name=\"privacy_agree\" value=\"true\" />\n" +
                     "    <boolean name=\"pref_key_privacy_policy_agree\" value=\"true\" />\n" +
                     "    <boolean name=\"key_privacy_policy_agree\" value=\"true\" />\n" +
                     "    <boolean name=\"privacy_policy_user_agree\" value=\"true\" />\n" +
                     "    <boolean name=\"sp_key_privacy_agree\" value=\"true\" />\n" +
                     "    <boolean name=\"agreed_privacy\" value=\"true\" />\n" +
                     "    <boolean name=\"show_privacy\" value=\"false\" />\n" +
                     "    <int name=\"privacy_agree_version\" value=\"999\" />\n" +
                     "</map>");
        } catch (Throwable ignored) {
        }
    }

    private static void hookPrivacyPreferences() {
        try {
            Class<?> spi = XposedHelpers.findClass("android.app.SharedPreferencesImpl", null);
            XposedHelpers.findAndHookMethod(spi, "getBoolean", String.class, boolean.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            String key = param.args[0] instanceof String ? (String) param.args[0] : null;
                            if (key == null) return;
                            String k = key.toLowerCase();
                            if (k.contains("show_privacy") || k.contains("privacy_dialog")) {
                                param.setResult(false);
                            } else if ((k.contains("agree") && k.contains("privacy"))
                                    || k.contains("privacy_statement")
                                    || "agreed_privacy".equals(k)
                                    || "ignore_privacy".equals(k)) {
                                param.setResult(true);
                            }
                        }
                    });
            XposedHelpers.findAndHookMethod(spi, "getInt", String.class, int.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            String key = param.args[0] instanceof String ? (String) param.args[0] : null;
                            if (key != null && key.toLowerCase().contains("privacy")
                                    && key.toLowerCase().contains("agree")) {
                                param.setResult(1);
                            }
                        }
                    });
            Log.i(TAG, "privacy SP ok");
        } catch (Throwable t) {
            Log.w(TAG, "privacy SP fail: " + t.getMessage());
        }
    }

    /** Best-effort: force any boolean isAgree*Privacy* methods on loaded ding classes. */
    private static void hookPrivacyMethods(ClassLoader cl) {
        // Hook Application package-level helpers if present (names from 7.8.10 strings).
        String[] classes = {
                "com.alibaba.android.rimet.LauncherApplication",
                "com.alibaba.android.rimet.RimetApplication",
                "com.alibaba.android.dingtalkbase.DingtalkBaseApplication"
        };
        for (String cn : classes) {
            try {
                Class<?> c = XposedHelpers.findClass(cn, cl);
                for (Method m : c.getDeclaredMethods()) {
                    String n = m.getName().toLowerCase();
                    if (m.getParameterTypes().length != 0) continue;
                    if (m.getReturnType() != boolean.class && m.getReturnType() != Boolean.class) continue;
                    if (!(n.contains("privacy") || n.contains("agree"))) continue;
                    XposedBridge.hookMethod(m, new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            param.setResult(true);
                        }
                    });
                    Log.i(TAG, "forced " + cn + "#" + m.getName());
                }
            } catch (Throwable ignored) {
            }
        }
    }

    private static void hookExportedActivityUtils(ClassLoader cl) {
        try {
            Class<?> utils = XposedHelpers.findClass(
                    "com.alibaba.android.rimet.ExportedActivityUtils", cl);
            for (Method m : utils.getDeclaredMethods()) {
                Class<?>[] pts = m.getParameterTypes();
                if (!"a".equals(m.getName()) || pts.length != 1
                        || !Activity.class.isAssignableFrom(pts[0])) {
                    continue;
                }
                XposedBridge.hookMethod(m, new XC_MethodHook() {
                    @Override
                    protected void beforeHookedMethod(MethodHookParam param) {
                        Log.i(TAG, "skip ExportedActivityUtils.a");
                        param.setResult(null);
                    }
                });
            }
            Log.i(TAG, "ExportedActivityUtils.a ok");
        } catch (Throwable t) {
            Log.w(TAG, "ExportedActivityUtils fail: " + t.getMessage());
        }
    }

    private static void hookSystemExit() {
        XC_MethodHook block = new XC_MethodHook() {
            @Override
            protected void beforeHookedMethod(MethodHookParam param) {
                Log.w(TAG, "block exit " + param.method);
                param.setResult(null);
            }
        };
        try {
            XposedHelpers.findAndHookMethod(System.class, "exit", int.class, block);
            XposedHelpers.findAndHookMethod(Runtime.class, "exit", int.class, block);
        } catch (Throwable t) {
            Log.w(TAG, "exit hook fail", t);
        }
    }

    private static void hookProcessKill() {
        try {
            XposedHelpers.findAndHookMethod(Process.class, "killProcess", int.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    int pid = param.args[0] instanceof Integer ? (Integer) param.args[0] : -1;
                    if (pid == Process.myPid()) {
                        Log.w(TAG, "block killProcess(self)");
                        param.setResult(null);
                    }
                }
            });
            XposedHelpers.findAndHookMethod(Process.class, "sendSignal", int.class, int.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            int pid = param.args[0] instanceof Integer ? (Integer) param.args[0] : -1;
                            int sig = param.args[1] instanceof Integer ? (Integer) param.args[1] : -1;
                            if (pid == Process.myPid() && sig != 0) {
                                Log.w(TAG, "block sendSignal(self," + sig + ")");
                                param.setResult(null);
                            }
                        }
                    });
        } catch (Throwable t) {
            Log.w(TAG, "process kill hook fail: " + t.getMessage());
        }
    }

    private static void hookPrivacyPolicyUi(ClassLoader cl) {
        try {
            Class<?> privacy = XposedHelpers.findClass(
                    "com.alibaba.android.rimet.PrivacyPolicyActivity", cl);
            XposedHelpers.findAndHookMethod(privacy, "onCreate", android.os.Bundle.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            final Activity a = (Activity) param.thisObject;
                            Handler h = new Handler(Looper.getMainLooper());
                            h.postDelayed(() -> tryClickAgree(a), 500);
                            h.postDelayed(() -> tryClickAgree(a), 1500);
                            h.postDelayed(() -> tryClickAgree(a), 3000);
                        }
                    });
            Log.i(TAG, "PrivacyPolicy auto-agree ok");
        } catch (Throwable t) {
            Log.w(TAG, "PrivacyPolicy hook: " + t.getMessage());
        }
    }

    private static void tryClickAgree(Activity activity) {
        if (activity == null || activity.isFinishing()) return;
        try {
            View root = activity.getWindow() != null ? activity.getWindow().getDecorView() : null;
            if (root == null) return;
            List<View> clicks = new ArrayList<>();
            collect(root, clicks);
            for (View v : clicks) {
                CharSequence text = v instanceof TextView ? ((TextView) v).getText() : v.getContentDescription();
                if (text == null) continue;
                String d = text.toString().trim();
                if (d.contains("同意") || d.contains("接受") || d.contains("继续")
                        || d.contains("我知道了") || d.contains("开始使用") || d.contains("确定")
                        || d.equalsIgnoreCase("Agree") || d.equalsIgnoreCase("OK")) {
                    Log.i(TAG, "auto-click: " + d);
                    v.performClick();
                    return;
                }
            }
        } catch (Throwable ignored) {
        }
    }

    private static void collect(View v, List<View> out) {
        if (v == null) return;
        if (v.isClickable() && v.getVisibility() == View.VISIBLE) out.add(v);
        if (v instanceof ViewGroup) {
            ViewGroup g = (ViewGroup) v;
            for (int i = 0; i < g.getChildCount(); i++) collect(g.getChildAt(i), out);
        }
    }
}
