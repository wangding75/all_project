package com.sx.app.data;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;

import org.json.JSONObject;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Reads configuration across processes via ConfigProvider and manages cache + hot refresh.
 */
public class ProfileRepository {

    private static final String TAG = "SX-ProfileRepository";
    private static ProfileRepository sInstance;

    private final Map<String, LocationConfig> mLocationCache = new ConcurrentHashMap<>();
    private final Map<String, DeviceProfile> mDeviceCache = new ConcurrentHashMap<>();
    private final Map<String, NetworkProfile> mNetworkCache = new ConcurrentHashMap<>();
    private final Map<String, CameraConfig> mCameraCache = new ConcurrentHashMap<>();
    private final Map<String, BluetoothProfile> mBluetoothCache = new ConcurrentHashMap<>();

    private boolean mReceiverRegistered = false;
    private String mHostPkg;

    public static synchronized ProfileRepository getInstance() {
        if (sInstance == null) {
            sInstance = new ProfileRepository();
        }
        return sInstance;
    }

    public void init(Context context, String hostPkg) {
        this.mHostPkg = hostPkg;
        registerBroadcastIfNeeded(context);
    }

    public synchronized void registerBroadcastIfNeeded(Context context) {
        if (mReceiverRegistered || context == null) return;
        String pkg = resolveHostPkg(context);
        IntentFilter filter = new IntentFilter(pkg + ".action.UPDATE_CONFIG");
        try {
            context.registerReceiver(new BroadcastReceiver() {
                @Override
                public void onReceive(Context ctx, Intent intent) {
                    String updatePkg = intent.getStringExtra("package_name");
                    int userId = intent.getIntExtra("user_id", 0);
                    Log.d(TAG, "Config update broadcast received for pkg: " + updatePkg + ":" + userId);
                    clearCache();
                }
            }, filter);
            mReceiverRegistered = true;
        } catch (Exception e) {
            Log.e(TAG, "Failed to register config update receiver", e);
        }
    }

    private String resolveHostPkg(Context context) {
        if (mHostPkg != null && !mHostPkg.isEmpty()) {
            return mHostPkg;
        }
        try {
            Class<?> bbCore = Class.forName("top.niunaijun.blackbox.BlackBoxCore");
            Object pkg = bbCore.getMethod("getHostPkg").invoke(null);
            if (pkg instanceof String && !((String) pkg).isEmpty()) {
                mHostPkg = (String) pkg;
                return mHostPkg;
            }
        } catch (Throwable ignored) {}
        return context != null ? context.getPackageName() : "com.sx.app";
    }

    public void clearCache() {
        mLocationCache.clear();
        mDeviceCache.clear();
        mNetworkCache.clear();
        mCameraCache.clear();
        mBluetoothCache.clear();
    }

    public LocationConfig resolveLocation(Context context, String pkg, int userId) {
        String cacheKey = (pkg == null ? "global" : pkg) + ":" + userId;
        LocationConfig cached = mLocationCache.get(cacheKey);
        if (cached != null) return cached;

        LocationConfig instanceCfg = queryConfig(context, SxPrefs.KEY_LOCATION, pkg, userId, LocationConfig::fromJson);
        if (instanceCfg != null && instanceCfg.enabled) {
            mLocationCache.put(cacheKey, instanceCfg);
            return instanceCfg;
        }

        // Fallback to global config if instance config not enabled
        if (pkg != null && !pkg.isEmpty()) {
            LocationConfig globalCfg = queryConfig(context, SxPrefs.KEY_LOCATION, null, 0, LocationConfig::fromJson);
            if (globalCfg != null && globalCfg.enabled) {
                mLocationCache.put(cacheKey, globalCfg);
                return globalCfg;
            }
        }

        LocationConfig res = instanceCfg != null ? instanceCfg : new LocationConfig();
        mLocationCache.put(cacheKey, res);
        return res;
    }

    public DeviceProfile resolveDevice(Context context, String pkg, int userId) {
        String cacheKey = (pkg == null ? "global" : pkg) + ":" + userId;
        DeviceProfile cached = mDeviceCache.get(cacheKey);
        if (cached != null) return cached;

        DeviceProfile instanceProfile = queryConfig(context, SxPrefs.KEY_DEVICE, pkg, userId, DeviceProfile::fromJson);
        if (instanceProfile != null && instanceProfile.enabled) {
            mDeviceCache.put(cacheKey, instanceProfile);
            return instanceProfile;
        }

        if (pkg != null && !pkg.isEmpty()) {
            DeviceProfile globalProfile = queryConfig(context, SxPrefs.KEY_DEVICE, null, 0, DeviceProfile::fromJson);
            if (globalProfile != null && globalProfile.enabled) {
                mDeviceCache.put(cacheKey, globalProfile);
                return globalProfile;
            }
        }

        DeviceProfile res = instanceProfile != null ? instanceProfile : new DeviceProfile();
        mDeviceCache.put(cacheKey, res);
        return res;
    }

