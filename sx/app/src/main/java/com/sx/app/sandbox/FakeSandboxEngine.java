package com.sx.app.sandbox;

import android.app.Application;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ShortcutInfo;
import android.content.pm.ShortcutManager;
import android.graphics.drawable.Icon;
import android.os.Build;
import android.util.Log;
import com.sx.app.R;
import com.sx.app.data.SandboxAppInfo;
import com.sx.app.data.SxPrefs;
import com.sx.app.ui.sandbox.ShortcutLaunchActivity;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

public class FakeSandboxEngine implements SandboxEngine {
    private static final String TAG = "FakeSandboxEngine";
    private Application mApp;
    private final List<SandboxAppInfo> mList = new ArrayList<>();
    private boolean mReady = false;

    @Override
    public void initialize(Application app) {
        mApp = app;
        mList.clear();
        JSONArray arr = SxPrefs.getJsonArray(app, SxPrefs.KEY_SANDBOX_APPS);
        for (int i = 0; i < arr.length(); i++) {
            JSONObject obj = arr.optJSONObject(i);
            if (obj != null) {
                mList.add(SandboxAppInfo.fromJson(obj));
            }
        }
        mReady = true;
        Log.d(TAG, "FakeSandboxEngine initialized with " + mList.size() + " apps.");
    }

    @Override
    public boolean isReady() {
        return mReady;
    }

    private void persist() {
        if (mApp == null) return;
        JSONArray arr = new JSONArray();
        for (SandboxAppInfo info : mList) {
            arr.put(info.toJson());
        }
        SxPrefs.putJsonArray(mApp, SxPrefs.KEY_SANDBOX_APPS, arr);
    }

    @Override
    public InstallResult installFromHost(String packageName) {
        if (!mReady || mApp == null) {
            return new InstallResult(false, -1, "Engine not initialized");
        }

        // Idempotency: check if primary instance (userId = 0) is already installed
        for (SandboxAppInfo info : mList) {
            if (info.packageName.equals(packageName) && info.userId == 0) {
                return new InstallResult(true, 0, "Already installed");
            }
        }

        PackageManager pm = mApp.getPackageManager();
        try {
            ApplicationInfo appInfo = pm.getApplicationInfo(packageName, 0);
            String label = pm.getApplicationLabel(appInfo).toString();
            String dataDir = appInfo.dataDir;
            
            SandboxAppInfo newApp = new SandboxAppInfo(packageName, label, 0, dataDir);
            mList.add(newApp);
            persist();
            Log.d(TAG, "Installed app from host: " + packageName);
            return new InstallResult(true, 0, "Success");
        } catch (PackageManager.NameNotFoundException e) {
            return new InstallResult(false, -1, "Package not found on host: " + packageName);
        }
    }

    @Override
    public InstallResult installFromApk(String apkPath) {
        return new InstallResult(false, -1, "Not supported in Phase 0");
    }

    @Override
    public boolean uninstall(String packageName, int userId) {
        if (!mReady) return false;
        boolean removed = false;
        for (int i = mList.size() - 1; i >= 0; i--) {
            SandboxAppInfo info = mList.get(i);
            if (info.packageName.equals(packageName) && info.userId == userId) {
                mList.remove(i);
                removed = true;
                break;
            }
        }
        if (removed) {
            persist();
            Log.d(TAG, "Uninstalled: " + packageName + " (User: " + userId + ")");
        }
        return removed;
    }

    @Override
    public boolean clearData(String packageName, int userId) {
        // Phase 0: Just update addedAt time as a change, log and return success
        for (SandboxAppInfo info : mList) {
            if (info.packageName.equals(packageName) && info.userId == userId) {
                info.addedAt = System.currentTimeMillis();
                persist();
                return true;
            }
        }
        return false;
    }

    @Override
    public List<SandboxAppInfo> listInstalled() {
        return new ArrayList<>(mList);
    }

    @Override
    public SandboxAppInfo get(String packageName, int userId) {
        for (SandboxAppInfo info : mList) {
            if (info.packageName.equals(packageName) && info.userId == userId) {
                return info;
            }
        }
        return null;
    }

