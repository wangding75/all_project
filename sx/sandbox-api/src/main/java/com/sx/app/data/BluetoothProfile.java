package com.sx.app.data;

import android.content.Context;

import com.sx.app.util.DeviceIdGenerator;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/** Bluetooth device profile for spoofing BluetoothAdapter & scan results. */
public class BluetoothProfile {

    public boolean enabled;
    public String name = "SX_Bluetooth";
    public String address = "02:00:00:00:00:03";
    public List<BtDevice> bondedDevices = new ArrayList<>();
    public List<BtDevice> scanList = new ArrayList<>();

    public static class BtDevice {
        public String name;
        public String address;
        public int rssi;

        public BtDevice() {}

        public BtDevice(String name, String address, int rssi) {
            this.name = name;
            this.address = address;
            this.rssi = rssi;
        }
    }

    public static BluetoothProfile load(Context context) {
        return load(context, null, 0);
    }

    public static BluetoothProfile load(Context context, String pkg, int userId) {
        String key = SxPrefs.makeKey(SxPrefs.KEY_BLUETOOTH, pkg, userId);
        return fromJson(SxPrefs.getJson(context, key));
    }

    public void save(Context context) {
        save(context, null, 0);
    }

    public void save(Context context, String pkg, int userId) {
        String key = SxPrefs.makeKey(SxPrefs.KEY_BLUETOOTH, pkg, userId);
        SxPrefs.putJson(context, key, toJson());
        ConfigBroadcast.notifyChanged(context, pkg, userId);
    }

    public void randomize() {
        name = "SX_BT_" + DeviceIdGenerator.randomAlpha(4);
        address = DeviceIdGenerator.randomMac();
        bondedDevices.clear();
        scanList.clear();
        for (int i = 0; i < 3; i++) {
            bondedDevices.add(new BtDevice(
                    "Paired_BT_" + DeviceIdGenerator.randomAlpha(3),
                    DeviceIdGenerator.randomMac(),
                    -50 - (int) (Math.random() * 30)
            ));
        }
        for (int i = 0; i < 5; i++) {
            scanList.add(new BtDevice(
                    "BLE_" + DeviceIdGenerator.randomAlpha(3),
                    DeviceIdGenerator.randomMac(),
                    -40 - (int) (Math.random() * 40)
            ));
        }
    }

    public JSONObject toJson() {
        JSONObject o = new JSONObject();
        try {
            o.put("enabled", enabled);
            o.put("name", name == null ? "" : name);
            o.put("address", address == null ? "" : address);

            JSONArray bondedArr = new JSONArray();
            for (BtDevice d : bondedDevices) {
                JSONObject b = new JSONObject();
                b.put("name", d.name);
                b.put("address", d.address);
                b.put("rssi", d.rssi);
                bondedArr.put(b);
            }
            o.put("bondedDevices", bondedArr);

            JSONArray scanArr = new JSONArray();
            for (BtDevice d : scanList) {
                JSONObject s = new JSONObject();
                s.put("name", d.name);
                s.put("address", d.address);
                s.put("rssi", d.rssi);
                scanArr.put(s);
            }
            o.put("scanList", scanArr);
        } catch (JSONException ignored) {
        }
        return o;
    }

    public static BluetoothProfile fromJson(JSONObject o) {
        BluetoothProfile p = new BluetoothProfile();
        if (o == null) {
            return p;
        }
        p.enabled = o.optBoolean("enabled", false);
        p.name = o.optString("name", "SX_Bluetooth");
        p.address = o.optString("address", "02:00:00:00:00:03");

        JSONArray bondedArr = o.optJSONArray("bondedDevices");
        if (bondedArr != null) {
            for (int i = 0; i < bondedArr.length(); i++) {
                JSONObject b = bondedArr.optJSONObject(i);
                if (b != null) {
                    p.bondedDevices.add(new BtDevice(
                            b.optString("name", "BT_Device"),
                            b.optString("address", "02:00:00:00:00:00"),
                            b.optInt("rssi", -60)
                    ));
                }
            }
        }

        JSONArray scanArr = o.optJSONArray("scanList");
        if (scanArr != null) {
            for (int i = 0; i < scanArr.length(); i++) {
                JSONObject s = scanArr.optJSONObject(i);
                if (s != null) {
                    p.scanList.add(new BtDevice(
                            s.optString("name", "BLE_Device"),
                            s.optString("address", "02:00:00:00:00:00"),
                            s.optInt("rssi", -55)
                    ));
                }
            }
        }
        return p;
    }
}
