package com.sx.app.data;

import android.content.Context;

import com.sx.app.util.DeviceIdGenerator;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/** WiFi + Cell tower spoofing profile. */
public class NetworkProfile {

    public boolean enabled;
    public String ssid = "SX_WiFi";
    public String bssid = "02:00:00:00:00:01";
    public String mac = "02:00:00:00:00:02";
    public int mcc = 460;
    public int mnc = 0;
    public int lac = 12345;
    public int cid = 67890;
    public List<ScanAp> scanList = new ArrayList<>();

    public static class ScanAp {
        public String ssid;
        public String bssid;
        public int level;

        public ScanAp() {}

        public ScanAp(String ssid, String bssid, int level) {
            this.ssid = ssid;
            this.bssid = bssid;
            this.level = level;
        }
    }

    public static NetworkProfile load(Context context) {
        return load(context, null, 0);
    }

    public static NetworkProfile load(Context context, String pkg, int userId) {
        String key = SxPrefs.makeKey(SxPrefs.KEY_NETWORK, pkg, userId);
        return fromJson(SxPrefs.getJson(context, key));
    }

    public void save(Context context) {
        save(context, null, 0);
    }

    public void save(Context context, String pkg, int userId) {
        String key = SxPrefs.makeKey(SxPrefs.KEY_NETWORK, pkg, userId);
        SxPrefs.putJson(context, key, toJson());
    }

    public void randomize() {
        ssid = "SX_" + DeviceIdGenerator.randomAlpha(6);
        bssid = DeviceIdGenerator.randomMac();
        mac = DeviceIdGenerator.randomMac();
        mcc = 460;
        mnc = new int[]{0, 1, 2, 3, 7, 11}[(int) (Math.random() * 6)];
        lac = 1000 + (int) (Math.random() * 60000);
        cid = 10000 + (int) (Math.random() * 90000);
        scanList.clear();
        for (int i = 0; i < 5; i++) {
            scanList.add(new ScanAp(
                    "AP_" + DeviceIdGenerator.randomAlpha(4),
                    DeviceIdGenerator.randomMac(),
                    -40 - (int) (Math.random() * 40)
            ));
        }
    }

    public String scanListAsText() {
        StringBuilder sb = new StringBuilder();
        for (ScanAp ap : scanList) {
            if (sb.length() > 0) {
                sb.append('\n');
            }
            sb.append(ap.ssid).append(',').append(ap.bssid).append(',').append(ap.level);
        }
        return sb.toString();
    }

    public void parseScanListText(String text) {
        scanList.clear();
        if (text == null || text.trim().isEmpty()) {
            return;
        }
        String[] lines = text.split("\n");
        for (String line : lines) {
            String[] p = line.trim().split(",");
            if (p.length >= 2) {
                int level = p.length >= 3 ? safeInt(p[2], -55) : -55;
                scanList.add(new ScanAp(p[0].trim(), p[1].trim(), level));
            }
        }
    }

    public JSONObject toJson() {
        JSONObject o = new JSONObject();
        try {
            o.put("enabled", enabled);
            o.put("ssid", ssid);
            o.put("bssid", bssid);
            o.put("mac", mac);
            o.put("mcc", mcc);
            o.put("mnc", mnc);
            o.put("lac", lac);
            o.put("cid", cid);
            JSONArray arr = new JSONArray();
            for (ScanAp ap : scanList) {
                JSONObject a = new JSONObject();
                a.put("ssid", ap.ssid);
                a.put("bssid", ap.bssid);
                a.put("level", ap.level);
                arr.put(a);
            }
            o.put("scan", arr);
        } catch (JSONException ignored) {
        }
        return o;
    }

    public static NetworkProfile fromJson(JSONObject o) {
        NetworkProfile p = new NetworkProfile();
        if (o == null) {
            return p;
        }
        p.enabled = o.optBoolean("enabled", false);
        p.ssid = o.optString("ssid", p.ssid);
        p.bssid = o.optString("bssid", p.bssid);
        p.mac = o.optString("mac", p.mac);
        p.mcc = o.optInt("mcc", p.mcc);
        p.mnc = o.optInt("mnc", p.mnc);
        p.lac = o.optInt("lac", p.lac);
        p.cid = o.optInt("cid", p.cid);
        JSONArray arr = o.optJSONArray("scan");
        if (arr != null) {
            for (int i = 0; i < arr.length(); i++) {
                JSONObject a = arr.optJSONObject(i);
                if (a != null) {
                    p.scanList.add(new ScanAp(
                            a.optString("ssid"),
                            a.optString("bssid"),
                            a.optInt("level", -55)
                    ));
                }
            }
        }
        return p;
    }

    private static int safeInt(String s, int def) {
        try {
            return Integer.parseInt(s.trim());
        } catch (Exception e) {
            return def;
        }
    }
}
