package com.loc.va.ui.activity;

import android.content.DialogInterface;
import android.content.Intent;
import arm.Loader;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public final /* synthetic */ class j implements DialogInterface.OnClickListener {
    private static int[] Bg;

    /* renamed from: a, reason: collision with root package name */
    public final /* synthetic */ HomeFragment f22923a;

    /* renamed from: b, reason: collision with root package name */
    public final /* synthetic */ Intent f22924b;

    static {
        Loader.registerNativesForClass(102);
        native_special_clinit0();
    }

    public /* synthetic */ j(HomeFragment homeFragment, Intent intent) {
        this.f22923a = homeFragment;
        this.f22924b = intent;
    }

    private static native /* synthetic */ void native_special_clinit0();

    @Override // android.content.DialogInterface.OnClickListener
    public final native void onClick(DialogInterface dialogInterface, int i5);
}
