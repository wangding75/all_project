package com.loc.va.abs.ui;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.TypedValue;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class c {

    /* renamed from: a, reason: collision with root package name */
    private static final org.jdeferred.android.b f20960a = new org.jdeferred.android.b();

    /* renamed from: b, reason: collision with root package name */
    private static final Handler f20961b = new Handler(Looper.getMainLooper());

    public static org.jdeferred.android.b a() {
        return f20960a;
    }

    public static int b(Context context, int i5) {
        return (int) TypedValue.applyDimension(1, i5, context.getResources().getDisplayMetrics());
    }

    public static void c(Runnable runnable) {
        f20961b.post(runnable);
    }

    public static void d(long j5, Runnable runnable) {
        f20961b.postDelayed(runnable, j5);
    }

    public static void e(long j5) {
        try {
            Thread.sleep(j5);
        } catch (InterruptedException e6) {
            e6.printStackTrace();
        }
    }
}
