package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Outline;
import android.os.AsyncTask;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewOutlineProvider;
import android.widget.CompoundButton;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.Switch;
import android.widget.TextView;
import androidx.constraintlayout.widget.ConstraintLayout;
import androidx.recyclerview.widget.RecyclerView;
import arm.Loader;
import com.loc.va.model.AppData;
import com.loc.va.ui.activity.HomeContract;
import com.loc.va.ui.widget.dialog.c;
import com.youth.banner.Banner;
import com.youth.banner.adapter.BannerImageAdapter;
import com.youth.banner.holder.BannerImageHolder;
import com.youth.banner.listener.OnBannerListener;
import java.util.ArrayList;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class HomeFragment extends com.loc.va.common.activity.a implements HomeContract.HomeView, View.OnClickListener, CompoundButton.OnCheckedChangeListener, OnBannerListener {
    private static short[] $;
    private static String V;
    public static boolean W;
    public static boolean X;
    public static int Y;
    public static AppData Z;
    private static int[] lD;
    private static int[] lG;
    private static int[] lK;
    private static int[] lO;
    private static int[] lQ;
    private static int[] lX;
    private static int[] mA;
    private static int[] mB;
    private static int[] mC;
    private static int[] mD;
    private static int[] mE;
    private static int[] mF;
    private static int[] mG;
    private static int[] mH;
    private static int[] mJ;
    private static int[] mK;
    private static int[] mL;
    private static int[] mN;
    private static int[] mO;
    private static int[] mP;
    private static int[] mR;
    private static int[] mS;
    private static int[] mT;
    private static int[] mV;
    private static int[] mW;
    private static int[] mY;
    private static int[] mZ;
    private static int[] mt;
    private static int[] mv;
    private static int[] mw;
    private static int[] mx;
    private static int[] my;
    private static int[] mz;
    private static int[] nc;
    private static int[] nd;
    private static int[] ne;
    private static int[] nf;
    private static int[] ng;
    private static int[] nh;
    private static int[] ni;
    private static int[] nj;
    private static int[] nk;
    private static int[] nl;
    private static int[] nm;
    private static int[] nn;
    private static int[] no;
    private static int[] nq;
    private static int[] nr;
    private ArrayList<Integer> A = new ArrayList<>();
    private ArrayList<String> B = new ArrayList<>();
    private ArrayList<String> C = new ArrayList<>();
    private ArrayList<String> D = new ArrayList<>();
    private ArrayList<Integer> E = new ArrayList<>();
    private LinearLayout F;
    private LinearLayout G;
    private LinearLayout H;
    private LinearLayout I;
    private LinearLayout J;
    private LinearLayout K;
    private LinearLayout L;
    private TextView M;
    private TextView N;
    private TextView O;
    private TextView P;
    private com.loc.va.ui.adapters.q Q;
    private String R;
    private String S;
    private String T;
    private HomeActivity U;

    /* renamed from: g, reason: collision with root package name */
    private com.google.android.material.bottomsheet.a f22742g;

    /* renamed from: h, reason: collision with root package name */
    private View f22743h;

    /* renamed from: i, reason: collision with root package name */
    private RecyclerView f22744i;

    /* renamed from: j, reason: collision with root package name */
    private ConstraintLayout f22745j;

    /* renamed from: k, reason: collision with root package name */
    private TextView f22746k;

    /* renamed from: l, reason: collision with root package name */
    private TextView f22747l;

    /* renamed from: m, reason: collision with root package name */
    private HomeContract.HomePresenter f22748m;

    /* renamed from: n, reason: collision with root package name */
    private ImageButton f22749n;

    /* renamed from: o, reason: collision with root package name */
    private String f22750o;

    /* renamed from: p, reason: collision with root package name */
    private Switch f22751p;

    /* renamed from: q, reason: collision with root package name */
    private Switch f22752q;

    /* renamed from: r, reason: collision with root package name */
    private Switch f22753r;

    /* renamed from: s, reason: collision with root package name */
    private Switch f22754s;

    /* renamed from: t, reason: collision with root package name */
    private Switch f22755t;

    /* renamed from: u, reason: collision with root package name */
    private Switch f22756u;

    /* renamed from: v, reason: collision with root package name */
    private TextView f22757v;

    /* renamed from: w, reason: collision with root package name */
    private TextView f22758w;

    /* renamed from: x, reason: collision with root package name */
    private TextView f22759x;

    /* renamed from: y, reason: collision with root package name */
    private TextView f22760y;

    /* renamed from: z, reason: collision with root package name */
    private Banner f22761z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class a extends ViewOutlineProvider {
        static {
            Loader.registerNativesForClass(21);
            native_special_clinit0();
        }

        a() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // android.view.ViewOutlineProvider
        public native void getOutline(View view, Outline outline);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class b implements c.e {
        private static short[] $;
        private static int[] Qd;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(22);
            native_special_clinit1();
        }

        b() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // com.loc.va.ui.widget.dialog.c.e
        public native void a();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class c implements c.d {
        static {
            Loader.registerNativesForClass(23);
            native_special_clinit0();
        }

        c() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // com.loc.va.ui.widget.dialog.c.d
        public native void a();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class d implements c.e {
        static {
            Loader.registerNativesForClass(24);
            native_special_clinit0();
        }

        d() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // com.loc.va.ui.widget.dialog.c.e
        public native void a();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class e implements c.d {
        static {
            Loader.registerNativesForClass(25);
            native_special_clinit0();
        }

        e() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // com.loc.va.ui.widget.dialog.c.d
        public native void a();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class f extends AsyncTask<Object, Integer, String> {
        private static short[] $;
        private static int[] QA;
        private static int[] QB;
        private static int[] QC;
        private static int[] QD;
        private static int[] QE;
        private static int[] QH;
        private static int[] QI;
        private static int[] QJ;
        private static int[] Qz;

        /* renamed from: a, reason: collision with root package name */
        private String f22767a;

        /* renamed from: b, reason: collision with root package name */
        private boolean f22768b;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(26);
            native_special_clinit1();
        }

        f() {
        }

        public static native /* synthetic */ void a(f fVar, String str);

        public static native /* synthetic */ void b(f fVar, String str);

        public static native /* synthetic */ void c(f fVar, String str);

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

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class g extends AsyncTask<String, Integer, String> {
        private static short[] $;
        private static int[] OZ;
        private static int[] Pb;
        private static int[] Pc;

        /* renamed from: a, reason: collision with root package name */
        private String f22770a;

        /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
        /* compiled from: fuck */
        class a extends BannerImageAdapter<String> {
            private static int[] tr;
            private static int[] ts;

            static {
                Loader.registerNativesForClass(27);
                native_special_clinit0();
            }

            a(List list) {
                super(list);
            }

            private static native /* synthetic */ void native_special_clinit0();

            public native void b(BannerImageHolder bannerImageHolder, String str, int i5, int i6);

            @Override // com.youth.banner.holder.IViewHolder
            public native /* bridge */ /* synthetic */ void onBindView(Object obj, Object obj2, int i5, int i6);
        }

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(28);
            native_special_clinit1();
        }

        g() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        protected native String a(String... strArr);

        protected native void b(String str);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ String doInBackground(String[] strArr);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ void onPostExecute(String str);

        @Override // android.os.AsyncTask
        protected native void onPreExecute();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class h extends AsyncTask<Object, Integer, byte[]> {
        private static short[] $;
        private static int[] Pj;
        private static int[] Pl;
        private static int[] Pm;

        /* renamed from: a, reason: collision with root package name */
        private String f22773a;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(29);
            native_special_clinit1();
        }

        h() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        protected native byte[] a(Object... objArr);

        protected native void b(byte[] bArr);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ byte[] doInBackground(Object[] objArr);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ void onPostExecute(byte[] bArr);

        @Override // android.os.AsyncTask
        protected native void onPreExecute();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class i extends AsyncTask<Object, Integer, String> {
        private static short[] $;
        private static int[] Oo;
        private static int[] Op;
        private static int[] Or;
        private static int[] Ot;
        private static int[] Ou;

        /* renamed from: a, reason: collision with root package name */
        String f22775a;

        /* renamed from: b, reason: collision with root package name */
        String f22776b;

        /* renamed from: c, reason: collision with root package name */
        String f22777c;

        /* renamed from: d, reason: collision with root package name */
        String f22778d;

        /* renamed from: e, reason: collision with root package name */
        int f22779e;

        /* renamed from: f, reason: collision with root package name */
        String f22780f;

        /* renamed from: g, reason: collision with root package name */
        double f22781g;

        /* renamed from: h, reason: collision with root package name */
        double f22782h;

        /* renamed from: i, reason: collision with root package name */
        String f22783i;

        /* renamed from: j, reason: collision with root package name */
        double f22784j;

        /* renamed from: k, reason: collision with root package name */
        double f22785k;

        /* renamed from: l, reason: collision with root package name */
        String f22786l;

        /* renamed from: m, reason: collision with root package name */
        String f22787m;

        /* renamed from: n, reason: collision with root package name */
        String f22788n;

        /* renamed from: o, reason: collision with root package name */
        String f22789o;

        /* renamed from: p, reason: collision with root package name */
        String f22790p;

        /* renamed from: q, reason: collision with root package name */
        AppData f22791q;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(30);
            native_special_clinit1();
        }

        i() {
        }

        public static native /* synthetic */ void a(i iVar);

        private native /* synthetic */ void c();

        private static native /* synthetic */ void native_special_clinit1();

        protected native String b(Object... objArr);

        protected native void d(String str);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ String doInBackground(Object[] objArr);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ void onPostExecute(String str);

        @Override // android.os.AsyncTask
        protected native void onPreExecute();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class j extends AsyncTask<Object, Integer, String> {
        private static short[] $;
        private static int[] OD;
        private static int[] OE;
        private static int[] OG;
        private static int[] OI;
        private static int[] OJ;

        /* renamed from: a, reason: collision with root package name */
        String f22793a;

        /* renamed from: b, reason: collision with root package name */
        String f22794b;

        /* renamed from: c, reason: collision with root package name */
        String f22795c;

        /* renamed from: d, reason: collision with root package name */
        String f22796d;

        /* renamed from: e, reason: collision with root package name */
        int f22797e;

        /* renamed from: f, reason: collision with root package name */
        String f22798f;

        /* renamed from: g, reason: collision with root package name */
        double f22799g;

        /* renamed from: h, reason: collision with root package name */
        double f22800h;

        /* renamed from: i, reason: collision with root package name */
        String f22801i;

        /* renamed from: j, reason: collision with root package name */
        double f22802j;

        /* renamed from: k, reason: collision with root package name */
        double f22803k;

        /* renamed from: l, reason: collision with root package name */
        String f22804l;

        /* renamed from: m, reason: collision with root package name */
        String f22805m;

        /* renamed from: n, reason: collision with root package name */
        String f22806n;

        /* renamed from: o, reason: collision with root package name */
        String f22807o;

        /* renamed from: p, reason: collision with root package name */
        AppData f22808p;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(31);
            native_special_clinit1();
        }

        j() {
        }

        public static native /* synthetic */ void a(j jVar);

        private native /* synthetic */ void c();

        private static native /* synthetic */ void native_special_clinit1();

        protected native String b(Object... objArr);

        protected native void d(String str);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ String doInBackground(Object[] objArr);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ void onPostExecute(String str);

        @Override // android.os.AsyncTask
        protected native void onPreExecute();
    }

    private static native String $(int i5, int i6, int i7);

    static {
        Loader.registerNativesForClass(32);
        native_special_clinit1();
    }

    public HomeFragment() {
    }

    public HomeFragment(HomeActivity homeActivity) {
        this.U = homeActivity;
    }

    public static native /* synthetic */ void A(HomeFragment homeFragment, View view, int i5, AppData appData);

    private static native /* synthetic */ void A0();

    static native /* synthetic */ HomeContract.HomePresenter B(HomeFragment homeFragment);

    private native /* synthetic */ void B0(int i5, String str);

    static native /* synthetic */ String C(HomeFragment homeFragment, String str);

    private static native /* synthetic */ void C0();

    static native /* synthetic */ LinearLayout D(HomeFragment homeFragment);

    private native /* synthetic */ void D0(int i5, String str);

    static native /* synthetic */ LinearLayout E(HomeFragment homeFragment);

    private static native /* synthetic */ void E0();

    static native /* synthetic */ LinearLayout F(HomeFragment homeFragment);

    private native /* synthetic */ void F0(DialogInterface dialogInterface, int i5);

    static native /* synthetic */ LinearLayout G(HomeFragment homeFragment);

    private native /* synthetic */ void G0(Intent intent, DialogInterface dialogInterface, int i5);

    static native /* synthetic */ LinearLayout H(HomeFragment homeFragment);

    static native /* synthetic */ String I(HomeFragment homeFragment);

    static native /* synthetic */ String J(HomeFragment homeFragment, String str);

    static native /* synthetic */ ConstraintLayout K(HomeFragment homeFragment);

    static native /* synthetic */ TextView L(HomeFragment homeFragment);

    static native /* synthetic */ TextView M(HomeFragment homeFragment);

    static native /* synthetic */ void N(HomeFragment homeFragment);

    static native /* synthetic */ ArrayList O(HomeFragment homeFragment);

    static native /* synthetic */ String P(HomeFragment homeFragment, String str);

    static native /* synthetic */ String Q(HomeFragment homeFragment, String str, String str2, String str3, String str4, int i5, String str5, double d6, double d7, String str6, double d8, double d9, String str7, String str8, String str9, String str10, AppData appData);

    static native /* synthetic */ String R(HomeFragment homeFragment, String str, String str2, String str3, String str4, int i5, String str5, double d6, double d7, String str6, double d8, double d9, String str7, String str8, String str9, String str10, String str11, AppData appData);

    static native /* synthetic */ String S(HomeFragment homeFragment);

    static native /* synthetic */ String T(HomeFragment homeFragment);

    static native /* synthetic */ String U(HomeFragment homeFragment);

    static native /* synthetic */ String V(HomeFragment homeFragment);

    static native /* synthetic */ String W(HomeFragment homeFragment);

    static native /* synthetic */ String X(HomeFragment homeFragment, String str, String str2, String str3, String str4, int i5, String str5, double d6, double d7, String str6, double d8, double d9, String str7, String str8, String str9, String str10, String str11, AppData appData);

    static native /* synthetic */ com.loc.va.ui.adapters.q Y(HomeFragment homeFragment);

    static native /* synthetic */ ArrayList Z(HomeFragment homeFragment);

    static native /* synthetic */ byte[] a0(HomeFragment homeFragment, String str);

    static native /* synthetic */ ArrayList b0(HomeFragment homeFragment);

    static native /* synthetic */ ArrayList c0(HomeFragment homeFragment);

    private native String checkUpdate(String str);

    static native /* synthetic */ ArrayList d0(HomeFragment homeFragment);

    static native /* synthetic */ Banner e0(HomeFragment homeFragment);

    static native /* synthetic */ LinearLayout f0(HomeFragment homeFragment);

    static native /* synthetic */ LinearLayout g0(HomeFragment homeFragment);

    private native String getInfos(String str);

    private native String getie();

    private native String getis();

    private native String getm();

    private native String gets();

    private native void h0();

    private native void i0(String str);

    private native void j0();

    private native void k0();

    public static native /* synthetic */ void l(HomeFragment homeFragment, int i5, String str);

    private native void l0();

    private native byte[] loaddd(String str);

    private native String lsa(String str, String str2, String str3, String str4, int i5, String str5, double d6, double d7, String str6, double d8, double d9, String str7, String str8, String str9, String str10, String str11, AppData appData);

    private native String lsc(String str, String str2, String str3, String str4, int i5, String str5, double d6, double d7, String str6, double d8, double d9, String str7, String str8, String str9, String str10, String str11, AppData appData);

    private native String lsget(String str, String str2, String str3, String str4, int i5, String str5, double d6, double d7, String str6, double d8, double d9, String str7, String str8, String str9, String str10, AppData appData);

    public static native /* synthetic */ void m();

    private native void m0();

    public static native /* synthetic */ void n();

    private native void n0();

    private static native /* synthetic */ void native_special_clinit1();

    public static native /* synthetic */ void o(HomeFragment homeFragment, int i5, String str);

    private native void o0(View view);

    public static native /* synthetic */ void p();

    public static native /* synthetic */ void q(View view, int i5, AppData appData);

    public static native /* synthetic */ void r();

    private native /* synthetic */ void r0(View view, int i5, AppData appData);

    public static native /* synthetic */ void s(HomeFragment homeFragment, int i5, String str);

    private static native /* synthetic */ void s0(View view, int i5, AppData appData);

    public static native /* synthetic */ void t(HomeFragment homeFragment, int i5, String str);

    private native /* synthetic */ void t0(int i5, String str);

    public static native /* synthetic */ void u(HomeFragment homeFragment, int i5, String str);

    private static native /* synthetic */ void u0();

    public static native /* synthetic */ void v(HomeFragment homeFragment, Intent intent, DialogInterface dialogInterface, int i5);

    private native /* synthetic */ void v0(int i5, String str);

    public static native /* synthetic */ void w(HomeFragment homeFragment, int i5, String str);

    private static native /* synthetic */ void w0();

    public static native /* synthetic */ void x();

    private native /* synthetic */ void x0(int i5, String str);

    public static native /* synthetic */ void y(HomeFragment homeFragment, DialogInterface dialogInterface, int i5);

    private static native /* synthetic */ void y0();

    public static native /* synthetic */ void z();

    private native /* synthetic */ void z0(int i5, String str);

    public native void H0(HomeContract.HomePresenter homePresenter);

    @Override // com.youth.banner.listener.OnBannerListener
    public native void OnBannerClick(Object obj, int i5);

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void addAppToLauncher(AppData appData);

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void askInstallGms();

    @Override // l1.b
    @b.k0
    public native /* bridge */ /* synthetic */ Activity d();

    @Override // l1.b
    public native /* bridge */ /* synthetic */ void e(HomeContract.HomePresenter homePresenter);

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void hideBottomAction();

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void loadError(Throwable th);

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void loadFinish(List<AppData> list);

    @Override // androidx.fragment.app.Fragment
    public native void onActivityResult(int i5, int i6, @b.k0 Intent intent);

    @Override // android.widget.CompoundButton.OnCheckedChangeListener
    public native void onCheckedChanged(CompoundButton compoundButton, boolean z5);

    @Override // android.view.View.OnClickListener
    public native void onClick(View view);

    @Override // androidx.fragment.app.Fragment
    @b.k0
    public native View onCreateView(@b.j0 LayoutInflater layoutInflater, @b.k0 ViewGroup viewGroup, @b.k0 Bundle bundle);

    public native void p0(View view);

    public native void q0();

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void refreshLauncherItem(AppData appData);

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void removeAppToLauncher(AppData appData);

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void showBottomAction();

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void showGuide();

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void showOverlayPermissionDialog();

    @Override // com.loc.va.ui.activity.HomeContract.HomeView
    public native void showPermissionDialog();
}
