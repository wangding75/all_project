package com.sx.app.sandbox.spoof.hook;

import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.SystemClock;
import android.util.Log;

import com.sx.app.data.LocationConfig;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XC_MethodHook.MethodHookParam;
import de.robv.android.xposed.XposedHelpers;

public class LocationHook {

    private static final String TAG = "SX-LocationHook";
    private static LocationConfig sConfig;

    public static void install(ClassLoader classLoader, LocationConfig config) {
        if (config == null || !config.enabled) return;
        sConfig = config;
        try {
            XposedHelpers.findAndHookMethod(Location.class, "getLatitude", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled) {
                        param.setResult(sConfig.latitude + getDrift());
                    }
                }
            });

            XposedHelpers.findAndHookMethod(Location.class, "getLongitude", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled) {
                        param.setResult(sConfig.longitude + getDrift());
                    }
                }
            });

            XposedHelpers.findAndHookMethod(Location.class, "getAltitude", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled) {
                        param.setResult(sConfig.altitude);
                    }
                }
            });

            XposedHelpers.findAndHookMethod(Location.class, "getAccuracy", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled) {
                        param.setResult(sConfig.accuracy);
                    }
                }
            });

            XposedHelpers.findAndHookMethod(Location.class, "getTime", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled) {
                        param.setResult(System.currentTimeMillis());
                    }
                }
            });

            XposedHelpers.findAndHookMethod(Location.class, "getElapsedRealtimeNanos", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled) {
                        param.setResult(SystemClock.elapsedRealtimeNanos());
                    }
                }
            });

            // Anti-Mock (D-04)
            XposedHelpers.findAndHookMethod(Location.class, "isFromMockProvider", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled && sConfig.antiMockDetect) {
                        param.setResult(false);
                    }
                }
            });

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                try {
                    XposedHelpers.findAndHookMethod(Location.class, "isMock", new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (sConfig != null && sConfig.enabled && sConfig.antiMockDetect) {
                                param.setResult(false);
                            }
                        }
                    });
                } catch (Throwable ignored) {}
            }

            // LocationManager getLastKnownLocation
            XposedHelpers.findAndHookMethod(LocationManager.class, "getLastKnownLocation", String.class, new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled) {
                        String provider = (String) param.args[0];
                        param.setResult(createFakeLocation(provider));
                    }
                }
            });

            Log.d(TAG, "LocationHook installed successfully.");
        } catch (Throwable e) {
            Log.e(TAG, "Failed to install LocationHook", e);
        }
    }

    private static Location createFakeLocation(String provider) {
        Location loc = new Location(provider != null ? provider : LocationManager.GPS_PROVIDER);
        loc.setLatitude(sConfig.latitude + getDrift());
        loc.setLongitude(sConfig.longitude + getDrift());
        loc.setAltitude(sConfig.altitude);
        loc.setAccuracy(sConfig.accuracy);
        loc.setTime(System.currentTimeMillis());
        loc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
        return loc;
    }

    private static double getDrift() {
        if (sConfig != null && sConfig.microDrift) {
            return (Math.random() - 0.5) * 0.00002;
        }
        return 0.0;
    }
}
