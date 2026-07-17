package com.loc.va.ui.activity;

import arm.Loader;
import com.loc.va.model.AppData;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public final /* synthetic */ class m0 implements Runnable {
    private static int[] tu;

    /* renamed from: a, reason: collision with root package name */
    public final /* synthetic */ n0 f22933a;

    /* renamed from: b, reason: collision with root package name */
    public final /* synthetic */ AppData f22934b;

    static {
        Loader.registerNativesForClass(109);
        native_special_clinit0();
    }

    public /* synthetic */ m0(n0 n0Var, AppData appData) {
        this.f22933a = n0Var;
        this.f22934b = appData;
    }

    private static native /* synthetic */ void native_special_clinit0();

    @Override // java.lang.Runnable
    public final native void run();
}
