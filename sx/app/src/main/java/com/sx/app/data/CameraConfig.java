package com.sx.app.data;

import android.content.Context;

import org.json.JSONException;
import org.json.JSONObject;

/** Virtual camera media source configuration. */
public class CameraConfig {

    public static final String TYPE_VIDEO = "video";
    public static final String TYPE_IMAGE = "image";

    public boolean enabled;
    public String sourceType = TYPE_VIDEO;
    public String mediaPath = "";

    public static CameraConfig load(Context context) {
        return fromJson(SxPrefs.getJson(context, SxPrefs.KEY_CAMERA));
    }

    public void save(Context context) {
        SxPrefs.putJson(context, SxPrefs.KEY_CAMERA, toJson());
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
        c.sourceType = o.optString("type", TYPE_VIDEO);
        c.mediaPath = o.optString("path", "");
        return c;
    }
}
