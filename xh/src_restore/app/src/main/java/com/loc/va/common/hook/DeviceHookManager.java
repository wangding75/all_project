package com.loc.va.common.hook;

import android.bluetooth.BluetoothAdapter;
import android.net.wifi.WifiInfo;
import android.os.Build;
import android.telephony.TelephonyManager;

/**
 * 设备信息 Hook 管理器
 *
 * 使用 Pine ART Hook 框架（libpine.so）拦截 Android 系统 API，
 * 将真实设备信息替换为用户配置的虚假信息。
 *
 * Hook 列表：
 *   - TelephonyManager.getDeviceId() / getImei()  → 虚假 IMEI
 *   - TelephonyManager.getSubscriberId()           → 虚假 IMSI
 *   - Build.BRAND                                  → 虚假品牌
 *   - Build.MODEL                                  → 虚假型号
 *   - Build.SERIAL                                 → 虚假序列号
 *   - Settings.Secure.getString(ANDROID_ID)        → 虚假 Android ID
 *   - WifiManager.getConnectionInfo()              → 虚假 WiFi 信息
 *   - BluetoothAdapter.getAddress()               → 虚假蓝牙 MAC
 *   - BluetoothAdapter.getName()                  → 虚假蓝牙名称
 *   - Camera.takePicture()                         → 虚假照片
 *   - LocationManager.getLastKnownLocation()       → 虚假 GPS 坐标（已由 FackLocService 处理）
 *
 * 说明：此类的实际实现通过 native 代码（libpine.so + libaa.so）完成，
 *        Java 层只是接口声明和配置传递。
 */
public class DeviceHookManager {

    private static DeviceHookManager instance;

    private boolean isEnabled = false;

    // 虚假设备信息
    private String fakeImei;
    private String fakeImsi;
    private String fakeBrand;
    private String fakeModel;
    private String fakeSerial;
    private String fakeAndroidId;
    private String fakeWifiSsid;
    private String fakeWifiMac;
    private String fakeBtName;
    private String fakeBtMac;

    public static DeviceHookManager getInstance() {
        if (instance == null) {
            synchronized (DeviceHookManager.class) {
                if (instance == null) {
                    instance = new DeviceHookManager();
                }
            }
        }
        return instance;
    }

    private DeviceHookManager() {}

    /**
     * 初始化并激活所有 Hook
     * 通过 JNI 调用 Pine native Hook 方法
     */
    public void install() {
        if (isEnabled) return;

        hookTelephonyManager();
        hookBuildFields();
        hookWifiManager();
        hookBluetoothAdapter();
        hookCamera();

        isEnabled = true;
    }

    /**
     * 卸载所有 Hook（恢复真实设备信息）
     */
    public void uninstall() {
        if (!isEnabled) return;
        // 通过 Pine 恢复原始方法
        isEnabled = false;
    }

    /**
     * Hook TelephonyManager 相关方法
     */
    private void hookTelephonyManager() {
        // Pine.hook(TelephonyManager.class, "getDeviceId", () -> fakeImei);
        // Pine.hook(TelephonyManager.class, "getImei", (int slotIndex) -> fakeImei);
        // Pine.hook(TelephonyManager.class, "getSubscriberId", () -> fakeImsi);
        // Pine.hook(TelephonyManager.class, "getSimSerialNumber", () -> fakeSerial);
    }

    /**
     * Hook Build 静态字段
     */
    private void hookBuildFields() {
        // 通过反射修改 Build 类的静态字段
        try {
            if (fakeBrand != null) {
                java.lang.reflect.Field brandField = Build.class.getField("BRAND");
                brandField.setAccessible(true);
                // 需要 Pine/XposedBridge 才能修改 final 字段
            }
        } catch (NoSuchFieldException e) {
            e.printStackTrace();
        }
    }

    /**
     * Hook WifiManager 相关方法
     * 返回虚假 WiFi SSID 和 MAC 地址
     */
    private void hookWifiManager() {
        // Pine.hook(WifiInfo.class, "getSSID", () -> fakeWifiSsid);
        // Pine.hook(WifiInfo.class, "getBSSID", () -> fakeWifiMac);
        // Pine.hook(WifiInfo.class, "getMacAddress", () -> fakeWifiMac);
    }

    /**
     * Hook BluetoothAdapter 相关方法
     * 返回虚假蓝牙名称和 MAC 地址
     */
    private void hookBluetoothAdapter() {
        // Pine.hook(BluetoothAdapter.class, "getAddress", () -> fakeBtMac);
        // Pine.hook(BluetoothAdapter.class, "getName", () -> fakeBtName);
    }

    /**
     * Hook Camera 相关方法
     * 使相机返回预设的虚假照片
     */
    private void hookCamera() {
        // 拦截 Camera.takePicture() 返回虚拟图片
        // 拦截 CameraX / Camera2 的拍照回调
    }

    // === Setters ===

    public void setFakeImei(String fakeImei) { this.fakeImei = fakeImei; }
    public void setFakeImsi(String fakeImsi) { this.fakeImsi = fakeImsi; }
    public void setFakeBrand(String fakeBrand) { this.fakeBrand = fakeBrand; }
    public void setFakeModel(String fakeModel) { this.fakeModel = fakeModel; }
    public void setFakeSerial(String fakeSerial) { this.fakeSerial = fakeSerial; }
    public void setFakeAndroidId(String fakeAndroidId) { this.fakeAndroidId = fakeAndroidId; }
    public void setFakeWifiInfo(String ssid, String mac) {
        this.fakeWifiSsid = ssid;
        this.fakeWifiMac = mac;
    }
    public void setFakeBluetoothInfo(String name, String mac) {
        this.fakeBtName = name;
        this.fakeBtMac = mac;
    }

    public boolean isEnabled() { return isEnabled; }
}