    @Override
    public boolean isInstalled(String packageName, int userId) {
        return get(packageName, userId) != null;
    }

    @Override
    public boolean launch(String packageName, int userId) {
        Log.d(TAG, "Simulated launch: " + packageName + " for user " + userId);
        return true;
    }

    @Override
    public boolean kill(String packageName, int userId) {
        Log.d(TAG, "Simulated kill: " + packageName + " for user " + userId);
        return true;
    }

    @Override
    public void killAll() {
        Log.d(TAG, "Simulated killAll");
    }

    @Override
    public int clone(String packageName) {
        if (!mReady) return -1;
        
        SandboxAppInfo primary = null;
        int maxUserId = -1;
        for (SandboxAppInfo info : mList) {
            if (info.packageName.equals(packageName)) {
                if (info.userId == 0) {
                    primary = info;
                }
                if (info.userId > maxUserId) {
                    maxUserId = info.userId;
                }
            }
        }

        if (primary == null) {
            Log.w(TAG, "Cannot clone, primary app not installed: " + packageName);
            return -1;
        }

        int newUserId = maxUserId + 1;
        SandboxAppInfo cloneApp = new SandboxAppInfo(packageName, primary.label, newUserId, primary.dataDir);
        mList.add(cloneApp);
        persist();
        Log.d(TAG, "Cloned: " + packageName + " with userId: " + newUserId);
        return newUserId;
    }

    @Override
    public boolean createShortcut(Context context, String packageName, int userId) {
        SandboxAppInfo info = get(packageName, userId);
        if (info == null) return false;

        String displayName = info.displayName();

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            ShortcutManager sm = context.getSystemService(ShortcutManager.class);
            if (sm != null && sm.isRequestPinShortcutSupported()) {
                Intent intent = new Intent(context, ShortcutLaunchActivity.class);
                intent.setAction("com.sx.app.action.LAUNCH_SANDBOX");
                intent.putExtra("package_name", packageName);
                intent.putExtra("user_id", userId);

                // Use the host application icon for shortcut if available
                Icon icon = Icon.createWithResource(context, R.drawable.ic_launcher);
                try {
                    PackageManager pm = context.getPackageManager();
                    android.graphics.drawable.Drawable d = pm.getApplicationIcon(packageName);
                    if (d instanceof android.graphics.drawable.BitmapDrawable) {
                        android.graphics.Bitmap bmp = ((android.graphics.drawable.BitmapDrawable) d).getBitmap();
                        if (bmp != null) {
                            icon = Icon.createWithBitmap(bmp);
                        }
                    } else {
                        // Rasterize custom/Adaptive drawables onto a bitmap
                        int width = d.getIntrinsicWidth() > 0 ? d.getIntrinsicWidth() : 144;
                        int height = d.getIntrinsicHeight() > 0 ? d.getIntrinsicHeight() : 144;
                        android.graphics.Bitmap bmp = android.graphics.Bitmap.createBitmap(width, height, android.graphics.Bitmap.Config.ARGB_8888);
                        android.graphics.Canvas canvas = new android.graphics.Canvas(bmp);
                        d.setBounds(0, 0, canvas.getWidth(), canvas.getHeight());
                        d.draw(canvas);
                        icon = Icon.createWithBitmap(bmp);
                    }
                } catch (Exception e) {
                    icon = Icon.createWithResource(context, R.drawable.ic_launcher);
                }

                ShortcutInfo shortcut = new ShortcutInfo.Builder(context, "sx_" + packageName + "_" + userId)
                        .setShortLabel(displayName)
                        .setIcon(icon)
                        .setIntent(intent)
                        .build();
                return sm.requestPinShortcut(shortcut, null);
            }
        }
        return false;
    }

    @Override
    public void setDisplayName(String packageName, int userId, String name) {
        for (SandboxAppInfo info : mList) {
            if (info.packageName.equals(packageName) && info.userId == userId) {
                info.label = name;
                persist();
                break;
            }
        }
    }
}
