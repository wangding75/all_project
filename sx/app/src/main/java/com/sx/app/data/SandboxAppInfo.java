package com.sx.app.data;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * A sandbox "clone" record.
 * userId 0 = primary instance; additional clones use 1,2,...
 * Data dir is redirected conceptually under app-private sandbox path.
 */
public class SandboxAppInfo {

    public String packageName;
    public String label;
    public int userId;
    public long addedAt;
    public String dataDir;

    public SandboxAppInfo() {}

    public SandboxAppInfo(String packageName, String label, int userId, String dataDir) {
        this.packageName = packageName;
        this.label = label;
        this.userId = userId;
        this.addedAt = System.currentTimeMillis();
        this.dataDir = dataDir;
    }

    public String displayName() {
        if (userId <= 0) {
            return label;
        }
        return label + " #" + (userId + 1);
    }

    public JSONObject toJson() {
        JSONObject o = new JSONObject();
        try {
            o.put("pkg", packageName);
            o.put("label", label);
            o.put("userId", userId);
            o.put("addedAt", addedAt);
            o.put("dataDir", dataDir);
        } catch (JSONException ignored) {
        }
        return o;
    }

    public static SandboxAppInfo fromJson(JSONObject o) {
        SandboxAppInfo info = new SandboxAppInfo();
        if (o == null) {
            return info;
        }
        info.packageName = o.optString("pkg");
        info.label = o.optString("label");
        info.userId = o.optInt("userId", 0);
        info.addedAt = o.optLong("addedAt", 0L);
        info.dataDir = o.optString("dataDir");
        return info;
    }
}
