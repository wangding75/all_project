package com.loc.va.utils;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class f {
    public static PackageInfo a(PackageManager packageManager, String str, int i5) {
        try {
            return packageManager.getPackageArchiveInfo(str, i5);
        } catch (Throwable unused) {
            return null;
        }
    }

    public static int b(Context context, String str) {
        PackageInfo a6 = a(context.getPackageManager(), str, 0);
        if (a6 == null) {
            return -1;
        }
        return a6.versionCode;
    }

    public static int c(PackageManager packageManager, String str) {
        PackageInfo a6 = a(packageManager, str, 0);
        if (a6 == null) {
            return -1;
        }
        return a6.versionCode;
    }
}