    public NetworkProfile resolveNetwork(Context context, String pkg, int userId) {
        String cacheKey = (pkg == null ? "global" : pkg) + ":" + userId;
        NetworkProfile cached = mNetworkCache.get(cacheKey);
        if (cached != null) return cached;

        NetworkProfile instanceProfile = queryConfig(context, SxPrefs.KEY_NETWORK, pkg, userId, NetworkProfile::fromJson);
        if (instanceProfile != null && instanceProfile.enabled) {
            mNetworkCache.put(cacheKey, instanceProfile);
            return instanceProfile;
        }

        if (pkg != null && !pkg.isEmpty()) {
            NetworkProfile globalProfile = queryConfig(context, SxPrefs.KEY_NETWORK, null, 0, NetworkProfile::fromJson);
            if (globalProfile != null && globalProfile.enabled) {
                mNetworkCache.put(cacheKey, globalProfile);
                return globalProfile;
            }
        }

        NetworkProfile res = instanceProfile != null ? instanceProfile : new NetworkProfile();
        mNetworkCache.put(cacheKey, res);
        return res;
    }

    public CameraConfig resolveCamera(Context context, String pkg, int userId) {
        String cacheKey = (pkg == null ? "global" : pkg) + ":" + userId;
        CameraConfig cached = mCameraCache.get(cacheKey);
        if (cached != null) return cached;

        CameraConfig instanceConfig = queryConfig(context, SxPrefs.KEY_CAMERA, pkg, userId, CameraConfig::fromJson);
        if (instanceConfig != null && instanceConfig.enabled) {
            mCameraCache.put(cacheKey, instanceConfig);
            return instanceConfig;
        }

        if (pkg != null && !pkg.isEmpty()) {
            CameraConfig globalConfig = queryConfig(context, SxPrefs.KEY_CAMERA, null, 0, CameraConfig::fromJson);
            if (globalConfig != null && globalConfig.enabled) {
                mCameraCache.put(cacheKey, globalConfig);
                return globalConfig;
            }
        }

        CameraConfig res = instanceConfig != null ? instanceConfig : new CameraConfig();
        mCameraCache.put(cacheKey, res);
        return res;
    }

    public BluetoothProfile resolveBluetooth(Context context, String pkg, int userId) {
        String cacheKey = (pkg == null ? "global" : pkg) + ":" + userId;
        BluetoothProfile cached = mBluetoothCache.get(cacheKey);
        if (cached != null) return cached;

        BluetoothProfile instanceProfile = queryConfig(context, SxPrefs.KEY_BLUETOOTH, pkg, userId, BluetoothProfile::fromJson);
        if (instanceProfile != null && instanceProfile.enabled) {
            mBluetoothCache.put(cacheKey, instanceProfile);
            return instanceProfile;
        }

        if (pkg != null && !pkg.isEmpty()) {
            BluetoothProfile globalProfile = queryConfig(context, SxPrefs.KEY_BLUETOOTH, null, 0, BluetoothProfile::fromJson);
            if (globalProfile != null && globalProfile.enabled) {
                mBluetoothCache.put(cacheKey, globalProfile);
                return globalProfile;
            }
        }

        BluetoothProfile res = instanceProfile != null ? instanceProfile : new BluetoothProfile();
        mBluetoothCache.put(cacheKey, res);
        return res;
    }

    private interface Parser<T> {
        T parse(JSONObject json);
    }

    private <T> T queryConfig(Context context, String baseKey, String pkg, int userId, Parser<T> parser) {
        try {
            String hostPkg = resolveHostPkg(context);
            Uri providerUri = Uri.parse("content://" + hostPkg + ".config.provider");
            Log.d(TAG, "Querying ConfigProvider authority=" + hostPkg + ".config.provider for baseKey=" + baseKey + " pkg=" + pkg);
            Bundle extras = new Bundle();
            extras.putString("package_name", pkg);
            extras.putInt("user_id", userId);

            Bundle reply = context.getContentResolver().call(providerUri, "get_config", baseKey, extras);
            if (reply != null) {
                String jsonStr = reply.getString("config_json", "");
                if (jsonStr != null && !jsonStr.isEmpty()) {
                    return parser.parse(new JSONObject(jsonStr));
                }
            }
        } catch (Exception e) {
            Log.w(TAG, "ContentProvider query failed for key " + baseKey + ", falling back to direct SxPrefs read", e);
            String fullKey = SxPrefs.makeKey(baseKey, pkg, userId);
            JSONObject json = SxPrefs.getJson(context, fullKey);
            return parser.parse(json);
        }
        return null;
    }
}
