package com.loc.va.utils;

import android.content.Context;
import android.os.Environment;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class d {
    

    

    public static String a(Context context) {
        return Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES).getPath();
    }

    public static String b(Context context) {
        return (("mounted".equals(Environment.getExternalStorageState()) || !Environment.isExternalStorageRemovable()) ? context.getExternalCacheDir() : context.getCacheDir()).getPath();
    }

    public static String c(Context context) {
        if (!"mounted".equals(Environment.getExternalStorageState())) {
            Environment.isExternalStorageRemovable();
        }
        return context.getFilesDir().getPath();
    }

    public static String d(Context context) {
        return context.getFilesDir().toString();
    }

    public static String e(Context context) {
        if (Environment.getExternalStorageState().equals("mounted")) {
            return null;
        }
        return Environment.getExternalStorageDirectory().toString();
    }
}
