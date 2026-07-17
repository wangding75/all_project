package com.custom.spoofer.xposed;

import android.location.Location;
import android.net.wifi.WifiInfo;
import android.provider.Settings;
import android.telephony.TelephonyManager;

import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage.LoadPackageParam;

/**
 * LSPosed 模块入口类
 *
 * <p>负责按包名过滤后，分发各功能 Hook 的安装工作：
 * <ul>
 *   <li>{@link ActivationBypassHook} - 激活/授权验证绕过（三层防御）</li>
 *   <li>内联 Mock 定位 Hook - 伪造 GPS 经纬度</li>
 *   <li>内联设备指纹 Hook - 伪造 IMEI / Android ID</li>
 *   <li>内联 WiFi 伪装 Hook - 伪造 BSSID/MAC</li>
 * </ul>
 */
public class SpooferModule implements IXposedHookLoadPackage {

    /** 目标 App 的 Manifest 包名（加固壳外层包名）。 */
    private static final String TARGET_PACKAGE = "com.xin.h6";

    @Override
    public void handleLoadPackage(LoadPackageParam lpparam) throws Throwable {
        if (!lpparam.packageName.equals(TARGET_PACKAGE)) {
            return;
        }

        XposedBridge.log("[SpooferModule] Injected into: " + lpparam.packageName);

        /* =======================================================
         * 1. 激活验证绕过 (Activation Bypass)
         *    委托给专用类，三层防御策略，详见 ActivationBypassHook.java
         * ======================================================= */
        ActivationBypassHook.install(lpparam);

        /* =======================================================
         * 2. Mock Location Hook (虚拟定位 API 劫持)
         * ======================================================= */
        XposedHelpers.findAndHookMethod(Location.class, "getLatitude", new XC_MethodHook() {
            @Override
            protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                param.setResult(22.543099); // 伪造纬度（深圳）
            }
        });

        XposedHelpers.findAndHookMethod(Location.class, "getLongitude", new XC_MethodHook() {
            @Override
            protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                param.setResult(113.929884); // 伪造经度（深圳）
            }
        });

        /* =======================================================
         * 3. Device Info Hook (设备指纹参数伪装)
         * ======================================================= */
        XposedHelpers.findAndHookMethod(TelephonyManager.class, "getDeviceId", new XC_MethodHook() {
            @Override
            protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                param.setResult("868888888888888"); // 伪造 IMEI
            }
        });

        XposedHelpers.findAndHookMethod(
                Settings.Secure.class,
                "getString",
                android.content.ContentResolver.class,
                String.class,
                new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                        String key = (String) param.args[1];
                        if (Settings.Secure.ANDROID_ID.equals(key)) {
                            param.setResult("1234567890abcdef"); // 伪造 Android ID
                        }
                    }
                });

        /* =======================================================
         * 4. WiFi Spoofing Hook (无线网络 MAC 伪装)
         * ======================================================= */
        XposedHelpers.findAndHookMethod(WifiInfo.class, "getBSSID", new XC_MethodHook() {
            @Override
            protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                param.setResult("00:11:22:33:44:55"); // 伪造 WiFi BSSID/MAC
            }
        });

        XposedBridge.log("[SpooferModule] All hooks installed successfully.");
    }
}
