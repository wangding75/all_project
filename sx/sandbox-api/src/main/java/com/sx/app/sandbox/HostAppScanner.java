package com.sx.app.sandbox;

import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import java.util.ArrayList;
import java.util.List;

public class HostAppScanner {
    
    public List<HostAppInfo> loadLaunchableApps(Context context) {
        List<HostAppInfo> list = new ArrayList<>();
        PackageManager pm = context.getPackageManager();
        Intent mainIntent = new Intent(Intent.ACTION_MAIN, null);
        mainIntent.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> apps = pm.queryIntentActivities(mainIntent, 0);
        String selfPkg = context.getPackageName();

        for (ResolveInfo info : apps) {
            if (info.activityInfo != null && info.activityInfo.applicationInfo != null) {
                String pkg = info.activityInfo.packageName;
                // Note (Requirement M7): Allow host app to be imported into sandbox for Probe verification.
                boolean isSystem = (info.activityInfo.applicationInfo.flags & ApplicationInfo.FLAG_SYSTEM) != 0;
                if (isSystem) {
                    continue;
                }
                String label = info.loadLabel(pm).toString();
                android.graphics.drawable.Drawable icon = info.loadIcon(pm);
                String sourceDir = info.activityInfo.applicationInfo.sourceDir;
                list.add(new HostAppInfo(pkg, label, icon, sourceDir));
            }
        }
        return list;
    }
}
