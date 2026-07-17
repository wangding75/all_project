package com.hjq.toast;

import android.app.Application;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
final class f extends a {

    /* renamed from: b, reason: collision with root package name */
    private final h f20853b;

    f(Application application) {
        super(application);
        this.f20853b = new h(this, application);
    }

    @Override // android.widget.Toast
    public void cancel() {
        this.f20853b.a();
    }

    @Override // android.widget.Toast
    public void show() {
        this.f20853b.b();
    }
}
