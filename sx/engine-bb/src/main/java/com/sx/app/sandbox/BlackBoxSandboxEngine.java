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
import com.sx.app.data.SandboxAppInfo;
// import com.sx.app.ui.sandbox.ShortcutLaunchActivity;
import java.util.ArrayList;
import java.util.List;
import top.niunaijun.blackbox.BlackBoxCore;
import top.niunaijun.blackbox.app.configuration.ClientConfiguration;
import top.niunaijun.blackbox.core.system.user.BUserInfo;

public class BlackBoxSandboxEngine implements SandboxEngine {
    private static final String TAG = "BlackBoxSandboxEngine";
    private Application mApp;
    private boolean mReady = false;

    @Override
    public void initialize(Application app) {
        mApp = app;
        Log.d(TAG, "BlackBoxSandboxEngine instance initialized.");
    }

    @Override
    public void onAttachBaseContext(Context base) {
        try {
            BlackBoxCore.get().doAttachBaseContext(base, new ClientConfiguration() {
                @Override
                public String getHostPackageName() {
                    return base.getPackageName();
                }

                @Override
                public boolean isEnableDaemonService() {
                    return false;
                }

                @Override
                public boolean isEnableLauncherActivity() {
                    return false;
                }
            });
            Log.d(TAG, "BlackBoxCore doAttachBaseContext completed.");
        } catch (Exception e) {
            Log.e(TAG, "Failed to attach base context for BlackBoxCore", e);
        }
    }

    @Override
    public void onAppCreate() {
        try {
            BlackBoxCore.get().doCreate();
            BlackBoxCore.get().addAppLifecycleCallback(new top.niunaijun.blackbox.app.configuration.AppLifecycleCallback() {
                @Override
                public void beforeCreateApplication(String packageName, String processName, Context context, int userId) {
                    String hostPkg = BlackBoxCore.getHostPkg();
                    Log.d(TAG, "beforeCreateApplication: pkg=" + packageName + " process=" + processName + " user=" + userId + " hostPkg=" + hostPkg);
                    com.sx.app.sandbox.spoof.SpoofRuntime.onVirtualClientStart(context, packageName, userId, hostPkg);
                }
            });
            mReady = true;
            Log.d(TAG, "BlackBoxCore doCreate completed. Engine is ready.");
        } catch (Exception e) {
            Log.e(TAG, "Failed to call doCreate for BlackBoxCore", e);
        }
    }

    @Override
    public boolean isReady() {
        return mReady;
    }

    @Override
    public InstallResult installFromHost(String packageName) {
        if (!mReady) {
            return new InstallResult(false, -1, "Engine not ready");
        }
        if (isInstalled(packageName, 0)) {
            return new InstallResult(true, 0, "Already installed");
        }
        try {
            top.niunaijun.blackbox.entity.pm.InstallResult result = 
                    BlackBoxCore.get().installPackageAsUser(packageName, 0);
            if (result.success) {
                Log.d(TAG, "Successfully installed " + packageName + " for user 0");
                return new InstallResult(true, 0, "Success");
            } else {
                Log.w(TAG, "Failed to install " + packageName + ": " + result.msg);
                return new InstallResult(false, -1, result.msg);
            }
        } catch (Exception e) {
            Log.e(TAG, "Exception installing " + packageName, e);
            return new InstallResult(false, -1, e.getMessage());
        }
    }

    @Override
    public InstallResult installFromApk(String apkPath) {
        return new InstallResult(false, -1, "Not supported in Phase 1");
    }

    @Override
    public boolean uninstall(String packageName, int userId) {
        if (!mReady) return false;
        try {
            // If it is the primary user (0), we can uninstall the package completely.
            // But to align with single-user removal behavior, we use uninstallPackageAsUser.
            BlackBoxCore.get().uninstallPackageAsUser(packageName, userId);
            Log.d(TAG, "Uninstalled " + packageName + " for user " + userId);
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Failed to uninstall package " + packageName + " for user " + userId, e);
            return false;
        }
    }

    @Override
    public boolean clearData(String packageName, int userId) {
        if (!mReady) return false;
        try {
            BlackBoxCore.get().clearPackage(packageName, userId);
            Log.d(TAG, "Cleared data of " + packageName + " for user " + userId);
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Failed to clear package " + packageName + " for user " + userId, e);
            return false;
        }
    }

