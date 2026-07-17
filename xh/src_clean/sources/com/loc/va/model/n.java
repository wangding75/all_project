package com.loc.va.model;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.icu.impl.PatternTokenizer;
import com.lody.virtual.remote.InstalledAppInfo;
import com.lody.virtual.remote.vloc.VLocation;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class n extends v {
    

    /* renamed from: e, reason: collision with root package name */
    public int f22665e;

    /* renamed from: f, reason: collision with root package name */
    public VLocation f22666f;

    

    public n() {
    }

    public n(Context context, InstalledAppInfo installedAppInfo, int i5) {
        this.f22687a = installedAppInfo.f24691a;
        this.f22688b = i5;
        a(context, installedAppInfo.h(installedAppInfo.i()[0]));
    }

    private void a(Context context, ApplicationInfo applicationInfo) {
        if (applicationInfo == null) {
            return;
        }
        PackageManager packageManager = context.getPackageManager();
        try {
            CharSequence loadLabel = applicationInfo.loadLabel(packageManager);
            if (loadLabel != null) {
                this.f22689c = loadLabel.toString();
            }
            this.f22690d = applicationInfo.loadIcon(packageManager);
        } catch (Throwable th) {
            th.printStackTrace();
        }
    }

    public String toString() {
        return "LocationData{packageName='" + this.f22687a + PatternTokenizer.SINGLE_QUOTE + ", userId=" + this.f22688b + ", location=" + ((Object) this.f22666f) + '}';
    }
}
