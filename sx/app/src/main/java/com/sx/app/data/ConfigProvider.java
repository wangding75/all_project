package com.sx.app.data;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Binder;
import android.os.Bundle;
import android.os.Process;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.io.File;

/**
 * Host ContentProvider for configuration sharing with sandbox virtual clients.
 * Authority: ${applicationId}.config.provider
 *
 * Access policy: same UID (host + BlackBox virtual processes) or matching signing cert.
 * Package-name prefix allowlist removed intentionally.
 */
public class ConfigProvider extends ContentProvider {

    private static final String TAG = "SX-ConfigProvider";
    private static final long MAX_CAMERA_BYTES = 8L * 1024 * 1024; // 8 MiB Binder-safe cap

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
        // Same UID covers host + BlackBox virtual client processes for this app.
        if (callingUid == myUid) {
            return true;
        }
        // Do not allow root/system UIDs in production surface.
        Context ctx = getContext();
        if (ctx == null) {
            return false;
        }
        String myPkg = ctx.getPackageName();
        String[] callingPackages = ctx.getPackageManager().getPackagesForUid(callingUid);
        if (callingPackages != null) {
            for (String pkg : callingPackages) {
                if (pkg != null && pkg.equals(myPkg)) {
                    return true;
                }
                try {
                    if (ctx.getPackageManager().checkSignatures(myPkg, pkg)
                            == PackageManager.SIGNATURE_MATCH) {
                        return true;
                    }
                } catch (Exception ignored) {
                }
            }
        }
        Log.w(TAG, "Denied access to caller UID: " + callingUid);
        return false;
    }

    private static boolean isPathUnderRoot(String targetCanonical, String rootCanonical) {
        if (targetCanonical == null || rootCanonical == null) {
            return false;
        }
        return targetCanonical.equals(rootCanonical)
                || targetCanonical.startsWith(rootCanonical + File.separator);
    }

    @Nullable
    @Override
    public Bundle call(@NonNull String method, @Nullable String arg, @Nullable Bundle extras) {
        if (!isCallerAllowed()) {
            throw new SecurityException("Unauthorized caller for ConfigProvider");
        }
        Context context = getContext();
        if (context == null) {
            return null;
        }

        Bundle result = new Bundle();

        if (METHOD_GET_CONFIG.equals(method)) {
            String baseKey = arg;
            if (baseKey == null) {
                return result;
            }

            String pkg = extras != null ? extras.getString(EXTRA_PKG, null) : null;
            int userId = extras != null ? extras.getInt(EXTRA_USER_ID, 0) : 0;

            String fullKey = SxPrefs.makeKey(baseKey, pkg, userId);
            String jsonStr = SxPrefs.get(context).getString(fullKey, "");

            if ((jsonStr == null || jsonStr.isEmpty()) && pkg != null && !pkg.isEmpty()) {
                jsonStr = SxPrefs.get(context).getString(baseKey, "");
            }

            result.putString(EXTRA_JSON, jsonStr == null ? "" : jsonStr);
            return result;
        } else if (METHOD_PUT_CONFIG.equals(method)) {
            String baseKey = arg;
            if (baseKey == null || extras == null) {
                return result;
            }

            String pkg = extras.getString(EXTRA_PKG, null);
            int userId = extras.getInt(EXTRA_USER_ID, 0);
            String jsonStr = extras.getString(EXTRA_JSON, "");

            String fullKey = SxPrefs.makeKey(baseKey, pkg, userId);
            SxPrefs.get(context).edit().putString(fullKey, jsonStr).apply();
            result.putBoolean("success", true);

            ConfigBroadcast.notifyChanged(context, pkg, userId);
            return result;
        } else if ("get_camera_bytes".equals(method)) {
            String path = extras != null ? extras.getString("path", "") : "";
            if (path != null && !path.isEmpty()) {
                try {
                    File file = new File(path);
                    String targetCanonical = file.getCanonicalPath();

                    File[] allowedRoots = new File[]{
                            context.getExternalFilesDir("camera"),
                            new File(context.getFilesDir(), "camera"),
                            // Only camera subdir under cache, not entire cache tree
                            new File(context.getExternalCacheDir(), "camera"),
                            new File(context.getCacheDir(), "camera")
                    };

                    boolean allowed = false;
                    for (File root : allowedRoots) {
                        if (root != null) {
                            // Ensure camera root exists conceptually for prefix check
                            String rootCanonical = root.getCanonicalPath();
                            if (isPathUnderRoot(targetCanonical, rootCanonical)) {
                                allowed = true;
                                break;
                            }
                        }
                    }

                    if (allowed && file.exists() && file.canRead() && file.isFile()) {
                        long len = file.length();
                        if (len <= 0 || len > MAX_CAMERA_BYTES) {
                            Log.w(TAG, "Rejected camera file size=" + len + " path=" + path);
                        } else {
                            try (java.io.FileInputStream fis = new java.io.FileInputStream(file);
                                 java.io.ByteArrayOutputStream baos =
                                         new java.io.ByteArrayOutputStream((int) len)) {
                                byte[] buf = new byte[8192];
                                int n;
                                long total = 0;
                                while ((n = fis.read(buf)) != -1) {
                                    total += n;
                                    if (total > MAX_CAMERA_BYTES) {
                                        Log.w(TAG, "Camera read exceeded cap");
                                        return result;
                                    }
                                    baos.write(buf, 0, n);
                                }
                                result.putByteArray("camera_bytes", baos.toByteArray());
                            }
                        }
                    } else {
                        Log.w(TAG, "Denied get_camera_bytes for path outside whitelist: " + path);
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error reading camera bytes", e);
                }
            }
            return result;
        }

        return super.call(method, arg, extras);
    }

    @Nullable
    @Override
    public Cursor query(@NonNull Uri uri, @Nullable String[] projection, @Nullable String selection,
                        @Nullable String[] selectionArgs, @Nullable String sortOrder) {
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
    public int update(@NonNull Uri uri, @Nullable ContentValues values, @Nullable String selection,
                      @Nullable String[] selectionArgs) {
        if (!isCallerAllowed()) {
            throw new SecurityException("Unauthorized caller for ConfigProvider");
        }
        return 0;
    }
}
