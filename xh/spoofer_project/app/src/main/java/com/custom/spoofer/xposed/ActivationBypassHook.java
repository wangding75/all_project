package com.custom.spoofer.xposed;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CompoundButton;
import android.widget.FrameLayout;

import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage.LoadPackageParam;

public class ActivationBypassHook {

    private static final String TAG = "[ActivationBypass]";
    private static final String TARGET_PACKAGE = "com.xin.h6";
    private static final String MY_UTIL_CLASS = "com.loc.va.utils.MyUtil";
    private static final String ACTIVE_CARD_ACTIVITY = "com.loc.va.ui.activity.ActiveCardActivity";

    // 伪造激活所需核心证书与各种授权字段候选名
    private static final String FAKE_TOKEN = "12345678901";
    private static final List<String> CANDIDATE_KEYS = Arrays.asList(
            "token", "card", "ck", "key", "account", "endTime", "app_authorization",
            "card_num", "card_id", "cardId", "cardNumber", "license", "activation",
            "activation_code", "active_code", "user", "password", "pass", "pwd",
            "sign", "sig", "signature", "hash", "id", "uuid", "imei", "device_id",
            "deviceId", "serial", "serial_no", "serialNo",
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"
    );

    // 伪造的主配置 JSON 串：CORE 代表主证书
    private static final String FAKE_CORE_CONFIG = "eyJ2aXAiOjEsImFjdGl2ZSI6MSwiZXhwaXJlIjoiMjA5OS0xMi0xMyAxMjoxMzoxNCIsInRva2VuIjoiMTIzNDU2Nzg5MDEifQ==";

    // 动态劫持 JSON 构造器时保护用的 ThreadLocal，防止陷入堆栈无限递归循环
    private static final ThreadLocal<Boolean> sInsideJsonHook = new ThreadLocal<Boolean>() {
        @Override
        protected Boolean initialValue() {
            return false;
        }
    };

    // 伪造的从本地 SharedPreferences 解密的完整配置 Json 对象，由 hookGetConfig 触发构建
    private static JSONObject sFakeConfigJson = null;

    static {
        try {
            sFakeConfigJson = new JSONObject();
            sFakeConfigJson.put("status", 0);
            sFakeConfigJson.put("code", 0);
            sFakeConfigJson.put("message", "success");
            sFakeConfigJson.put("ak", "ujigN1eMQaVIkQZiOX3HSajguTG2anp6");
            sFakeConfigJson.put("token", FAKE_TOKEN);
            sFakeConfigJson.put("uid", "6003332880");
            sFakeConfigJson.put("sk", "NnTHv0E6vGKAMV8ZawqpcEIQTebpnKju");
            sFakeConfigJson.put("user_permission", 1);
            sFakeConfigJson.put("ak_permission", 1);
            sFakeConfigJson.put("up", 1);
            sFakeConfigJson.put("ap", 1);
            sFakeConfigJson.put("en", 1);
            sFakeConfigJson.put("current", 1784006865217L);
            sFakeConfigJson.put("detail", null);

            JSONObject datas = new JSONObject();
            datas.put("account", "12345678901");
            datas.put("summary", "success");
            datas.put("price", 1.0);
            datas.put("period", 1);
            datas.put("activeTime", "2026-07-14 20:21:44");
            datas.put("endTime", "2099-12-13 12:13:14");
            datas.put("expire", "2099-12-13 12:13:14");
            datas.put("time", "2099-12-13 12:13:14");
            for (String key : CANDIDATE_KEYS) {
                if ("endTime".equalsIgnoreCase(key) || "activeTime".equalsIgnoreCase(key) 
                        || "expire".equalsIgnoreCase(key) || "time".equalsIgnoreCase(key)
                        || "current".equalsIgnoreCase(key)) {
                    continue;
                }
                datas.put(key, "12345678901");
            }
            sFakeConfigJson.put("datas", datas);

            sFakeConfigJson.put("activeTime", "2026-07-14 20:21:44");
            sFakeConfigJson.put("endTime", "2099-12-13 12:13:14");
            sFakeConfigJson.put("expire", "2099-12-13 12:13:14");
            sFakeConfigJson.put("time", "2099-12-13 12:13:14");
            for (String key : CANDIDATE_KEYS) {
                if ("endTime".equalsIgnoreCase(key) || "activeTime".equalsIgnoreCase(key) 
                        || "expire".equalsIgnoreCase(key) || "time".equalsIgnoreCase(key)
                        || "current".equalsIgnoreCase(key)) {
                    continue;
                }
                sFakeConfigJson.put(key, "12345678901");
            }
        } catch (Exception e) {
            XposedBridge.log(TAG + " Static init FAILED: " + e.getMessage());
        }
    }

    public static void install(final LoadPackageParam lpparam) {
        XposedBridge.log(TAG + " Injected into: " + lpparam.packageName);

        // Hook attachBaseContext 以获得被360加固壳解密后的真实 ClassLoader
        hook360Stub(lpparam.classLoader);
    }

