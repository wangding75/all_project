/**
 * ActivationBypass Frida Hook Script v3
 * 目标: com.xin.h6 (星盒) - 360加固
 *
 * 基于 src_restore 真实逆向结论：
 *
 * 【激活判断链】（来自 SplashActivity.checkLoginStatus）
 *   SharedPreferences["user_info"]["token"] != null → 已激活 → HomeActivity
 *   否则 → ActiveCardActivity
 *
 * 【CORE 配置】（来自 MyUtil.java 真实代码）
 *   getConfig(ctx, "CORE") → SharedPreferences["DEFAULT"]["CORE"] → Base64(JSON)
 *   getConfig2(ctx, key)   → decode(CORE) → JSON.getString(key)
 *
 * 【Xposed 检测】（来自 SplashActivity.isXposedInstalled）
 *   遍历调用栈，检查是否含 "de.robv.android.xposed" → 有则 finish()
 *
 * 【注入方式】
 *   由于 360 壳检测 spawn 注入，必须在 App 启动后通过 PID attach 注入
 *   使用: frida -U -p <PID> -l activation_bypass.js
 *
 * 【Hook 策略】
 *   Layer-0: Hook Exception.getStackTrace() → 屏蔽 Xposed 检测
 *   Layer-1: Hook MyUtil.getConfig(CORE)    → 注入伪造激活 JSON
 *   Layer-2: Hook MyUtil.getConfig2(key)    → 注入激活子字段
 *   Layer-3: Hook Activity.startActivity    → 重定向 ActiveCardActivity
 *   Layer-4: 直接写入 token 到 SharedPreferences["user_info"]
 */

"use strict";

const TAG = "[ActivationBypass]";

// 激活数据（与 MyUtil.java 中 Base64(JSON) 格式完全一致）
const FAKE_CORE_BASE64 =
    "eyJ2aXAiOiIxIiwiYWN0aXZlIjoiMSIsInN0YXR1cyI6IjEiLCJhdXRoIjoiMSIsImV4cGlyZSI6" +
    "IjIwOTktMTItMzEgMjM6NTk6NTkiLCJleHBpcmVfdGltZSI6IjQwOTk4OTg4MDAwMDAiLCJleHBp" +
    "cmVUaW1lIjoiNDA5OTg5ODgwMDAwMCIsInRpbWUiOiI0MDk5ODk4ODAwMDAwIiwiZGF5IjoiOTk5" +
    "OTkiLCJjb2RlIjoiYWN0aXZhdGVkIn0=";

const FAKE_TOKEN = "bypass_activated_token_" + Date.now();

const ACTIVATION_KEYS = ["vip","active","status","auth","expire","expire_time","expireTime","time","day","code"];
const FAKE_CONFIG = {
    vip:"1", active:"1", status:"1", auth:"1",
    expire:"2099-12-31 23:59:59",
    expire_time:"4099898800000", expireTime:"4099898800000",
    time:"4099898800000", day:"99999", code:"activated"
};

const ACTIVE_CARD_CLASS = "com.loc.va.ui.activity.ActiveCardActivity";
const HOME_CLASS        = "com.loc.va.ui.activity.HomeActivity";
const MYUTIL_CLASS      = "com.loc.va.utils.MyUtil";

function log(msg) { console.log(TAG + " " + msg); }

setTimeout(function () {
    Java.perform(function () {
        log("=== v3 Hook Script Active (attach mode) ===");

    // ─────────────────────────────────────────────────────────
    // Layer-0: 绕过 Xposed 检测
    // SplashActivity.isXposedInstalled() 通过检查调用栈
    // 含 "de.robv.android.xposed" 来判断，Hook StackTraceElement.getClassName
    // ─────────────────────────────────────────────────────────
    hookXposedDetection();

    // ─────────────────────────────────────────────────────────
    // Layer-1 & 2: Hook MyUtil.getConfig / getConfig2
    // 在 attach 模式下，360 壳已解壳，类可以直接访问
    // ─────────────────────────────────────────────────────────
    hookGetConfig();
    hookGetConfig2();

    // ─────────────────────────────────────────────────────────
    // Layer-3: startActivity 重定向
    // ─────────────────────────────────────────────────────────
    hookStartActivity();

    // ─────────────────────────────────────────────────────────
    // Layer-4: 直接向 SharedPreferences["user_info"] 写入 token
    // 这是最直接的方式，让 checkLoginStatus() 返回 true
    // ─────────────────────────────────────────────────────────
    injectTokenIntoSharedPrefs();
    hookSharedPreferences();
    hookActiveCardRedirection();

    });
}, 500);

