package com.loc.va.model;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.drawable.Drawable;
import com.lody.virtual.remote.InstalledAppInfo;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class v {

    /* renamed from: a, reason: collision with root package name */
    public String f22687a;

    /* renamed from: b, reason: collision with root package name */
    public int f22688b;

    /* renamed from: c, reason: collision with root package name */
    public String f22689c;

    /* renamed from: d, reason: collision with root package name */
    public Drawable f22690d;

    public v() {
    }

    public v(Context context, InstalledAppInfo installedAppInfo, int i5) {
        this.f22687a = installedAppInfo == null ? null : installedAppInfo.f24691a;
        this.f22688b = i5;
        if (installedAppInfo != null) {
            a(context, installedAppInfo.h(installedAppInfo.i()[0]));
        }
    }

    private void a(Context context, ApplicationInfo applicationInfo) {
        if (applicationInfo == null) {
            return;
        }
        PackageManager packageManager = context.getPackageManager();
        try {
            this.f22689c = applicationInfo.loadLabel(packageManager).toString();
            this.f22690d = applicationInfo.loadIcon(packageManager);
        } catch (Throwable th) {
            th.printStackTrace();
        }
    }
}
