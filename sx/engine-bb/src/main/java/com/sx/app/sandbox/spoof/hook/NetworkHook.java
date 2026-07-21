package com.sx.app.sandbox.spoof.hook;

import android.net.wifi.ScanResult;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.util.Log;

import com.sx.app.data.NetworkProfile;

import java.util.ArrayList;
import java.util.List;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XC_MethodHook.MethodHookParam;
import de.robv.android.xposed.XposedHelpers;

public class NetworkHook {

    private static final String TAG = "SX-NetworkHook";

    public static void install(ClassLoader classLoader, NetworkProfile profile) {
        if (profile == null || !profile.enabled) return;
        try {
            XposedHelpers.findAndHookMethod(WifiInfo.class, "getSSID", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (profile.ssid != null) {
                        String s = profile.ssid;
                        if (!s.startsWith("\"")) {
                            s = "\"" + s + "\"";
                        }
                        param.setResult(s);
                    }
                }
            });

            XposedHelpers.findAndHookMethod(WifiInfo.class, "getBSSID", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (profile.bssid != null) {
                        param.setResult(profile.bssid);
                    }
                }
            });

            XposedHelpers.findAndHookMethod(WifiInfo.class, "getMacAddress", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (profile.mac != null) {
                        param.setResult(profile.mac);
                    }
                }
            });

            XposedHelpers.findAndHookMethod(WifiManager.class, "getScanResults", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (profile.scanList != null && !profile.scanList.isEmpty()) {
                        try {
                            List<ScanResult> list = new ArrayList<>();
                            for (NetworkProfile.ScanAp ap : profile.scanList) {
                                try {
                                    ScanResult sr = new ScanResult();
                                    sr.SSID = ap.ssid;
                                    sr.BSSID = ap.bssid;
                                    sr.level = ap.level;
                                    list.add(sr);
                                } catch (Throwable innerEx) {
                                    Log.w(TAG, "Failed to instantiate single ScanResult", innerEx);
                                }
                            }
                            if (!list.isEmpty()) {
                                param.setResult(list);
                            }
                        } catch (Throwable t) {
                            Log.w(TAG, "Failed to construct fake ScanResult list", t);
                        }
                    }
                }
            });

            Log.d(TAG, "NetworkHook installed successfully.");
        } catch (Throwable e) {
            Log.e(TAG, "Failed to install NetworkHook", e);
        }
    }
}
