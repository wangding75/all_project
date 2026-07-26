package com.sx.app.data;

import android.content.Context;

import org.json.JSONException;
import org.json.JSONObject;

/** Virtual camera media source configuration. */
public class CameraConfig {

    public static final String TYPE_VIDEO = "video";
    public static final String TYPE_IMAGE = "image";

    public boolean enabled;
    public String sourceType = TYPE_IMAGE;
    public String mediaPath = "";

    public static CameraConfig load(Context context) {
        return load(context, null, 0);
    }

    public static CameraConfig load(Context context, String pkg, int userId) {
        String key = SxPrefs.makeKey(SxPrefs.KEY_CAMERA, pkg, userId);
        return fromJson(SxPrefs.getJson(context, key));
    }

    public void save(Context context) {
        save(context, null, 0);
    }

    public void save(Context context, String pkg, int userId) {
        String key = SxPrefs.makeKey(SxPrefs.KEY_CAMERA, pkg, userId);
        SxPrefs.putJson(context, key, toJson());
        ConfigBroadcast.notifyChanged(context, pkg, userId);
    }

    public JSONObject toJson() {
        JSONObject o = new JSONObject();
        try {
            o.put("enabled", enabled);
            o.put("type", sourceType);
            o.put("path", mediaPath == null ? "" : mediaPath);
        } catch (JSONException ignored) {
        }
        return o;
    }

    public static CameraConfig fromJson(JSONObject o) {
        CameraConfig c = new CameraConfig();
        if (o == null) {
            return c;
        }
        c.enabled = o.optBoolean("enabled", false);
        c.sourceType = o.optString("type", TYPE_IMAGE);
        c.mediaPath = o.optString("path", "");
        return c;
    }
}
