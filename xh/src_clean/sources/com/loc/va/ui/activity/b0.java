package com.loc.va.ui.activity;

import arm.Loader;
import com.loc.va.model.AppInfoLite;
import com.loc.va.ui.activity.n0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public final /* synthetic */ class b0 implements Runnable {
    private static int[] pk;

    /* renamed from: a, reason: collision with root package name */
    public final /* synthetic */ n0 f22895a;

    /* renamed from: b, reason: collision with root package name */
    public final /* synthetic */ AppInfoLite f22896b;

    /* renamed from: c, reason: collision with root package name */
    public final /* synthetic */ n0.a f22897c;

    static {
        Loader.registerNativesForClass(76);
        native_special_clinit0();
    }

    public /* synthetic */ b0(n0 n0Var, AppInfoLite appInfoLite, n0.a aVar) {
        this.f22895a = n0Var;
        this.f22896b = appInfoLite;
        this.f22897c = aVar;
    }

    private static native /* synthetic */ void native_special_clinit0();

    @Override // java.lang.Runnable
    public final native void run();
}
