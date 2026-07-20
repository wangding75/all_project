package com.sx.app.data;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Central preferences store.
 * World-readable flag is required so LSPosed module (different process) can read configs
 * via {@code XSharedPreferences} when the host app is selected as module scope source.
 */
public final class SxPrefs {

    public static final String PREFS_NAME = "sx_config";
    public static final String KEY_LOCATION = "location";
    public static final String KEY_DEVICE = "device";
    public static final String KEY_NETWORK = "network";
    public static final String KEY_CAMERA = "camera";
    public static final String KEY_SANDBOX_APPS = "sandbox_apps";
    public static final String KEY_LICENSE = "license";
    public static final String KEY_TIME_GUARD = "time_guard";

    private SxPrefs() {}

    @SuppressWarnings("deprecation")
    public static SharedPreferences get(Context context) {
        // MODE_WORLD_READABLE allows XSharedPreferences to read from LSPosed
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_WORLD_READABLE);
    }

    public static SharedPreferences getPrivate(Context context) {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
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