// ─────────────────────────────────────────────────────────────
// Layer-0: 屏蔽 Xposed 调用栈检测
// ─────────────────────────────────────────────────────────────
function hookXposedDetection() {
    try {
        var StackTraceElement = Java.use("java.lang.StackTraceElement");
        StackTraceElement.getClassName.implementation = function () {
            var name = this.getClassName();
            // 将 Xposed 包名替换为无害字符串
            if (name && name.indexOf("de.robv.android.xposed") !== -1) {
                log("[Layer-0] Xposed class name masked: " + name);
                return "android.app.Activity";
            }
            return name;
        };
        log("[Layer-0] Xposed detection hook OK ✅");
    } catch (e) {
        log("[Layer-0] FAILED: " + e);
    }
}

// ─────────────────────────────────────────────────────────────
// Layer-1: Hook MyUtil.getConfig
// 真实实现: context.getSharedPreferences("DEFAULT",0).getString(key,"")
// ─────────────────────────────────────────────────────────────
function hookGetConfig() {
    try {
        var MyUtil = Java.use(MYUTIL_CLASS);
        MyUtil.getConfig.overload("android.content.Context", "java.lang.String")
            .implementation = function (ctx, key) {
                var original = this.getConfig(ctx, key);
                var k = String(key);
                if (k === "CORE") {
                    log("[Layer-1] getConfig(CORE) → inject fake Base64 config");
                    return FAKE_CORE_BASE64;
                }
                log("[Layer-1] getConfig(" + k + ") = " + original);
                return original;
            };
        log("[Layer-1] getConfig hook OK ✅");
    } catch (e) {
        log("[Layer-1] getConfig FAILED: " + e.message);
    }
}

// ─────────────────────────────────────────────────────────────
// Layer-2: Hook MyUtil.getConfig2
// 真实实现: getConfig(ctx,"CORE") → b_dec() → JSONObject.getString(subKey)
// ─────────────────────────────────────────────────────────────
function hookGetConfig2() {
    try {
        var MyUtil = Java.use(MYUTIL_CLASS);
        MyUtil.getConfig2.overload("android.content.Context", "java.lang.String")
            .implementation = function (ctx, subKey) {
                var original = this.getConfig2(ctx, subKey);
                var k = String(subKey);
                if (ACTIVATION_KEYS.indexOf(k) !== -1) {
                    var fakeVal = FAKE_CONFIG[k] || "1";
                    log("[Layer-2] getConfig2(" + k + ") → [" + fakeVal + "] (was: " + original + ")");
                    return fakeVal;
                }
                log("[Layer-2] getConfig2(" + k + ") = " + original);
                return original;
            };
        log("[Layer-2] getConfig2 hook OK ✅");
    } catch (e) {
        log("[Layer-2] getConfig2 FAILED: " + e.message);
    }
}

// ─────────────────────────────────────────────────────────────
// Layer-3: startActivity 重定向
// ─────────────────────────────────────────────────────────────
function hookStartActivity() {
    try {
        var Activity = Java.use("android.app.Activity");
        Activity.startActivity.overload("android.content.Intent")
            .implementation = function (intent) {
                if (intent !== null && intent.getComponent() !== null) {
                    var cls = String(intent.getComponent().getClassName());
                    if (cls === ACTIVE_CARD_CLASS) {
                        var pkg = String(intent.getComponent().getPackageName());
                        log("[Layer-3] ActiveCardActivity → HomeActivity ✅");
                        intent.setClassName(pkg, HOME_CLASS);
                    }
                }
                return this.startActivity(intent);
            };
        log("[Layer-3] startActivity redirect hook OK ✅");
    } catch (e) {
        log("[Layer-3] startActivity FAILED: " + e);
    }
}

