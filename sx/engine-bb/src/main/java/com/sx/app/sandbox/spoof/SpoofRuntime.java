package com.sx.app.sandbox.spoof;

import android.content.Context;
import android.util.Log;

import com.sx.app.data.BluetoothProfile;
import com.sx.app.data.CameraConfig;
import com.sx.app.data.DeviceProfile;
import com.sx.app.data.LocationConfig;
import com.sx.app.data.NetworkProfile;
import com.sx.app.data.ProfileRepository;
import com.sx.app.sandbox.spoof.hook.BluetoothHook;
import com.sx.app.sandbox.spoof.hook.CameraHook;
import com.sx.app.sandbox.spoof.hook.CellHook;
import com.sx.app.sandbox.spoof.hook.DeviceHook;
import com.sx.app.sandbox.spoof.hook.DingTalkHook;
import com.sx.app.sandbox.spoof.hook.LocationHook;
import com.sx.app.sandbox.spoof.hook.NetworkHook;

public class SpoofRuntime {

    private static final String TAG = "SX-SpoofRuntime";
    private static volatile String sPackageName;
    private static volatile int sUserId;

    public static void onVirtualClientStart(Context context, String packageName, int userId, String hostPkg) {
        try {
            Log.d(TAG, "spoof installed pkg=" + packageName + " user=" + userId);
            sPackageName = packageName;
            sUserId = userId;

            ProfileRepository repo = ProfileRepository.getInstance();
            repo.init(context, hostPkg);
            repo.setUpdateListener((ctx, pkg, uid) -> {
                // Apply hot refresh for hooks that hold mutable static config.
                // Device BUILD fields may still require process restart.
                try {
                    boolean globalUpdate = pkg == null || pkg.isEmpty();
                    if (!globalUpdate
                            && (!pkg.equals(sPackageName) || uid != sUserId)) {
                        Log.d(TAG, "Ignoring config update for another instance: "
                                + pkg + ":" + uid);
                        return;
                    }
                    LocationConfig loc = repo.resolveLocation(ctx, sPackageName, sUserId);
                    CameraConfig cam = repo.resolveCamera(ctx, sPackageName, sUserId);
                    if (loc != null) {
                        LocationHook.updateConfig(loc);
                    }
                    if (cam != null) {
                        CameraHook.updateConfig(cam);
                    }
                    Log.d(TAG, "Hot-refreshed location/camera config for "
                            + sPackageName + ":" + sUserId);
                } catch (Throwable t) {
                    Log.w(TAG, "Hot refresh failed", t);
                }
            });

            LocationConfig locConfig = repo.resolveLocation(context, packageName, userId);
            DeviceProfile deviceProfile = repo.resolveDevice(context, packageName, userId);
            NetworkProfile netProfile = repo.resolveNetwork(context, packageName, userId);
            CameraConfig cameraConfig = repo.resolveCamera(context, packageName, userId);
            BluetoothProfile btProfile = repo.resolveBluetooth(context, packageName, userId);

            ClassLoader cl = context.getClassLoader();

            if (locConfig != null && locConfig.enabled) {
                LocationHook.install(cl, locConfig);
            }

            if (deviceProfile != null && deviceProfile.enabled) {
                DeviceHook.install(cl, deviceProfile);
            }

            if (netProfile != null && netProfile.enabled) {
                NetworkHook.install(cl, netProfile);
                CellHook.install(cl, netProfile);
            }

            if (cameraConfig != null && cameraConfig.enabled) {
                CameraHook.install(context, cl, cameraConfig);
            }

            if (btProfile != null && btProfile.enabled) {
                BluetoothHook.install(cl, btProfile);
            }

            if (DingTalkHook.PACKAGE.equals(packageName)) {
                DingTalkHook.install(cl, packageName);
            }

        } catch (Throwable e) {
            Log.e(TAG, "Error in SpoofRuntime.onVirtualClientStart for " + packageName, e);
        }
    }
}