    @Override
    public List<SandboxAppInfo> listInstalled() {
        List<SandboxAppInfo> result = new ArrayList<>();
        if (!mReady || mApp == null) return result;
        try {
            PackageManager pm = mApp.getPackageManager();
            List<BUserInfo> users = BlackBoxCore.get().getUsers();
            for (BUserInfo user : users) {
                int userId = user.id;
                List<ApplicationInfo> apps = BlackBoxCore.get().getInstalledApplications(0, userId);
                for (ApplicationInfo appInfo : apps) {
                    String pkg = appInfo.packageName;
                    // Filter system/stub packages if desired, but general apps should be shown
                    if (pkg.equals("com.google.android.gms") || pkg.equals("com.android.vending")) {
                        continue;
                    }
                    String label = mApp.getSharedPreferences("sx_app_labels", Context.MODE_PRIVATE)
                            .getString(pkg + "_" + userId, null);
                    if (label == null) {
                        label = appInfo.loadLabel(pm).toString();
                    }
                    String dataDir = appInfo.dataDir;
                    result.add(new SandboxAppInfo(pkg, label, userId, dataDir));
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error listing installed sandbox apps", e);
        }
        return result;
    }

    @Override
    public SandboxAppInfo get(String packageName, int userId) {
        if (!mReady) return null;
        List<SandboxAppInfo> list = listInstalled();
        for (SandboxAppInfo info : list) {
            if (info.packageName.equals(packageName) && info.userId == userId) {
                return info;
            }
        }
        return null;
    }

    @Override
    public boolean isInstalled(String packageName, int userId) {
        if (!mReady) return false;
        try {
            return BlackBoxCore.get().isInstalled(packageName, userId);
        } catch (Exception e) {
            Log.e(TAG, "Error checking if installed " + packageName, e);
            return false;
        }
    }

    @Override
    public boolean launch(String packageName, int userId) {
        if (!mReady) return false;
        if (mApp != null && !com.sx.app.license.LicenseManager.isActivated(mApp)) {
            Log.w(TAG, "Launch blocked: License is not activated or has expired.");
            return false;
        }
        try {
            Log.d(TAG, "Launching " + packageName + " for user " + userId);
            return BlackBoxCore.get().launchApk(packageName, userId);
        } catch (Exception e) {
            Log.e(TAG, "Error launching " + packageName + " for user " + userId, e);
            return false;
        }
    }

    @Override
    public boolean kill(String packageName, int userId) {
        if (!mReady) return false;
        try {
            BlackBoxCore.get().stopPackage(packageName, userId);
            Log.d(TAG, "Killed " + packageName + " for user " + userId);
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Failed to kill package " + packageName + " for user " + userId, e);
            return false;
        }
    }

    @Override
    public void killAll() {
        if (!mReady) return;
        try {
            List<SandboxAppInfo> list = listInstalled();
            for (SandboxAppInfo info : list) {
                BlackBoxCore.get().stopPackage(info.packageName, info.userId);
            }
            Log.d(TAG, "Killed all virtual processes.");
        } catch (Exception e) {
            Log.e(TAG, "Error killing all processes", e);
        }
    }

    @Override
    public int clone(String packageName) {
        if (!mReady) return -1;
        try {
            List<SandboxAppInfo> list = listInstalled();
            int maxUserId = -1;
            boolean foundPrimary = false;
            for (SandboxAppInfo info : list) {
                if (info.packageName.equals(packageName)) {
                    if (info.userId == 0) {
                        foundPrimary = true;
                    }
                    if (info.userId > maxUserId) {
                        maxUserId = info.userId;
                    }
                }
            }
            if (!foundPrimary) {
                Log.w(TAG, "Cannot clone, primary package not installed: " + packageName);
                return -1;
            }
            int newUserId = maxUserId + 1;
            
            // Create user
            BlackBoxCore.get().createUser(newUserId);
            
            // Install package
            top.niunaijun.blackbox.entity.pm.InstallResult result = 
                    BlackBoxCore.get().installPackageAsUser(packageName, newUserId);
            if (result.success) {
                Log.d(TAG, "Successfully cloned " + packageName + " with new userId: " + newUserId);
                return newUserId;
            } else {
                Log.w(TAG, "Failed to install package during clone: " + result.msg);
                return -1;
            }
        } catch (Exception e) {
            Log.e(TAG, "Exception cloning package " + packageName, e);
            return -1;
        }
    }

    @Override
    public boolean createShortcut(Context context, String packageName, int userId) {
        SandboxAppInfo info = get(packageName, userId);
        if (info == null) return false;

        String displayName = info.displayName();

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            ShortcutManager sm = context.getSystemService(ShortcutManager.class);
            if (sm != null && sm.isRequestPinShortcutSupported()) {
                Intent intent = new Intent();
                intent.setClassName(context.getPackageName(), "com.sx.app.ui.sandbox.ShortcutLaunchActivity");
                intent.setAction("com.sx.app.action.LAUNCH_SANDBOX");
                intent.putExtra("package_name", packageName);
                intent.putExtra("user_id", userId);

                // Use the host application icon for shortcut if available
                Icon icon;
                try {
                    PackageManager pm = context.getPackageManager();
                    android.graphics.drawable.Drawable d = pm.getApplicationIcon(packageName);
                    if (d instanceof android.graphics.drawable.BitmapDrawable) {
                        android.graphics.Bitmap bmp = ((android.graphics.drawable.BitmapDrawable) d).getBitmap();
                        if (bmp != null) {
                            icon = Icon.createWithBitmap(bmp);
                        } else {
                            icon = Icon.createWithResource(context, getAppIconResId(context));
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
                    icon = Icon.createWithResource(context, getAppIconResId(context));
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

    private int getAppIconResId(Context context) {
        int resId = context.getResources().getIdentifier("ic_launcher", "mipmap", context.getPackageName());
        if (resId == 0) {
            resId = context.getResources().getIdentifier("ic_launcher", "drawable", context.getPackageName());
        }
        if (resId == 0) {
            resId = context.getApplicationInfo().icon;
        }
        return resId;
    }

    @Override
    public void setDisplayName(String packageName, int userId, String name) {
        if (mApp == null) return;
        try {
            mApp.getSharedPreferences("sx_app_labels", Context.MODE_PRIVATE)
                    .edit()
                    .putString(packageName + "_" + userId, name)
                    .apply();
            Log.d(TAG, "Updated display name for " + packageName + "_" + userId + " to: " + name);
        } catch (Exception e) {
            Log.e(TAG, "Failed to save display name for " + packageName, e);
        }
    }
}
