package com.loc.va.ui.activity;

import android.os.AsyncTask;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import arm.Loader;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class MeFragment extends com.loc.va.common.activity.a implements View.OnClickListener {
    private static short[] $;

    /* renamed from: s, reason: collision with root package name */
    public static String f22849s;

    /* renamed from: t, reason: collision with root package name */
    public static String f22850t;

    /* renamed from: u, reason: collision with root package name */
    public static String f22851u;
    private static int[] uS;
    private static int[] uT;
    private static int[] uY;
    private static int[] uZ;
    private static int[] va;

    /* renamed from: g, reason: collision with root package name */
    private TextView f22852g;

    /* renamed from: h, reason: collision with root package name */
    private TextView f22853h;

    /* renamed from: i, reason: collision with root package name */
    private LinearLayout f22854i;

    /* renamed from: j, reason: collision with root package name */
    private LinearLayout f22855j;

    /* renamed from: k, reason: collision with root package name */
    private LinearLayout f22856k;

    /* renamed from: l, reason: collision with root package name */
    private LinearLayout f22857l;

    /* renamed from: n, reason: collision with root package name */
    private Button f22858n;

    /* renamed from: o, reason: collision with root package name */
    private String f22859o;

    /* renamed from: p, reason: collision with root package name */
    private String f22860p;

    /* renamed from: q, reason: collision with root package name */
    private String f22861q;

    /* renamed from: r, reason: collision with root package name */
    private HomeActivity f22862r;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class a extends AsyncTask<Object, Integer, String> {
        private static short[] $;
        private static int[] Co;
        private static int[] Cp;
        private static int[] Cq;
        private static int[] Cr;
        private static int[] Cs;
        private static int[] Ct;
        private static int[] Cw;
        private static int[] Cx;
        private static int[] Cy;

        /* renamed from: a, reason: collision with root package name */
        private String f22863a;

        /* renamed from: b, reason: collision with root package name */
        private boolean f22864b;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(52);
            native_special_clinit1();
        }

        a() {
        }

        public static native /* synthetic */ void a(a aVar, String str);

        public static native /* synthetic */ void b(a aVar, String str);

        public static native /* synthetic */ void c(a aVar, String str);

        private native /* synthetic */ void e(String str);

        private native /* synthetic */ void f(String str);

        private native /* synthetic */ void g(String str);

        private static native /* synthetic */ void native_special_clinit1();

        protected native String d(Object... objArr);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ String doInBackground(Object[] objArr);

        protected native void h(String str);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ void onPostExecute(String str);

        @Override // android.os.AsyncTask
        protected native void onPreExecute();
    }

    private static native String $(int i5, int i6, int i7);

    static {
        Loader.registerNativesForClass(53);
        native_special_clinit1();
    }

    public MeFragment() {
    }

    public MeFragment(HomeActivity homeActivity) {
        this.f22862r = homeActivity;
    }

    private native String checkUpdate(String str);

    static native /* synthetic */ String l(MeFragment meFragment, String str);

    private native void m();

    private native void n();

    private static native /* synthetic */ void native_special_clinit1();

    private native void o(View view);

    private native void p(int i5);

    private native void q();

    private native void s(int i5);

    @Override // android.view.View.OnClickListener
    public native void onClick(View view);

    @Override // androidx.fragment.app.Fragment
    @b.k0
    public native View onCreateView(@b.j0 LayoutInflater layoutInflater, @b.k0 ViewGroup viewGroup, @b.k0 Bundle bundle);

    public native boolean r(String str);
}
