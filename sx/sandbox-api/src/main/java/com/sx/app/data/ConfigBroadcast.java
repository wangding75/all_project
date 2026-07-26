package com.sx.app.data;

import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Notify host + virtual client processes that spoof config changed.
 * Mirrors ConfigProvider put_config broadcast behavior (bound + unbound).
 */
public final class ConfigBroadcast {

    private static final String TAG = "SX-ConfigBroadcast";
    public static final String EXTRA_PKG = "package_name";
    public static final String EXTRA_USER_ID = "user_id";

    private ConfigBroadcast() {}

    public static String actionName(String hostPkg) {
        return hostPkg + ".action.UPDATE_CONFIG";
    }

    public static void notifyChanged(Context context, String pkg, int userId) {
        if (context == null) {
            return;
        }
        try {
            String hostPkg = resolveHostPkg(context);
            String action = actionName(hostPkg);

            Intent bound = new Intent(action);
            bound.setPackage(hostPkg);
            bound.putExtra(EXTRA_PKG, pkg);
            bound.putExtra(EXTRA_USER_ID, userId);
            context.sendBroadcast(bound);

            Intent unbound = new Intent(action);
            unbound.putExtra(EXTRA_PKG, pkg);
            unbound.putExtra(EXTRA_USER_ID, userId);
            context.sendBroadcast(unbound);
        } catch (Exception e) {
            Log.w(TAG, "notifyChanged failed", e);
        }
    }

    private static String resolveHostPkg(Context context) {
        try {
            Class<?> bbCore = Class.forName("top.niunaijun.blackbox.BlackBoxCore");
            Object pkg = bbCore.getMethod("getHostPkg").invoke(null);
            if (pkg instanceof String && !((String) pkg).isEmpty()) {
                return (String) pkg;
            }
        } catch (Throwable ignored) {
        }
        return context.getPackageName();
    }
}
