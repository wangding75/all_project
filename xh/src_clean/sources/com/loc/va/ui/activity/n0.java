package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.Context;
import android.content.DialogInterface;
import arm.Loader;
import com.loc.va.model.AppData;
import com.loc.va.model.AppInfoLite;
import com.loc.va.ui.activity.HomeContract;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
class n0 implements HomeContract.HomePresenter {
    private static short[] $;
    private static int[] vJ;
    private static int[] vK;
    private static int[] vL;
    private static int[] vM;
    private static int[] vN;
    private static int[] vO;
    private static int[] vP;
    private static int[] vQ;
    private static int[] vR;
    private static int[] vS;
    private static int[] vT;
    private static int[] vV;
    private static int[] vW;
    private static int[] vX;
    private static int[] vY;
    private static int[] vZ;
    private static int[] wc;
    private static int[] we;
    private static int[] wf;
    private static int[] wi;
    private static int[] wk;
    private static int[] wn;
    private static int[] wo;

    /* renamed from: a, reason: collision with root package name */
    private HomeContract.HomeView f22938a;

    /* renamed from: b, reason: collision with root package name */
    private Activity f22939b;

    /* renamed from: c, reason: collision with root package name */
    private com.loc.va.model.h f22940c;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes10.dex */
    class a {

        /* renamed from: a, reason: collision with root package name */
        private com.loc.va.model.r f22941a;

        /* renamed from: b, reason: collision with root package name */
        private int f22942b;

        static {
            Loader.registerNativesForClass(112);
            native_special_clinit0();
        }

        a() {
        }

        static native /* synthetic */ int a(a aVar);

        static native /* synthetic */ int b(a aVar, int i5);

        static native /* synthetic */ com.loc.va.model.r c(a aVar);

        static native /* synthetic */ com.loc.va.model.r d(a aVar, com.loc.va.model.r rVar);

        private static native /* synthetic */ void native_special_clinit0();
    }

    private static native String $(int i5, int i6, int i7);

    static {
        Loader.registerNativesForClass(113);
        native_special_clinit1();
    }

    n0(HomeContract.HomeView homeView) {
        this.f22938a = homeView;
        this.f22939b = homeView.d();
        this.f22940c = new com.loc.va.model.h(this.f22939b);
        this.f22938a.e(this);
    }

    public static native /* synthetic */ void a(a aVar, AppInfoLite appInfoLite, Void r22);

    public static native /* synthetic */ void b(Void r02);

    public static native /* synthetic */ void c(n0 n0Var, Throwable th);

    public static native /* synthetic */ void d(n0 n0Var, a aVar, Void r22);

    public static native /* synthetic */ void e(n0 n0Var, AppData appData);

    public static native /* synthetic */ void f(n0 n0Var, AppData appData, Void r22);

    public static native /* synthetic */ void g(Throwable th);

    public static native /* synthetic */ void h(boolean z5, DialogInterface dialogInterface, int i5);

    public static native /* synthetic */ void i(n0 n0Var, AppInfoLite appInfoLite, a aVar);

    public static native /* synthetic */ void j();

    public static native boolean k(Context context);

    private native void l(AppData appData);

    private native /* synthetic */ void m(AppInfoLite appInfoLite, a aVar);

    private static native /* synthetic */ void n(a aVar, AppInfoLite appInfoLite, Void r22);

    private static native /* synthetic */ void native_special_clinit1();

    private native /* synthetic */ void o(Throwable th);

    private native /* synthetic */ void p(a aVar, Void r22);

    private native /* synthetic */ void q(AppData appData);

    private static native /* synthetic */ void r(Throwable th);

    private static native /* synthetic */ void s(Void r02);

    private static native /* synthetic */ void t();

    private native /* synthetic */ void u(AppData appData, Void r22);

    private static native /* synthetic */ void v(boolean z5, DialogInterface dialogInterface, int i5);

    private native void w(int i5, String str);

    @Override // com.loc.va.ui.activity.HomeContract.HomePresenter
    public native void addApp(AppInfoLite appInfoLite);

    @Override // com.loc.va.ui.activity.HomeContract.HomePresenter
    @b.o0(api = 23)
    public native boolean checkExtPackageBootPermission();

    @Override // com.loc.va.ui.activity.HomeContract.HomePresenter
    public native void dataChanged();

    @Override // com.loc.va.ui.activity.HomeContract.HomePresenter
    public native void deleteApp(AppData appData);

    @Override // com.loc.va.ui.activity.HomeContract.HomePresenter
    public native void enterAppSetting(AppData appData);

    @Override // com.loc.va.ui.activity.HomeContract.HomePresenter
    public native int getAppCount();

    @Override // com.loc.va.ui.activity.HomeContract.HomePresenter
    public native String getLabel(String str);

    @Override // com.loc.va.ui.activity.HomeContract.HomePresenter
    public native void launchApp(AppData appData);

    @Override // l1.a
    public native void start();
}
