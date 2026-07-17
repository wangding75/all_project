package com.loc.va;

import android.app.Application;
import android.content.Context;
import io.busniess.va.common.CommonApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class App extends Application {

    /* renamed from: b, reason: collision with root package name */
    private static App f20937b;

    /* renamed from: a, reason: collision with root package name */
    CommonApp f20938a = new CommonApp();

    public static App a() {
        return f20937b;
    }

    @Override // android.content.ContextWrapper
    protected void attachBaseContext(Context context) {
        super.attachBaseContext(context);
        f20937b = this;
        this.f20938a.attachBaseContext(context);
    }

    @Override // android.app.Application
    public void onCreate() {
        super.onCreate();
        this.f20938a.onCreate(this);
    }
}
