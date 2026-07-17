package com.loc.va.model;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.drawable.Drawable;
import com.lody.virtual.helper.InstalledInfoCache;
import com.lody.virtual.remote.InstalledAppInfo;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class r extends AppData {

    /* renamed from: c, reason: collision with root package name */
    public String f22678c;

    /* renamed from: d, reason: collision with root package name */
    public String f22679d;

    /* renamed from: e, reason: collision with root package name */
    public Drawable f22680e;

    /* renamed from: f, reason: collision with root package name */
    public boolean f22681f;

    public r(Context context, InstalledAppInfo installedAppInfo) {
        this.f22678c = installedAppInfo.f24691a;
        this.f22625a = !installedAppInfo.u(0);
        this.f22681f = installedAppInfo.f24697g;
        l(context, installedAppInfo.h(installedAppInfo.i()[0]));
    }

    private void l(Context context, ApplicationInfo applicationInfo) {
        Drawable icon;
        if (applicationInfo == null) {
            return;
        }
        PackageManager packageManager = context.getPackageManager();
        try {
            InstalledInfoCache.CacheItem b6 = InstalledInfoCache.b(applicationInfo.packageName);
            if (b6 == null) {
                this.f22679d = applicationInfo.loadLabel(packageManager).toString();
                icon = applicationInfo.loadIcon(packageManager);
            } else {
                this.f22679d = b6.getLabel();
                icon = b6.getIcon();
            }
            this.f22680e = icon;
        } catch (Throwable th) {
            th.printStackTrace();
        }
    }

    @Override // com.loc.va.model.AppData
    public boolean a() {
        return true;
    }

    @Override // com.loc.va.model.AppData
    public boolean b() {
        return true;
    }

    @Override // com.loc.va.model.AppData
    public boolean c() {
        return true;
    }

    @Override // com.loc.va.model.AppData
    public boolean d() {
        return true;
    }

    @Override // com.loc.va.model.AppData
    public Drawable e() {
        return this.f22680e;
    }

    @Override // com.loc.va.model.AppData
    public String f() {
        return this.f22679d;
    }

    @Override // com.loc.va.model.AppData
    public String g() {
        return this.f22678c;
    }

    @Override // com.loc.va.model.AppData
    public int h() {
        return 0;
    }

    @Override // com.loc.va.model.AppData
    public boolean i() {
        return this.f22681f;
    }

    @Override // com.loc.va.model.AppData
    public boolean j() {
        return this.f22625a;
    }

    @Override // com.loc.va.model.AppData
    public boolean k() {
        return this.f22626b;
    }
}
