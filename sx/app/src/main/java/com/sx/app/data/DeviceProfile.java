package com.sx.app.data;

import android.content.Context;
import android.os.Build;

import com.sx.app.util.DeviceIdGenerator;

import org.json.JSONException;
import org.json.JSONObject;

/** Device hardware fingerprint spoofing profile. */
public class DeviceProfile {

    public boolean enabled;
    public String brand = Build.BRAND;
    public String model = Build.MODEL;
    public String manufacturer = Build.MANUFACTURER;
    public String board = Build.BOARD;
    public String serial = "unknown";
    public String imei = "";
    public String meid = "";
    public String androidId = "";
    public String phoneNumber = "";
    public String imsi = "";
    public String iccid = "";
    public String operatorName = "中国移动";

    public static DeviceProfile load(Context context) {
        return fromJson(SxPrefs.getJson(context, SxPrefs.KEY_DEVICE));
    }

    public void save(Context context) {
        SxPrefs.putJson(context, SxPrefs.KEY_DEVICE, toJson());
    }

    public void randomize() {
        DeviceIdGenerator.DeviceBundle b = DeviceIdGenerator.randomBundle();
        brand = b.brand;
        model = b.model;
        manufacturer = b.manufacturer;
        board = b.board;
        serial = b.serial;
        imei = b.imei;
        meid = b.meid;
        androidId = b.androidId;
        phoneNumber = b.phoneNumber;
        imsi = b.imsi;
        iccid = b.iccid;
        operatorName = b.operatorName;
    }

    public void resetToReal() {
        brand = Build.BRAND;
        model = Build.MODEL;
        manufacturer = Build.MANUFACTURER;
        board = Build.BOARD;
        serial = Build.SERIAL;
        imei = "";
        meid = "";
        androidId = "";
        phoneNumber = "";
        imsi = "";
        iccid = "";
        operatorName = "";
        enabled = false;
    }

    public JSONObject toJson() {
        JSONObject o = new JSONObject();
        try {
            o.put("enabled", enabled);
            o.put("brand", brand);
            o.put("model", model);
            o.put("manufacturer", manufacturer);
            o.put("board", board);
            o.put("serial", serial);
            o.put("imei", imei);
            o.put("meid", meid);
            o.put("androidId", androidId);
            o.put("phone", phoneNumber);
            o.put("imsi", imsi);
            o.put("iccid", iccid);
            o.put("operator", operatorName);
        } catch (JSONException ignored) {
        }
        return o;
    }

    public static DeviceProfile fromJson(JSONObject o) {
        DeviceProfile p = new DeviceProfile();
        if (o == null) {
            return p;
        }
        p.enabled = o.optBoolean("enabled", false);
        p.brand = o.optString("brand", p.brand);
        p.model = o.optString("model", p.model);
        p.manufacturer = o.optString("manufacturer", p.manufacturer);
        p.board = o.optString("board", p.board);
        p.serial = o.optString("serial", p.serial);
        p.imei = o.optString("imei", p.imei);
        p.meid = o.optString("meid", p.meid);
        p.androidId = o.optString("androidId", p.androidId);
        p.phoneNumber = o.optString("phone", p.phoneNumber);
        p.imsi = o.optString("imsi", p.imsi);
        p.iccid = o.optString("iccid", p.iccid);
        p.operatorName = o.optString("operator", p.operatorName);
        return p;
    }
}
