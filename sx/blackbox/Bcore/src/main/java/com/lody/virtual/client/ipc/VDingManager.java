package com.lody.virtual.client.ipc;

import com.lody.virtual.remote.VDingConfig;

/**
 * Stub implementation of VDingManager for DingTalk compatibility.
 */
public class VDingManager {
    public static final int GLOBAL_USERID = 888888;
    public static String GLOBAL_PACKAGE = "com.alibaba.android.rimet";
    private static final VDingManager sInstance = new VDingManager();

    public static VDingManager get() {
        return sInstance;
    }

    public VDingConfig getCurAppDkConfig() {
        return new VDingConfig();
    }

    public boolean getCurAppEnable() {
        return true;
    }

    public VDingConfig getDkConfig(int userId, String pkg) {
        return new VDingConfig();
    }

    public VDingConfig getGlobalDkConfig() {
        return new VDingConfig();
    }

    public boolean getGlobalEnable() {
        return true;
    }

    public boolean isEnable(int userId, String pkg) {
        return true;
    }

    public void setDkConfig(int userId, String pkg, VDingConfig config) {
    }

    public void setEnable(int userId, String pkg, boolean enable) {
    }

    public void setGlobalDkConfig(VDingConfig config) {
    }

    public void setGlobalEnable(boolean enable) {
    }
}
