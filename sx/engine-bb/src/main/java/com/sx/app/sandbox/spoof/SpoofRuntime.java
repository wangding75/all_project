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
import com.sx.app.sandbox.spoof.hook.LocationHook;
import com.sx.app.sandbox.spoof.hook.NetworkHook;

public class SpoofRuntime {

    private static final String TAG = "SX-SpoofRuntime";

    public static void onVirtualClientStart(Context context, String packageName, int userId, String hostPkg) {
        try {
            Log.d(TAG, "spoof installed pkg=" + packageName + " user=" + userId);

            ProfileRepository repo = ProfileRepository.getInstance();
            repo.init(context, hostPkg);

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

        } catch (Throwable e) {
            Log.e(TAG, "Error in SpoofRuntime.onVirtualClientStart for " + packageName, e);
        }
    }
}
