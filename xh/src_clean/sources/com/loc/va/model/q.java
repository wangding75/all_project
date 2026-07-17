package com.loc.va.model;

import android.graphics.drawable.Drawable;
import com.lody.virtual.remote.InstalledAppInfo;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class q extends AppData {

    /* renamed from: c, reason: collision with root package name */
    public InstalledAppInfo f22673c;

    /* renamed from: d, reason: collision with root package name */
    public int f22674d;

    /* renamed from: e, reason: collision with root package name */
    public Drawable f22675e;

    /* renamed from: f, reason: collision with root package name */
    public String f22676f;

    /* renamed from: g, reason: collision with root package name */
    public String f22677g;

    public q(r rVar, int i5) {
        Drawable.ConstantState constantState;
        this.f22674d = i5;
        this.f22673c = com.lody.virtual.client.core.j.h().v(rVar.f22678c, 0);
        this.f22625a = !r0.u(i5);
        Drawable drawable = rVar.f22680e;
        if (drawable != null && (constantState = drawable.getConstantState()) != null) {
            this.f22675e = constantState.newDrawable();
        }
        this.f22676f = rVar.f22679d;
        this.f22677g = rVar.f22678c;
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
        return this.f22675e;
    }

    @Override // com.loc.va.model.AppData
    public String f() {
        return this.f22676f;
    }

    @Override // com.loc.va.model.AppData
    public String g() {
        return this.f22677g;
    }

    @Override // com.loc.va.model.AppData
    public int h() {
        return this.f22674d;
    }

    @Override // com.loc.va.model.AppData
    public boolean i() {
        return this.f22673c.f24697g;
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