    // ─────────────────────────────────────────────────────────────
    // 360 加固壳attachBaseContext拦截
    // ─────────────────────────────────────────────────────────────
    private static void hook360Stub(ClassLoader classLoader) {
        try {
            XposedHelpers.findAndHookMethod(
                    "com.stub.StubApp",
                    classLoader,
                    "attachBaseContext",
                    Context.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            Context context = (Context) param.args[0];
                            ClassLoader realClassLoader = context.getClassLoader();
                            XposedBridge.log(TAG + " 360 StubApp attachBaseContext executed. Real ClassLoader retrieved: " + realClassLoader);

                            // 开始在真实 ClassLoader 域中注册所有 Xposed Hook 逻辑
                            hookHomeFragmentJ0(realClassLoader);
                            hookD5B(realClassLoader);
                            hookGetConfig(realClassLoader);
                            hookGetConfig2(realClassLoader);
                            hookSystemLogger(realClassLoader);
                            hookCrypto(realClassLoader);
                            hookStartActivityRedirect(realClassLoader);
                            hookActiveCardActivityFinish(realClassLoader);
                            hookVDingManager(realClassLoader);
                            hookVActivityManager(realClassLoader);
                            hookNativeEngineSendPost(realClassLoader);
                            hookSignatureValidationHelper(realClassLoader);
                            hookExtension(realClassLoader);
                            hookNativeClickHandlers(realClassLoader);
                        }
                    });
            XposedBridge.log(TAG + " Hooked com.stub.StubApp.attachBaseContext successfully.");
        } catch (Throwable t1) {
            XposedBridge.log(TAG + " Hooking com.stub.StubApp failed, trying fallback to android.app.Application.attachBaseContext. Error: " + t1.getMessage());
            try {
                XposedHelpers.findAndHookMethod(
                        "android.app.Application",
                        classLoader,
                        "attachBaseContext",
                        Context.class,
                        new XC_MethodHook() {
                            @Override
                            protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                                Context context = (Context) param.args[0];
                                ClassLoader realClassLoader = context.getClassLoader();
                                XposedBridge.log(TAG + " Fallback attachBaseContext executed. Real ClassLoader: " + realClassLoader);

                                hookHomeFragmentJ0(realClassLoader);
                                hookD5B(realClassLoader);
                                hookGetConfig(realClassLoader);
                                hookGetConfig2(realClassLoader);
                                hookSystemLogger(realClassLoader);
                                hookCrypto(realClassLoader);
                                hookStartActivityRedirect(realClassLoader);
                                hookActiveCardActivityFinish(realClassLoader);
                                hookVDingManager(realClassLoader);
                                hookVActivityManager(realClassLoader);
                                hookNativeEngineSendPost(realClassLoader);
                                hookSignatureValidationHelper(realClassLoader);
                                hookExtension(realClassLoader);
                                hookNativeClickHandlers(realClassLoader);
                            }
                        });
                XposedBridge.log(TAG + " Fallback android.app.Application.attachBaseContext hook registered.");
            } catch (Throwable t2) {
                XposedBridge.log(TAG + " Fallback Application.attachBaseContext hook FAILED: " + t2.getMessage());
            }
        }
    }

    // ─────────────────────────────────────────────────────────────
    // 注入 HomeFragment 安全网（Crash Shield），防 native NPE 崩溃
    // ─────────────────────────────────────────────────────────────
    private static void hookHomeFragmentJ0(ClassLoader classLoader) {
        try {
            XposedHelpers.findAndHookMethod(
                    "com.loc.va.ui.activity.HomeFragment",
                    classLoader,
                    "onCreateView",
                    LayoutInflater.class,
                    ViewGroup.class,
                    Bundle.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            if (param.hasThrowable()) {
                                Throwable t = param.getThrowable();
                                XposedBridge.log(TAG + " [Crash-Shield] HomeFragment.onCreateView crashed! Swallowing exception: " + t.getMessage());
                                param.setThrowable(null); // Clear the crash exception
                                
                                // Fallback to an empty view so the app remains alive
                                LayoutInflater inflater = (LayoutInflater) param.args[0];
                                FrameLayout emptyView = new FrameLayout(inflater.getContext());
                                param.setResult(emptyView);
                            } else {
                                XposedBridge.log(TAG + " [Crash-Shield] HomeFragment.onCreateView loaded successfully without crash.");
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Crash-Shield] HomeFragment.onCreateView safety wrap hook registered via " + classLoader);
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Crash-Shield] HomeFragment.onCreateView hook failed: " + t.getMessage());
        }
    }

    // ─────────────────────────────────────────────────────────────
    // 针对核心混淆校验类 d5.b 进行方法全局劫持绕过
    // ─────────────────────────────────────────────────────────────
    private static void hookD5B(ClassLoader classLoader) {
        try {
            Class<?> clazz = classLoader.loadClass("d5.b");
            XposedBridge.log(TAG + " [d5.b] Hooking d5.b core decision methods...");

            // Hook d(String) -> Boolean
            XposedHelpers.findAndHookMethod(clazz, "d", String.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    XposedBridge.log(TAG + " [d5.b] d(String=" + param.args[0] + ") called.");
                }
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    XposedBridge.log(TAG + " [d5.b] d(String) original returned: " + param.getResult());
                }
            });

            // Hook e(String) -> boolean
            XposedHelpers.findAndHookMethod(clazz, "e", String.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    XposedBridge.log(TAG + " [d5.b] e(String=" + param.args[0] + ") called.");
                }
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    XposedBridge.log(TAG + " [d5.b] e(String) original returned: " + param.getResult());
                }
            });

            // Hook f(String) -> boolean
            XposedHelpers.findAndHookMethod(clazz, "f", String.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    XposedBridge.log(TAG + " [d5.b] f(String=" + param.args[0] + ") called.");
                }
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    XposedBridge.log(TAG + " [d5.b] f(String) original returned: " + param.getResult());
                }
            });

            // Hook g(String) -> boolean
            XposedHelpers.findAndHookMethod(clazz, "g", String.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    XposedBridge.log(TAG + " [d5.b] g(String=" + param.args[0] + ") called.");
                }
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    XposedBridge.log(TAG + " [d5.b] g(String) original returned: " + param.getResult());
                }
            });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [d5.b] Hooking d5.b core decision FAILED: " + t.getMessage());
        }
    }

    // ─────────────────────────────────────────────────
    // 第一层：Hook getConfig，注入伪造激活主配置
    // ─────────────────────────────────────────────────
    private static void hookGetConfig(ClassLoader classLoader) {
        try {
            XposedHelpers.findAndHookMethod(
                    MY_UTIL_CLASS,
                    classLoader,
                    "getConfig",
                    Context.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String key = (String) param.args[1];
                            if ("CORE".equals(key)) {
                                param.setResult(FAKE_CORE_CONFIG);
                                XposedBridge.log(TAG + " [Layer-1] MyUtil.getConfig(CORE) → injected fake license config.");
                            } else if ("app_authorization".equals(key)) {
                                param.setResult("12345678901");
                                XposedBridge.log(TAG + " [Layer-1] MyUtil.getConfig(app_authorization) → injected mock key 12345678901.");
                            } else {
                                XposedBridge.log(TAG + " [Layer-1] MyUtil.getConfig(key=" + key + ") → passed through.");
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Layer-1] MyUtil.getConfig hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Layer-1] MyUtil.getConfig hook FAILED: " + t.getMessage());
        }
    }

    // ─────────────────────────────────────────────────
    // 第二层：Hook getConfig2，子键注入激活字段值
    // ─────────────────────────────────────────────────
    private static void hookGetConfig2(ClassLoader classLoader) {
        try {
            XposedHelpers.findAndHookMethod(
                    MY_UTIL_CLASS,
                    classLoader,
                    "getConfig2",
                    Context.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String subKey = (String) param.args[1];
                            Object originalResult = param.getResult();

                            if (sFakeConfigJson != null && sFakeConfigJson.has(subKey)) {
                                String fakeValue = sFakeConfigJson.optString(subKey, "");
                                param.setResult(fakeValue);
                                XposedBridge.log(TAG + " [Layer-2] MyUtil.getConfig2(subKey=" + subKey
                                        + ") → injected [" + fakeValue + "] (original was: [" + originalResult + "])");
                            } else {
                                // 针对经纬度设置（不区分大小写），若无配置字段值则强制兜底为有效Double字符串 "0.0"，防JNI解析闪退
                                if (subKey.equalsIgnoreCase("rlat") || subKey.equalsIgnoreCase("rlng") 
                                        || subKey.equalsIgnoreCase("lat") || subKey.equalsIgnoreCase("lng")) {
                                    param.setResult("0.0");
                                    XposedBridge.log(TAG + " [Layer-2] MyUtil.getConfig2(subKey=" + subKey
                                            + ") → forced fallback [0.0] to bypass NumberFormatException.");
                                } else {
                                    XposedBridge.log(TAG + " [Layer-2] MyUtil.getConfig2(subKey=" + subKey
                                            + ") → passed through [" + originalResult + "]");
                                }
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Layer-2] MyUtil.getConfig2 hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Layer-2] MyUtil.getConfig2 hook FAILED (method may not exist): " + t.getMessage());
        }
    }

    // ─────────────────────────────────────────────────────────────
    // 全方位系统级与SharedPreferences事件 Logger 和拦截
    // ─────────────────────────────────────────────────────────────
    private static void hookSystemLogger(ClassLoader classLoader) {
        // 0. JSONObject 构造器拦截：核心拦截，防止 JNI 解密乱码造成崩溃，并使用 ThreadLocal 防递归
        try {
            XposedHelpers.findAndHookConstructor(
                    JSONObject.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            if (sInsideJsonHook.get()) {
                                return;
                            }
                            sInsideJsonHook.set(true);
                            try {
                                String json = (String) param.args[0];
                                if (json == null) return;

                                if (json.contains("\"vip\"") || json.contains("\"active\"") || json.contains("\"expire\"")) {
                                    return;
                                }

                                boolean isTarget = false;

                                if (json.contains("\"status\"") && (json.contains("\"message\"") || json.contains("\"token\""))) {
                                    isTarget = true;
                                } else if (json.contains("\"code\"") && json.contains("\"message\"") && (json.contains("\"detail\"") || json.contains("\"datas\""))) {
                                    isTarget = true;
                                }

                                if (!json.trim().startsWith("{") && !json.trim().startsWith("[")) {
                                    StackTraceElement[] stack = Thread.currentThread().getStackTrace();
                                    for (StackTraceElement element : stack) {
                                        if (element.getClassName().contains("com.loc.va") || element.getClassName().contains("com.xin.h6")) {
                                            isTarget = true;
                                            break;
                                        }
                                    }
                                }

                                if (isTarget) {
                                    boolean needsRewrite = false;
                                    try {
                                        JSONObject testObj = new JSONObject(json);
                                        int status = testObj.optInt("status", -1);
                                        int code = testObj.optInt("code", -1);
                                        if ((status != -1 && status != 0) || (code != -1 && code != 0 && code != 1)) {
                                            needsRewrite = true;
                                            XposedBridge.log(TAG + " [JSON-Init] Detected failure/error status JSON string: " + json);
                                        }
                                    } catch (Exception e) {
                                        needsRewrite = true;
                                        XposedBridge.log(TAG + " [JSON-Init] Detected invalid decryption result (JNI garbage): " + json);
                                    }

                                    if (needsRewrite) {
                                        param.args[0] = sFakeConfigJson.toString();
                                        XposedBridge.log(TAG + " [JSON-Init] Hijacked and corrected JSONObject string to: " + param.args[0]);
                                    }
                                }
                            } finally {
                                sInsideJsonHook.set(false);
                            }
                        }
                    });
            XposedBridge.log(TAG + " [JSON-Init] Hooked JSONObject(String) constructor successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [JSON-Init] Hooking JSONObject constructor FAILED: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookConstructor(
                    JSONTokener.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            String in = (String) param.args[0];
                            if (in == null) return;

                            if (in.contains("\"vip\"") || in.contains("\"active\"") || in.contains("\"expire\"")) {
                                return;
                            }

                            boolean isTarget = false;

                            if (in.contains("\"status\"") && (in.contains("\"message\"") || in.contains("\"token\""))) {
                                isTarget = true;
                            } else if (in.contains("\"code\"") && in.contains("\"message\"") && (in.contains("\"detail\"") || in.contains("\"datas\""))) {
                                isTarget = true;
                            }

                            if (!in.trim().startsWith("{") && !in.trim().startsWith("[")) {
                                StackTraceElement[] stack = Thread.currentThread().getStackTrace();
                                for (StackTraceElement element : stack) {
                                    if (element.getClassName().contains("com.loc.va") || element.getClassName().contains("com.xin.h6")) {
                                        isTarget = true;
                                        break;
                                    }
                                }
                            }

                            if (isTarget) {
                                boolean needsRewrite = false;
                                try {
                                    if (!sInsideJsonHook.get()) {
                                        sInsideJsonHook.set(true);
                                        try {
                                            JSONObject testObj = new JSONObject(in);
                                            int status = testObj.optInt("status", -1);
                                            int code = testObj.optInt("code", -1);
                                            if ((status != -1 && status != 0) || (code != -1 && code != 0 && code != 1)) {
                                                needsRewrite = true;
                                            }
                                        } finally {
                                            sInsideJsonHook.set(false);
                                        }
                                    }
                                } catch (Exception e) {
                                    needsRewrite = true;
                                }

                                if (needsRewrite) {
                                    param.args[0] = sFakeConfigJson.toString();
                                    XposedBridge.log(TAG + " [Tokener-Init] Hijacked and corrected JSONTokener string to: " + param.args[0]);
                                }
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Tokener-Init] Hooked JSONTokener(String) constructor successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Tokener-Init] Hooking JSONTokener FAILED: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.content.ContextWrapper",
                    classLoader,
                    "getSharedPreferences",
                    String.class,
                    int.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            String name = (String) param.args[0];
                            int mode = (int) param.args[1];
                            XposedBridge.log(TAG + " [SP-Open] getSharedPreferences(name=" + name + ", mode=" + mode + ")");
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [SP-Logger] SharedPreferences open hook failed: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.app.SharedPreferencesImpl",
                    classLoader,
                    "getString",
                    String.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String key = (String) param.args[0];
                            String defValue = (String) param.args[1];
                            Object result = param.getResult();
                            XposedBridge.log(TAG + " [SP-Get] getString(key=" + key + ", def=" + defValue + ") → " + result);

                            if ("status".equals(key) && result instanceof String) {
                                String jsonStr = (String) result;
                                if (jsonStr.contains("\"status\"")) {
                                    try {
                                        JSONObject json = new JSONObject(jsonStr);
                                        for (String ckKey : CANDIDATE_KEYS) {
                                            json.put(ckKey, "12345678901");
                                        }
                                        json.put("status", 0);
                                        String modified = json.toString();
                                        param.setResult(modified);
                                        XposedBridge.log(TAG + " [SP-Get] Dynamically patched status JSON containing all candidates. Result: " + modified);
                                    } catch (Exception e) {
                                        XposedBridge.log(TAG + " [SP-Get] Failed to patch status JSON: " + e.getMessage());
                                    }
                                }
                            }
                            if ("app_authorization".equals(key)) {
                                param.setResult("12345678901");
                                XposedBridge.log(TAG + " [SP-Get] Dynamically patched app_authorization to 12345678901");
                            }
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [SP-Logger] SharedPreferences getString hook failed: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.app.SharedPreferencesImpl$EditorImpl",
                    classLoader,
                    "putString",
                    String.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            String key = (String) param.args[0];
                            String value = (String) param.args[1];
                            XposedBridge.log(TAG + " [SP-Put] putString(key=" + key + ", value=" + value + ")");

                            if ("status".equals(key) && value != null) {
                                if (value.contains("\"status\"")) {
                                    try {
                                        JSONObject json = new JSONObject(value);
                                        json.put("status", 0);
                                        json.put("message", "success");
                                        for (String ckKey : CANDIDATE_KEYS) {
                                            json.put(ckKey, "12345678901");
                                        }
                                        String modified = json.toString();
                                        param.args[1] = modified;
                                        XposedBridge.log(TAG + " [SP-Put] Dynamically patched written status JSON to success: " + modified);
                                    } catch (Exception e) {
                                        XposedBridge.log(TAG + " [SP-Put] Failed to patch written status JSON: " + e.getMessage());
                                    }
                                }
                            }
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [SP-Logger] SharedPreferences putString hook failed: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.content.Intent",
                    classLoader,
                    "getStringExtra",
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String key = (String) param.args[0];
                            Object result = param.getResult();
                            XposedBridge.log(TAG + " [Intent-Get] getStringExtra(key=" + key + ") → " + result);
                            if (result == null || "".equals(result)) {
                                for (String ckKey : CANDIDATE_KEYS) {
                                    if (ckKey.equalsIgnoreCase(key)) {
                                        param.setResult("12345678901");
                                        XposedBridge.log(TAG + " [Intent-Get] Patched null/empty Intent extra key " + key + " to 12345678901");
                                        break;
                                    }
                                }
                            }
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Intent-Logger] Hook failed: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.os.BaseBundle",
                    classLoader,
                    "getString",
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String key = (String) param.args[0];
                            Object result = param.getResult();
                            XposedBridge.log(TAG + " [Bundle-Get] getString(key=" + key + ") → " + result);
                            if (result == null || "".equals(result)) {
                                for (String ckKey : CANDIDATE_KEYS) {
                                    if (ckKey.equalsIgnoreCase(key)) {
                                        param.setResult("12345678901");
                                        XposedBridge.log(TAG + " [Bundle-Get] Patched null/empty Bundle key " + key + " to 12345678901");
                                        break;
                                    }
                                }
                            }
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Bundle-Logger] Hook failed: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "java.lang.System",
                    classLoader,
                    "getProperty",
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String key = (String) param.args[0];
                            XposedBridge.log(TAG + " [System.getProperty] getProperty(key=" + key + ") → " + param.getResult());
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [System.getProperty] Hook failed: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.provider.Settings.System",
                    classLoader,
                    "getString",
                    "android.content.ContentResolver",
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String name = (String) param.args[1];
                            XposedBridge.log(TAG + " [Settings.System] getString(name=" + name + ") → " + param.getResult());
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Settings.System] Hook failed: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.provider.Settings.Secure",
                    classLoader,
                    "getString",
                    "android.content.ContentResolver",
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String name = (String) param.args[1];
                            XposedBridge.log(TAG + " [Settings.Secure] getString(name=" + name + ") → " + param.getResult());
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Settings.Secure] Hook failed: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.os.SystemProperties",
                    classLoader,
                    "get",
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String key = (String) param.args[0];
                            XposedBridge.log(TAG + " [SysProp] get(key=" + key + ") → " + param.getResult());
                        }
                    });
            XposedHelpers.findAndHookMethod(
                    "android.os.SystemProperties",
                    classLoader,
                    "get",
                    String.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String key = (String) param.args[0];
                            XposedBridge.log(TAG + " [SysProp] get(key=" + key + ", def=" + param.args[1] + ") → " + param.getResult());
                        }
                    });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [SysProp] Hook failed: " + t.getMessage());
        }

        // Hook all JSONObject getter methods with safety fallbacks
        hookJsonGetter(classLoader, "get", 0);
        hookJsonGetter(classLoader, "getString", "12345678901");
        hookJsonGetter(classLoader, "getInt", 0);
        hookJsonGetter(classLoader, "getBoolean", false);
        hookJsonGetter(classLoader, "getDouble", 0.0);
        hookJsonGetter(classLoader, "getLong", 0L);
        hookJsonGetter(classLoader, "getJSONObject", new JSONObject());
        hookJsonGetter(classLoader, "getJSONArray", new org.json.JSONArray());

        try {
            XposedHelpers.findAndHookMethod(
                    "com.loc.va.ui.activity.n0",
                    classLoader,
                    "launchApp",
                    "com.loc.va.model.AppData",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            Object appData = param.args[0];
                            XposedBridge.log(TAG + " [n0-Presenter] launchApp called! AppData: " + appData);
                        }
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            XposedBridge.log(TAG + " [n0-Presenter] launchApp finished. Exception: " + param.getThrowable());
                        }
                    });
            XposedBridge.log(TAG + " [n0-Presenter] Hooked launchApp successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [n0-Presenter] Hooking launchApp FAILED: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "com.loc.va.home.p",
                    classLoader,
                    "launchApp",
                    "com.loc.va.model.AppData",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            Object appData = param.args[0];
                            XposedBridge.log(TAG + " [HomePresenterImpl-p] launchApp called! AppData: " + appData);
                        }
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            XposedBridge.log(TAG + " [HomePresenterImpl-p] launchApp finished. Exception: " + param.getThrowable());
                        }
                    });
            XposedBridge.log(TAG + " [HomePresenterImpl-p] Hooked launchApp successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [HomePresenterImpl-p] Hooking launchApp FAILED: " + t.getMessage());
        }

        hookVActivityManager(classLoader);
    }

    private static void hookJsonGetter(ClassLoader classLoader, String methodName, final Object defaultFallback) {
        try {
            XposedHelpers.findAndHookMethod(
                    JSONObject.class,
                    methodName,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            if (param.hasThrowable()) {
                                Throwable t = param.getThrowable();
                                if (t instanceof JSONException) {
                                    String key = (String) param.args[0];
                                    Object fallback = defaultFallback;
                                    if ("message".equalsIgnoreCase(key) || "summary".equalsIgnoreCase(key)) {
                                        fallback = "success";
                                    } else if ("activeTime".equalsIgnoreCase(key)) {
                                        fallback = "2026-07-14 20:21:44";
                                    } else if ("endTime".equalsIgnoreCase(key) || "expire".equalsIgnoreCase(key)) {
                                        fallback = "2099-12-13 12:13:14";
                                    } else if (key.toLowerCase().contains("risk") || key.toLowerCase().contains("error") 
                                            || key.toLowerCase().contains("fail") || "status".equalsIgnoreCase(key) 
                                            || "code".equalsIgnoreCase(key)) {
                                        if (defaultFallback instanceof Integer) fallback = 0;
                                        else if (defaultFallback instanceof Double) fallback = 0.0;
                                        else if (defaultFallback instanceof Long) fallback = 0L;
                                        else if (defaultFallback instanceof String) fallback = "0";
                                        else if (defaultFallback instanceof Boolean) fallback = false;
                                    } else {
                                        // For status/permission indicators (like lw, ds, de, hc), mock 1/true to allow flow
                                        if (defaultFallback instanceof Integer) fallback = 1;
                                        else if (defaultFallback instanceof Double) fallback = 1.0;
                                        else if (defaultFallback instanceof Long) fallback = 1L;
                                        else if (defaultFallback instanceof String) fallback = "1";
                                        else if (defaultFallback instanceof Boolean) fallback = true;
                                    }
                                    XposedBridge.log(TAG + " [JSON-Get] Swallowed Exception in " + param.method.getName() + " for key '" + key + "'. Mocking: " + fallback);
                                    param.setThrowable(null);
                                    param.setResult(fallback);
                                }
                            }
                        }
                    });
            XposedBridge.log(TAG + " [JSON-Get] Hooked JSONObject." + methodName + " successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [JSON-Get] Hooking JSONObject." + methodName + " FAILED: " + t.getMessage());
        }
    }

    // 加密算法兼容 Hook (防止无效密钥大小造成闪退)
    private static void hookCrypto(ClassLoader classLoader) {
        try {
            XposedHelpers.findAndHookMethod(
                    MY_UTIL_CLASS,
                    classLoader,
                    "aesEncrypt_iv",
                    String.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            String str = (String) param.args[0];
                            String key = (String) param.args[1];
                            XposedBridge.log(TAG + " [Crypto-Hook] aesEncrypt_iv(str=" + str + ", key=" + key + ")");
                            if (key == null || key.length() != 16) {
                                XposedBridge.log(TAG + " [Crypto-Hook] [WARN] Invalid key size for aesEncrypt_iv: " 
                                        + (key != null ? key.length() : 0) + " bytes. Forcing fallback key.");
                                if ("nulledcba".equals(key)) {
                                    param.args[1] = "12345678901edcba";
                                    XposedBridge.log(TAG + " [Crypto-Hook] Forced 'nulledcba' to card-aligned key '12345678901edcba'");
                                } else {
                                    param.args[1] = "1201230125462244";
                                }
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Crypto-Hook] aesEncrypt_iv hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Crypto-Hook] aesEncrypt_iv hook FAILED: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    MY_UTIL_CLASS,
                    classLoader,
                    "aesDecrypt_iv",
                    String.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            String str = (String) param.args[0];
                            String key = (String) param.args[1];
                            XposedBridge.log(TAG + " [Crypto-Hook] aesDecrypt_iv(str=" + str + ", key=" + key + ")");
                            if (key == null || key.length() != 16) {
                                XposedBridge.log(TAG + " [Crypto-Hook] [WARN] Invalid key size for aesDecrypt_iv: " 
                                        + (key != null ? key.length() : 0) + " bytes. Forcing fallback key.");
                                if ("nulledcba".equals(key)) {
                                    param.args[1] = "12345678901edcba";
                                    XposedBridge.log(TAG + " [Crypto-Hook] Forced 'nulledcba' to card-aligned key '12345678901edcba'");
                                } else {
                                    param.args[1] = "1201230125462244";
                                }
                            }
                        }
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            String result = (String) param.getResult();
                            if (result != null) {
                                if (result.contains("\"code\":") || result.contains("\"status\":")) {
                                    XposedBridge.log(TAG + " [Crypto-Hook] Detected decrypted JSON in aesDecrypt_iv: " + result);
                                    if (result.contains("\"code\":102") || result.contains("\"code\":-1") || result.contains("\"code\":1") || result.contains("\"code\":100") || result.contains("\"code\":101")) {
                                        String fakeResult = sFakeConfigJson.toString();
                                        XposedBridge.log(TAG + " [Crypto-Hook] Rewrote decrypted JSON to success: " + fakeResult);
                                        param.setResult(fakeResult);
                                    }
                                }
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Crypto-Hook] aesDecrypt_iv hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Crypto-Hook] aesDecrypt_iv hook FAILED: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    MY_UTIL_CLASS,
                    classLoader,
                    "url_encode",
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            String str = (String) param.args[0];
                            XposedBridge.log(TAG + " [MyUtil-Hook] url_encode(str=" + str + ")");
                            if (str == null) {
                                XposedBridge.log(TAG + " [MyUtil-Hook] [WARN] url_encode input is NULL! Forcing empty string.");
                                param.setResult("");
                            }
                        }
                    });
            XposedBridge.log(TAG + " [MyUtil-Hook] url_encode hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [MyUtil-Hook] url_encode hook FAILED: " + t.getMessage());
        }
    }

    // ─────────────────────────────────────────────────────────────
    // startActivity 重定向 Hook 实体声明
    // 策略：直接拦截所有 ActiveCardActivity 的启动并取消（setResult(null)）
    // ─────────────────────────────────────────────────────────────
    private static void hookStartActivityRedirect(ClassLoader classLoader) {
        try {
            XposedHelpers.findAndHookMethod(
                    "android.content.ContextWrapper",
                    classLoader,
                    "startActivity",
                    Intent.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            Intent intent = (Intent) param.args[0];
                            if (intent == null || intent.getComponent() == null) return;
                            String targetClass = intent.getComponent().getClassName();
                            if (ACTIVE_CARD_ACTIVITY.equals(targetClass)) {
                                param.setResult(null); // 直接取消启动，不跳转激活页
                                XposedBridge.log(TAG + " [Layer-3] (ContextWrapper.startActivity) BLOCKED ActiveCardActivity launch.");
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Layer-3] ContextWrapper.startActivity block hook registered.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Layer-3] ContextWrapper.startActivity hook FAILED: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.app.Activity",
                    classLoader,
                    "startActivity",
                    Intent.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            Intent intent = (Intent) param.args[0];
                            if (intent == null || intent.getComponent() == null) return;
                            String targetClass = intent.getComponent().getClassName();
                            if (ACTIVE_CARD_ACTIVITY.equals(targetClass)) {
                                param.setResult(null); // 直接取消启动
                                XposedBridge.log(TAG + " [Layer-3] (Activity.startActivity) BLOCKED ActiveCardActivity launch.");
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Layer-3] Activity.startActivity block hook registered.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Layer-3] Activity.startActivity hook FAILED: " + t.getMessage());
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "android.app.Activity",
                    classLoader,
                    "startActivityForResult",
                    Intent.class,
                    int.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            Intent intent = (Intent) param.args[0];
                            if (intent == null || intent.getComponent() == null) return;
                            String targetClass = intent.getComponent().getClassName();
                            if (ACTIVE_CARD_ACTIVITY.equals(targetClass)) {
                                param.setResult(null); // 直接取消启动
                                XposedBridge.log(TAG + " [Layer-3] (Activity.startActivityForResult) BLOCKED ActiveCardActivity launch.");
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Layer-3] Activity.startActivityForResult block hook registered.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Layer-3] Activity.startActivityForResult hook FAILED: " + t.getMessage());
        }
    }

    // ─────────────────────────────────────────────────────────────
    // Hook ActiveCardActivity.onCreate → 立刻 finish() 自己
    // ─────────────────────────────────────────────────────────────
    private static void hookActiveCardActivityFinish(ClassLoader classLoader) {
        try {
            XposedHelpers.findAndHookMethod(
                    ACTIVE_CARD_ACTIVITY,
                    classLoader,
                    "onCreate",
                    Bundle.class,
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            android.app.Activity activity = (android.app.Activity) param.thisObject;
                            XposedBridge.log(TAG + " [ActiveCard-Kill] ActiveCardActivity.onCreate() intercepted. Calling finish() immediately.");
                            activity.finish();
                        }
                    });
            XposedBridge.log(TAG + " [ActiveCard-Kill] ActiveCardActivity.onCreate hook registered.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [ActiveCard-Kill] Hooking ActiveCardActivity.onCreate FAILED: " + t.getMessage());
        }
    }

    private static void hookVDingManager(ClassLoader classLoader) {
        try {
            Class<?> clazz = classLoader.loadClass("com.lody.virtual.client.ipc.VDingManager");
            XposedBridge.log(TAG + " [VDingManager] Hooking VDingManager methods...");

            XposedHelpers.findAndHookMethod(clazz, "isEnable", int.class, String.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    param.setResult(true);
                    XposedBridge.log(TAG + " [VDingManager] Intercepted isEnable and forced true.");
                }
            });

            XposedHelpers.findAndHookMethod(clazz, "getCurAppEnable", new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    param.setResult(true);
                    XposedBridge.log(TAG + " [VDingManager] Intercepted getCurAppEnable and forced true.");
                }
            });

            XposedHelpers.findAndHookMethod(clazz, "getGlobalEnable", new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                    param.setResult(true);
                    XposedBridge.log(TAG + " [VDingManager] Intercepted getGlobalEnable and forced true.");
                }
            });
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [VDingManager] Hooking FAILED: " + t.getMessage());
        }
    }

    private static void setStaticFieldSafely(Class<?> clazz, String fieldName, int value) {
        try {
            XposedHelpers.setStaticIntField(clazz, fieldName, value);
            XposedBridge.log(TAG + " [VActivityManager] Successfully set field " + fieldName + " to " + value);
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [VActivityManager] Failed to set field " + fieldName + ": " + t.getMessage());
        }
    }

    private static void forceStaticValidationFields(Class<?> clazz) {
        setStaticFieldSafely(clazz, "c", 1);
        setStaticFieldSafely(clazz, "g", 1);
        setStaticFieldSafely(clazz, "f23939c", 1);
        setStaticFieldSafely(clazz, "f23940g", 1);
    }

    private static void hookVActivityManager(ClassLoader classLoader) {
        try {
            final Class<?> clazz = classLoader.loadClass("com.lody.virtual.client.ipc.VActivityManager");
            XposedBridge.log(TAG + " [VActivityManager] Hooking VActivityManager...");

            // Try to force static validation fields to 1 immediately
            forceStaticValidationFields(clazz);

            XposedHelpers.findAndHookMethod(
                    clazz,
                    "launchApp",
                    int.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            forceStaticValidationFields(clazz);
                            int userId = (int) param.args[0];
                            String pkgName = (String) param.args[1];
                            XposedBridge.log(TAG + " [VActivityManager] launchApp(2-args) called. userId: " + userId + ", pkg: " + pkgName);
                        }
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            XposedBridge.log(TAG + " [VActivityManager] launchApp(2-args) finished. Result: " + param.getResult());
                        }
                    });

            XposedHelpers.findAndHookMethod(
                    clazz,
                    "launchApp",
                    int.class,
                    String.class,
                    boolean.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            forceStaticValidationFields(clazz);
                            int userId = (int) param.args[0];
                            String pkgName = (String) param.args[1];
                            boolean arg2 = (boolean) param.args[2];
                            XposedBridge.log(TAG + " [VActivityManager] launchApp(3-args) called. userId: " + userId + ", pkg: " + pkgName + ", arg2: " + arg2);
                        }
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                            XposedBridge.log(TAG + " [VActivityManager] launchApp(3-args) finished. Result: " + param.getResult());
                        }
                    });

        } catch (Throwable t) {
            XposedBridge.log(TAG + " [VActivityManager] Hooking FAILED: " + t.getMessage());
        }
    }

    private static void hookNativeEngineSendPost(ClassLoader classLoader) {
        try {
            XposedHelpers.findAndHookMethod(
                    "com.lody.virtual.client.NativeEngine",
                    classLoader,
                    "sendPost",
                    String.class,
                    String.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            String url = (String) param.args[0];
                            String postData = (String) param.args[1];
                            String key = (String) param.args[2];
                            XposedBridge.log(TAG + " [NativeEngine-SendPost] url: " + url + ", postData: " + postData + ", key: " + key);
                            
                            // Return a fake successful validation JSON!
                            String mockResponse = "{\"code\":0,\"datas\":{\"token\":\"12345678901\",\"sign\":\"mock_sign\"}}";
                            param.setResult(mockResponse);
                            XposedBridge.log(TAG + " [NativeEngine-SendPost] Hijacked! Returned mock response: " + mockResponse);
                        }
                    });
            XposedBridge.log(TAG + " [NativeEngine-SendPost] Hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [NativeEngine-SendPost] Hook FAILED: " + t.getMessage());
        }
    }

    private static void hookSignatureValidationHelper(ClassLoader classLoader) {
        // Hook d5.b.a
        try {
            XposedHelpers.findAndHookMethod(
                    "d5.b",
                    classLoader,
                    "a",
                    String.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            String str = (String) param.args[0];
                            String str2 = (String) param.args[1];
                            XposedBridge.log(TAG + " [d5.b.a] Comparing: [" + str + "] with [" + str2 + "]");
                            if ("mock_sign".equals(str) || "mock_sign".equals(str2)) {
                                param.setResult(true);
                                XposedBridge.log(TAG + " [d5.b.a] Signature comparison bypassed! Forced true.");
                            }
                        }
                    });
            XposedBridge.log(TAG + " [d5.b.a] Hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [d5.b.a] Hook FAILED: " + t.getMessage());
        }

        // Hook io.busniess.va.delegate.hook.util.f.a
        try {
            XposedHelpers.findAndHookMethod(
                    "io.busniess.va.delegate.hook.util.f",
                    classLoader,
                    "a",
                    String.class,
                    String.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            String str = (String) param.args[0];
                            String str2 = (String) param.args[1];
                            XposedBridge.log(TAG + " [io.busniess.va.delegate.hook.util.f.a] Comparing: [" + str + "] with [" + str2 + "]");
                            if ("mock_sign".equals(str) || "mock_sign".equals(str2)) {
                                param.setResult(true);
                                XposedBridge.log(TAG + " [io.busniess.va.delegate.hook.util.f.a] Signature comparison bypassed! Forced true.");
                            }
                        }
                    });
            XposedBridge.log(TAG + " [io.busniess.va.delegate.hook.util.f.a] Hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [io.busniess.va.delegate.hook.util.f.a] Hook FAILED: " + t.getMessage());
        }
    }

    private static void hookExtension(ClassLoader classLoader) {
        try {
            XposedHelpers.findAndHookMethod(
                    "com.lody.virtual.server.extension.a",
                    classLoader,
                    "k",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            param.setResult(true);
                            XposedBridge.log(TAG + " [Extension-a] k() intercepted. Forcing true.");
                        }
                    });
            XposedBridge.log(TAG + " [Extension-a] k() hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Extension-a] Hooking k() FAILED: " + t.getMessage());
        }
    }

    private static void hookNativeClickHandlers(final ClassLoader classLoader) {
        // Hook com.loc.va.ui.adapters.q.g
        try {
            XposedHelpers.findAndHookMethod(
                    "com.loc.va.ui.adapters.q",
                    classLoader,
                    "g",
                    int.class,
                    "com.loc.va.model.AppData",
                    View.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            int index = (int) param.args[0];
                            Object appData = param.args[1];
                            XposedBridge.log(TAG + " [Adapter-q] g() intercepted. AppData: " + appData);
                            if (appData != null) {
                                String pkg = (String) XposedHelpers.callMethod(appData, "g");
                                int userId = (int) XposedHelpers.callMethod(appData, "h");
                                XposedBridge.log(TAG + " [Adapter-q] Manually launching userId=" + userId + ", pkg=" + pkg);
                                
                                Class<?> vamClass = classLoader.loadClass("com.lody.virtual.client.ipc.VActivityManager");
                                Object vamInstance = XposedHelpers.callStaticMethod(vamClass, "get");
                                boolean launched = (boolean) XposedHelpers.callMethod(vamInstance, "launchApp", userId, pkg);
                                XposedBridge.log(TAG + " [Adapter-q] Manual launch result: " + launched);
                                param.setResult(null); // Bypass delegate completely
                            }
                        }
                    });
            XposedBridge.log(TAG + " [Adapter-q] Hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [Adapter-q] Hooking failed: " + t.getMessage());
        }

        // Hook HomeFragment.q
        try {
            XposedHelpers.findAndHookMethod(
                    "com.loc.va.ui.activity.HomeFragment",
                    classLoader,
                    "q",
                    View.class,
                    int.class,
                    "com.loc.va.model.AppData",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            Object appData = param.args[2];
                            XposedBridge.log(TAG + " [HomeFragment-q] Intercepted. AppData: " + appData);
                            if (appData != null) {
                                String pkg = (String) XposedHelpers.callMethod(appData, "g");
                                int userId = (int) XposedHelpers.callMethod(appData, "h");
                                XposedBridge.log(TAG + " [HomeFragment-q] Manually launching userId=" + userId + ", pkg=" + pkg);
                                
                                Class<?> vamClass = classLoader.loadClass("com.lody.virtual.client.ipc.VActivityManager");
                                Object vamInstance = XposedHelpers.callStaticMethod(vamClass, "get");
                                boolean launched = (boolean) XposedHelpers.callMethod(vamInstance, "launchApp", userId, pkg);
                                XposedBridge.log(TAG + " [HomeFragment-q] Manual launch result: " + launched);
                                param.setResult(null);
                            }
                        }
                    });
            XposedBridge.log(TAG + " [HomeFragment-q] Hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [HomeFragment-q] Hooking failed: " + t.getMessage());
        }

        // Hook HomeFragment.r0
        try {
            XposedHelpers.findAndHookMethod(
                    "com.loc.va.ui.activity.HomeFragment",
                    classLoader,
                    "r0",
                    View.class,
                    int.class,
                    "com.loc.va.model.AppData",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            Object appData = param.args[2];
                            XposedBridge.log(TAG + " [HomeFragment-r0] Intercepted. AppData: " + appData);
                            if (appData != null) {
                                String pkg = (String) XposedHelpers.callMethod(appData, "g");
                                int userId = (int) XposedHelpers.callMethod(appData, "h");
                                XposedBridge.log(TAG + " [HomeFragment-r0] Manually launching userId=" + userId + ", pkg=" + pkg);
                                
                                Class<?> vamClass = classLoader.loadClass("com.lody.virtual.client.ipc.VActivityManager");
                                Object vamInstance = XposedHelpers.callStaticMethod(vamClass, "get");
                                boolean launched = (boolean) XposedHelpers.callMethod(vamInstance, "launchApp", userId, pkg);
                                XposedBridge.log(TAG + " [HomeFragment-r0] Manual launch result: " + launched);
                                param.setResult(null);
                            }
                        }
                    });
            XposedBridge.log(TAG + " [HomeFragment-r0] Hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [HomeFragment-r0] Hooking failed: " + t.getMessage());
        }

        // Hook HomeFragment.s0
        try {
            XposedHelpers.findAndHookMethod(
                    "com.loc.va.ui.activity.HomeFragment",
                    classLoader,
                    "s0",
                    View.class,
                    int.class,
                    "com.loc.va.model.AppData",
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) throws Throwable {
                            Object appData = param.args[2];
                            XposedBridge.log(TAG + " [HomeFragment-s0] Intercepted. AppData: " + appData);
                            if (appData != null) {
                                String pkg = (String) XposedHelpers.callMethod(appData, "g");
                                int userId = (int) XposedHelpers.callMethod(appData, "h");
                                XposedBridge.log(TAG + " [HomeFragment-s0] Manually launching userId=" + userId + ", pkg=" + pkg);
                                
                                Class<?> vamClass = classLoader.loadClass("com.lody.virtual.client.ipc.VActivityManager");
                                Object vamInstance = XposedHelpers.callStaticMethod(vamClass, "get");
                                boolean launched = (boolean) XposedHelpers.callMethod(vamInstance, "launchApp", userId, pkg);
                                XposedBridge.log(TAG + " [HomeFragment-s0] Manual launch result: " + launched);
                                param.setResult(null);
                            }
                        }
                    });
            XposedBridge.log(TAG + " [HomeFragment-s0] Hook registered successfully.");
        } catch (Throwable t) {
            XposedBridge.log(TAG + " [HomeFragment-s0] Hooking failed: " + t.getMessage());
        }
    }
}
