package com.loc.va.utils;

import android.os.IBinder;
import android.os.RemoteException;
import android.util.Log;
import com.lody.virtual.helper.utils.p;
import j3.r;
import java.lang.reflect.Method;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class e {
    

    /* renamed from: a, reason: collision with root package name */
    public static String f23485a = "IBinderTool";

    

    public static void a() {
        for (String str : (String[]) p.x(r.TYPE).e("listServices").q()) {
            IBinder iBinder = (IBinder) p.x(r.TYPE).f("getService", str).q();
            String $2 = "srv=";
            if (iBinder == null) {
                Log.w(f23485a, $2 + str + " no find ");
            } else {
                try {
                    Log.i(f23485a, $2 + str + "@" + iBinder.getInterfaceDescriptor());
                } catch (RemoteException e6) {
                    e6.printStackTrace();
                }
            }
        }
    }

    public static void b(String str) {
        try {
            for (Method method : Class.forName(str).getDeclaredMethods()) {
                Log.i(f23485a, "method=" + ((Object) method));
            }
        } catch (Throwable th) {
            th.printStackTrace();
        }
    }

    public static void c(String str) {
        f23485a = str;
    }
}
