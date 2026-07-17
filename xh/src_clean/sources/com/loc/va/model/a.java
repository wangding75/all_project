package com.loc.va.model;

import android.content.Context;
import android.graphics.drawable.Drawable;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class a extends AppData {

    /* renamed from: c, reason: collision with root package name */
    private String f22633c = "";

    /* renamed from: d, reason: collision with root package name */
    private Drawable f22634d;

    public a(Context context) {
        this.f22634d = context.getResources().getDrawable(c.n.f21982p);
    }

    @Override // com.loc.va.model.AppData
    public boolean a() {
        return false;
    }

    @Override // com.loc.va.model.AppData
    public boolean b() {
        return false;
    }

    @Override // com.loc.va.model.AppData
    public boolean c() {
        return false;
    }

    @Override // com.loc.va.model.AppData
    public boolean d() {
        return false;
    }

    @Override // com.loc.va.model.AppData
    public Drawable e() {
        return this.f22634d;
    }

    @Override // com.loc.va.model.AppData
    public String f() {
        return this.f22633c;
    }

    @Override // com.loc.va.model.AppData
    public String g() {
        return null;
    }

    @Override // com.loc.va.model.AppData
    public int h() {
        return -1;
    }

    @Override // com.loc.va.model.AppData
    public boolean j() {
        return false;
    }

    @Override // com.loc.va.model.AppData
    public boolean k() {
        return false;
    }
}
