package com.sx.app.sandbox.spoof.hook;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.util.Log;

import com.sx.app.data.BluetoothProfile;

import java.util.HashSet;
import java.util.Set;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XC_MethodHook.MethodHookParam;
import de.robv.android.xposed.XposedHelpers;

public class BluetoothHook {

    private static final String TAG = "SX-BluetoothHook";

    public static void install(ClassLoader classLoader, BluetoothProfile profile) {
        if (profile == null || !profile.enabled) return;

        try {
            // 1. BluetoothAdapter.getName()
            XposedHelpers.findAndHookMethod(BluetoothAdapter.class, "getName", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (profile.name != null && !profile.name.isEmpty()) {
                        param.setResult(profile.name);
                    }
                }
            });

            // 2. BluetoothAdapter.getAddress()
            XposedHelpers.findAndHookMethod(BluetoothAdapter.class, "getAddress", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (profile.address != null && !profile.address.isEmpty()) {
                        param.setResult(profile.address);
                    }
                }
            });

            // 3. BluetoothAdapter.getBondedDevices()
            XposedHelpers.findAndHookMethod(BluetoothAdapter.class, "getBondedDevices", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    if (profile.bondedDevices != null && !profile.bondedDevices.isEmpty()) {
                        try {
                            BluetoothAdapter adapter = (BluetoothAdapter) param.thisObject;
                            if (adapter != null) {
                                Set<BluetoothDevice> devices = new HashSet<>();
                                for (BluetoothProfile.BtDevice dev : profile.bondedDevices) {
                                    if (dev.address != null && !dev.address.isEmpty()) {
                                        try {
                                            BluetoothDevice d = adapter.getRemoteDevice(dev.address);
                                            if (d != null) {
                                                devices.add(d);
                                            }
                                        } catch (Throwable ignored) {}
                                    }
                                }
                                param.setResult(devices);
                            }
                        } catch (Throwable t) {
                            Log.w(TAG, "Error constructing fake bonded Bluetooth devices", t);
                        }
                    }
                }
            });

            // 4. BluetoothDevice.getName()
            XposedHelpers.findAndHookMethod(BluetoothDevice.class, "getName", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    try {
                        BluetoothDevice dev = (BluetoothDevice) param.thisObject;
                        if (dev != null) {
                            String addr = dev.getAddress();
                            if (profile.bondedDevices != null) {
                                for (BluetoothProfile.BtDevice b : profile.bondedDevices) {
                                    if (b.address != null && b.address.equalsIgnoreCase(addr)) {
                                        if (b.name != null && !b.name.isEmpty()) {
                                            param.setResult(b.name);
                                            return;
                                        }
                                    }
                                }
                            }
                            if (profile.scanList != null) {
                                for (BluetoothProfile.BtDevice s : profile.scanList) {
                                    if (s.address != null && s.address.equalsIgnoreCase(addr)) {
                                        if (s.name != null && !s.name.isEmpty()) {
                                            param.setResult(s.name);
                                            return;
                                        }
                                    }
                                }
                            }
                        }
                    } catch (Throwable ignored) {}
                }
            });

            Log.d(TAG, "BluetoothHook installed successfully.");
        } catch (Throwable e) {
            Log.e(TAG, "Failed to install BluetoothHook", e);
        }
    }
}
