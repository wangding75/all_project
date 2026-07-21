package com.sx.app.sandbox.spoof.hook;

import android.telephony.CellLocation;
import android.telephony.TelephonyManager;
import android.telephony.gsm.GsmCellLocation;
import android.util.Log;

import com.sx.app.data.NetworkProfile;

import java.util.Collections;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XC_MethodHook.MethodHookParam;
import de.robv.android.xposed.XposedHelpers;

public class CellHook {

    private static final String TAG = "SX-CellHook";

    public static void install(ClassLoader classLoader, NetworkProfile profile) {
        if (profile == null || !profile.enabled) return;
        try {
            XposedHelpers.findAndHookMethod(TelephonyManager.class, "getAllCellInfo", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    param.setResult(Collections.emptyList());
                }
            });

            XposedHelpers.findAndHookMethod(TelephonyManager.class, "getCellLocation", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    GsmCellLocation loc = new GsmCellLocation();
                    loc.setLacAndCid(profile.lac, profile.cid);
                    param.setResult(loc);
                }
            });

            Log.d(TAG, "CellHook installed successfully.");
        } catch (Throwable e) {
            Log.e(TAG, "Failed to install CellHook", e);
        }
    }
}
