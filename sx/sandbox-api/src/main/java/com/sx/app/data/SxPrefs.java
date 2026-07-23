package com.sx.app.data;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * 闪现配置存储（Phase 2：sandbox-api 迁移版）。
 * 保持 PREFS_NAME = "sx_config", MODE_PRIVATE 兼容性。
 */
public final class SxPrefs {

    public static final String PREFS_NAME = "sx_config";
    public static final String KEY_GLOBAL = "global";

    public static final String KEY_LOCATION = "location";
    public static final String KEY_DEVICE = "device";
    public static final String KEY_NETWORK = "network";
    public static final String KEY_CAMERA = "camera";
    public static final String KEY_BLUETOOTH = "bluetooth";
    public static final String KEY_SANDBOX_APPS = "sandbox_apps";
    public static final String KEY_LICENSE = "license";
    public static final String KEY_TIME_GUARD = "time_guard";

    private SxPrefs() {}

    public static SharedPreferences get(Context context) {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    public static SharedPreferences getPrivate(Context context) {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    public static String makeKey(String baseKey, String pkg, int userId) {
        if (pkg == null || pkg.trim().isEmpty()) {
            return baseKey;
        }
        return baseKey + "_" + pkg.trim() + ":" + userId;
    }

    public static void putJson(Context context, String key, JSONObject obj) {
        get(context).edit().putString(key, obj == null ? "" : obj.toString()).apply();
    }

    public static JSONObject getJson(Context context, String key) {
        String raw = get(context).getString(key, "");
        if (raw == null || raw.isEmpty()) {
            return new JSONObject();
        }
        try {
            return new JSONObject(raw);
        } catch (JSONException e) {
            return new JSONObject();
        }
    }

    public static void putJsonArray(Context context, String key, JSONArray arr) {
        get(context).edit().putString(key, arr == null ? "[]" : arr.toString()).apply();
    }

    public static JSONArray getJsonArray(Context context, String key) {
        String raw = get(context).getString(key, "[]");
        if (raw == null || raw.isEmpty()) {
            return new JSONArray();
        }
        try {
            return new JSONArray(raw);
        } catch (JSONException e) {
            return new JSONArray();
        }
    }
}
