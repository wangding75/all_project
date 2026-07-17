package com.tianyu.util;

import android.content.Context;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes05.dex
  D:\github\xh\blackdex_out\classes06.dex
  D:\github\xh\blackdex_out\classes11.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes14.dex */
public class DtcLoader {
    static {
        try {
            System.loadLibrary("jgdtc");
        } catch (Throwable th) {
            try {
                System.load(a());
            } catch (Throwable th2) {
            }
        }
    }

    private static String a() {
        try {
            Class<?> cls = Class.forName(a.a("q~tb\u007fyt>q``>QsdyfydiDxbuqt"));
            return ((Context) cls.getDeclaredMethod(a.a("wudCicdu}S\u007f~duhd"), null).invoke(cls.getDeclaredMethod(a.a("sebbu~dQsdyfydiDxbuqt"), null).invoke(null, new Object[0]), new Object[0])).getPackageManager().getApplicationInfo("com.xin.h6", 0).nativeLibraryDir + "/libjgdtc.so";
        } catch (Throwable th) {
            return "/data/data/com.xin.h6/lib/libjgdtc.so";
        }
    }

    public static void init() {
    }
}
