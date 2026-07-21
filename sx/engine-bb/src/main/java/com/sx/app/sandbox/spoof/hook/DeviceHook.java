package com.sx.app.sandbox.spoof.hook;

import android.content.ContentResolver;
import android.os.Build;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.util.Log;

import com.sx.app.data.DeviceProfile;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XC_MethodHook.MethodHookParam;
import de.robv.android.xposed.XposedHelpers;

public class DeviceHook {

    private static final String TAG = "SX-DeviceHook";

    public static void install(ClassLoader classLoader, DeviceProfile profile) {
        if (profile == null || !profile.enabled) return;
        try {
            setBuildField("BRAND", profile.brand);
            setBuildField("MODEL", profile.model);
            setBuildField("MANUFACTURER", profile.manufacturer);
            setBuildField("BOARD", profile.board);
            setBuildField("SERIAL", profile.serial);
            setBuildField("HARDWARE", profile.board);

            try {
                XposedHelpers.findAndHookMethod(Build.class, "getSerial", new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) {
                        param.setResult(profile.serial);
                    }
                });
            } catch (Throwable ignored) {}

            hookTelephony(TelephonyManager.class, "getDeviceId", profile.imei);
            hookTelephony(TelephonyManager.class, "getImei", profile.imei);
            hookTelephony(TelephonyManager.class, "getMeid", profile.meid);
            hookTelephony(TelephonyManager.class, "getSubscriberId", profile.imsi);
            hookTelephony(TelephonyManager.class, "getSimSerialNumber", profile.iccid);
            hookTelephony(TelephonyManager.class, "getLine1Number", profile.phoneNumber);
            hookTelephony(TelephonyManager.class, "getNetworkOperatorName", profile.operatorName);
            hookTelephony(TelephonyManager.class, "getSimOperatorName", profile.operatorName);

            XposedHelpers.findAndHookMethod(Settings.Secure.class, "getString", ContentResolver.class, String.class, new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    String name = (String) param.args[1];
                    if (Settings.Secure.ANDROID_ID.equals(name)) {
                        if (profile.androidId != null && !profile.androidId.isEmpty()) {
                            param.setResult(profile.androidId);
                        }
                    }
                }
            });

            Log.d(TAG, "DeviceHook installed successfully.");
        } catch (Throwable e) {
            Log.e(TAG, "Failed to install DeviceHook", e);
        }
    }

    private static void setBuildField(String fieldName, String value) {
        if (value == null) return;
        try {
            XposedHelpers.setStaticObjectField(Build.class, fieldName, value);
        } catch (Throwable ignored) {}
    }

    private static void hookTelephony(Class<?> clazz, String methodName, String returnValue) {
        if (returnValue == null || returnValue.isEmpty()) return;
        try {
            XposedHelpers.findAndHookMethod(clazz, methodName, new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    param.setResult(returnValue);
                }
            });
            XposedHelpers.findAndHookMethod(clazz, methodName, int.class, new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    param.setResult(returnValue);
                }
            });
        } catch (Throwable ignored) {}
    }
}
