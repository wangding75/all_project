package com.sx.app.data;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Binder;
import android.os.Bundle;
import android.os.Process;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

/**
 * Host ContentProvider for configuration sharing.
 * Scoped by authority: ${applicationId}.config.provider
 */
public class ConfigProvider extends ContentProvider {

    private static final String TAG = "SX-ConfigProvider";

    public static final String METHOD_GET_CONFIG = "get_config";
    public static final String METHOD_PUT_CONFIG = "put_config";

    public static final String EXTRA_PKG = "package_name";
    public static final String EXTRA_USER_ID = "user_id";
    public static final String EXTRA_JSON = "config_json";

    @Override
    public boolean onCreate() {
        Log.d(TAG, "ConfigProvider initialized.");
        return true;
    }

    private boolean isCallerAllowed() {
        int callingUid = Binder.getCallingUid();
        int myUid = Process.myUid();
        if (callingUid == myUid || callingUid == 0 || callingUid == 1000) {
            return true;
        }
        Context ctx = getContext();
        if (ctx == null) return false;
        String myPkg = ctx.getPackageName();
        String[] callingPackages = ctx.getPackageManager().getPackagesForUid(callingUid);
        if (callingPackages != null) {
            for (String pkg : callingPackages) {
                if (pkg.equals(myPkg) || pkg.startsWith("com.sx.app")) {
                    return true;
                }
                try {
                    if (ctx.getPackageManager().checkSignatures(myPkg, pkg) == android.content.pm.PackageManager.SIGNATURE_MATCH) {
                        return true;
                    }
                } catch (Exception ignored) {}
            }
        }
        Log.w(TAG, "Denied access to caller UID: " + callingUid);
        return false;
    }

    @Nullable
    @Override
    public Bundle call(@NonNull String method, @Nullable String arg, @Nullable Bundle extras) {
        if (!isCallerAllowed()) {
            throw new SecurityException("Unauthorized caller for ConfigProvider");
        }
        Context context = getContext();
        if (context == null) return null;

        Bundle result = new Bundle();

        if (METHOD_GET_CONFIG.equals(method)) {
            String baseKey = arg;
            if (baseKey == null) return result;

            String pkg = extras != null ? extras.getString(EXTRA_PKG, null) : null;
            int userId = extras != null ? extras.getInt(EXTRA_USER_ID, 0) : 0;

            String fullKey = SxPrefs.makeKey(baseKey, pkg, userId);
            String jsonStr = SxPrefs.get(context).getString(fullKey, "");

            // Fallback to global config if instance-specific config is empty
            if ((jsonStr == null || jsonStr.isEmpty()) && pkg != null && !pkg.isEmpty()) {
                jsonStr = SxPrefs.get(context).getString(baseKey, "");
            }

            result.putString(EXTRA_JSON, jsonStr == null ? "" : jsonStr);
            return result;
        } else if (METHOD_PUT_CONFIG.equals(method)) {
            String baseKey = arg;
            if (baseKey == null || extras == null) return result;

            String pkg = extras.getString(EXTRA_PKG, null);
            int userId = extras.getInt(EXTRA_USER_ID, 0);
            String jsonStr = extras.getString(EXTRA_JSON, "");

            String fullKey = SxPrefs.makeKey(baseKey, pkg, userId);
            SxPrefs.get(context).edit().putString(fullKey, jsonStr).apply();
            result.putBoolean("success", true);

            // Send package-bound broadcast (for Host) + unbound broadcast (for virtual client processes) (S1)
            String hostPkg = context.getPackageName();
            Intent boundIntent = new Intent(hostPkg + ".action.UPDATE_CONFIG");
            boundIntent.setPackage(hostPkg);
            boundIntent.putExtra(EXTRA_PKG, pkg);
            boundIntent.putExtra(EXTRA_USER_ID, userId);
            context.sendBroadcast(boundIntent);

            Intent unboundIntent = new Intent(hostPkg + ".action.UPDATE_CONFIG");
            unboundIntent.putExtra(EXTRA_PKG, pkg);
            unboundIntent.putExtra(EXTRA_USER_ID, userId);
            context.sendBroadcast(unboundIntent);

            return result;
        }

        return super.call(method, arg, extras);
    }

    @Nullable
    @Override
    public Cursor query(@NonNull Uri uri, @Nullable String[] projection, @Nullable String selection, @Nullable String[] selectionArgs, @Nullable String sortOrder) {
        if (!isCallerAllowed()) {
            throw new SecurityException("Unauthorized caller for ConfigProvider");
        }
        return null;
    }

    @Nullable
    @Override
    public String getType(@NonNull Uri uri) {
        return null;
    }

    @Nullable
    @Override
    public Uri insert(@NonNull Uri uri, @Nullable ContentValues values) {
        if (!isCallerAllowed()) {
            throw new SecurityException("Unauthorized caller for ConfigProvider");
        }
        return null;
    }

    @Override
    public int delete(@NonNull Uri uri, @Nullable String selection, @Nullable String[] selectionArgs) {
        if (!isCallerAllowed()) {
            throw new SecurityException("Unauthorized caller for ConfigProvider");
        }
        return 0;
    }

    @Override
    public int update(@NonNull Uri uri, @Nullable ContentValues values, @Nullable String selection, @Nullable String[] selectionArgs) {
        if (!isCallerAllowed()) {
            throw new SecurityException("Unauthorized caller for ConfigProvider");
        }
        return 0;
    }
}