// ─────────────────────────────────────────────────────────────
// Layer-4: 直接注入 token 到 SharedPreferences["user_info"]
// 让 checkLoginStatus() 直接返回 true
// ─────────────────────────────────────────────────────────────
function injectTokenIntoSharedPrefs() {
    try {
        // 通过 Context 获取 SP 并写入 token
        Java.choose("android.app.Application", {
            onMatch: function (app) {
                var context = app.getApplicationContext();

                // 写入 user_info SP（激活状态 token）
                var spUserInfo = context.getSharedPreferences("user_info", 0);
                var editorUserInfo = spUserInfo.edit();
                editorUserInfo.putString("token", FAKE_TOKEN);
                editorUserInfo.apply();
                log("[Layer-4] Written token to SharedPreferences[user_info] ✅");

                // 同时写入 DEFAULT SP 的 CORE 字段（双重保险）
                var spDefault = context.getSharedPreferences("DEFAULT", 0);
                var editorDefault = spDefault.edit();
                editorDefault.putString("CORE", FAKE_CORE_BASE64);
                editorDefault.apply();
                log("[Layer-4] Written CORE to SharedPreferences[DEFAULT] ✅");

                return "stop";
            },
            onComplete: function () {}
        });
    } catch (e) {
        log("[Layer-4] SP injection FAILED: " + e);
    }
} // 闭合 injectTokenIntoSharedPrefs

// ─────────────────────────────────────────────────────────────
// 动态 SharedPreferences Hook (兜底物理配置文件失效)
// ─────────────────────────────────────────────────────────────
function hookSharedPreferences() {
    try {
        var SharedPreferencesImpl = Java.use("android.app.SharedPreferencesImpl");

        // 拦截 getString
        SharedPreferencesImpl.getString.overload("java.lang.String", "java.lang.String").implementation = function (key, defValue) {
            var k = String(key);
            if (k === "token") {
                log("[SP-Hook] getString(token) → injected FAKE_TOKEN ✅");
                return FAKE_TOKEN;
            }
            if (k === "CORE") {
                log("[SP-Hook] getString(CORE) → injected FAKE_CORE_BASE64 ✅");
                return FAKE_CORE_BASE64;
            }
            if (ACTIVATION_KEYS.indexOf(k) !== -1) {
                var fakeVal = FAKE_CONFIG[k] || "1";
                log("[SP-Hook] getString(" + k + ") → injected " + fakeVal + " ✅");
                return fakeVal;
            }
            return this.getString(key, defValue);
        };

        // 拦截 getBoolean
        SharedPreferencesImpl.getBoolean.overload("java.lang.String", "boolean").implementation = function (key, defValue) {
            var k = String(key);
            if (k === "active" || k === "vip" || k === "auth" || k === "status") {
                log("[SP-Hook] getBoolean(" + k + ") → forced true ✅");
                return true;
            }
            return this.getBoolean(key, defValue);
        };

        log("[SP-Hook] Dynamic SharedPreferences hook registered OK ✅");
    } catch (e) {
        log("[SP-Hook] FAILED: " + e);
    }
}

// ─────────────────────────────────────────────────────────────
// 动态 ActiveCardActivity 重定向 (保底 UI 交互)
// ─────────────────────────────────────────────────────────────
function hookActiveCardRedirection() {
    try {
        var Activity = Java.use("android.app.Activity");
        Activity.onResume.implementation = function () {
            var className = this.getClass().getName();
            if (className === ACTIVE_CARD_CLASS) {
                log("[UI-Hook] Detected ActiveCardActivity.onResume! Redirecting to HomeActivity...");
                var context = this;
                var Intent = Java.use("android.content.Intent");
                var HomeActivityClass = Java.use("com.loc.va.ui.activity.HomeActivity").class;
                var targetIntent = Intent.$new(context, HomeActivityClass);
                context.startActivity(targetIntent);
                context.finish();
            }
            this.onResume();
        };
        log("[UI-Hook] Global Activity.onResume hook registered OK ✅");
    } catch (e) {
        log("[UI-Hook] FAILED: " + e);
    }
}
