package com.sx.app.data;

import android.content.Context;

import org.json.JSONException;
import org.json.JSONObject;

/** Virtual geolocation configuration. */
public class LocationConfig {

    public boolean enabled;
    public double latitude = 22.543099;
    public double longitude = 113.929884;
    public float accuracy = 2.0f;
    public double altitude = 10.0;
    public long intervalMs = 50L;
    public boolean microDrift = true;
    public boolean antiMockDetect = true;
    public String address = "";

    public static LocationConfig load(Context context) {
        return load(context, null, 0);
    }

    public static LocationConfig load(Context context, String pkg, int userId) {
        String key = SxPrefs.makeKey(SxPrefs.KEY_LOCATION, pkg, userId);
        return fromJson(SxPrefs.getJson(context, key));
    }

    public void save(Context context) {
        save(context, null, 0);
    }

    public void save(Context context, String pkg, int userId) {
        String key = SxPrefs.makeKey(SxPrefs.KEY_LOCATION, pkg, userId);
        SxPrefs.putJson(context, key, toJson());
        ConfigBroadcast.notifyChanged(context, pkg, userId);
    }

    public JSONObject toJson() {
        JSONObject o = new JSONObject();
        try {
            o.put("enabled", enabled);
            o.put("lat", latitude);
            o.put("lng", longitude);
            o.put("accuracy", accuracy);
            o.put("altitude", altitude);
            o.put("intervalMs", intervalMs);
            o.put("microDrift", microDrift);
            o.put("antiMock", antiMockDetect);
            o.put("address", address == null ? "" : address);
        } catch (JSONException ignored) {
        }
        return o;
    }

    public static LocationConfig fromJson(JSONObject o) {
        LocationConfig c = new LocationConfig();
        if (o == null) {
            return c;
        }
        c.enabled = o.optBoolean("enabled", false);
        c.latitude = o.optDouble("lat", c.latitude);
        c.longitude = o.optDouble("lng", c.longitude);
        c.accuracy = (float) o.optDouble("accuracy", c.accuracy);
        c.altitude = o.optDouble("altitude", c.altitude);
        c.intervalMs = o.optLong("intervalMs", c.intervalMs);
        c.microDrift = o.optBoolean("microDrift", true);
        c.antiMockDetect = o.optBoolean("antiMock", true);
        c.address = o.optString("address", "");
        return c;
    }
}
