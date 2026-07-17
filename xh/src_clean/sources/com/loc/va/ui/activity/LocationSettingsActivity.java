package com.loc.va.ui.activity;

import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import arm.Loader;
import com.baidu.location.BDAbstractLocationListener;
import com.baidu.location.BDLocation;
import com.baidu.location.LocationClient;
import com.baidu.mapapi.map.BaiduMap;
import com.baidu.mapapi.map.MapPoi;
import com.baidu.mapapi.map.MapView;
import com.baidu.mapapi.map.Marker;
import com.baidu.mapapi.model.LatLng;
import com.baidu.mapapi.search.geocode.GeoCodeResult;
import com.baidu.mapapi.search.geocode.GeoCoder;
import com.baidu.mapapi.search.geocode.OnGetGeoCoderResultListener;
import com.baidu.mapapi.search.geocode.ReverseGeoCodeResult;
import com.loc.va.common.activity.BaseActivity;
import com.loc.va.ui.widget.dialog.c;
import com.lody.virtual.remote.vloc.VLocation;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class LocationSettingsActivity extends BaseActivity {
    private static short[] $;
    private static int[] LP;
    private static int[] LR;
    private static int[] LS;
    private static int[] LT;
    private static int[] LU;
    private static int[] LV;
    private static int[] LW;
    private static int[] LY;
    private static int[] MA;
    private static int[] MB;
    private static int[] MC;
    private static int[] MD;
    private static int[] ME;
    private static int[] MF;
    private static int[] MG;
    private static int[] MH;
    private static int[] MI;
    private static int[] MJ;
    private static int[] MK;
    private static int[] ML;
    private static int[] MM;
    private static int[] MO;
    private static int[] MP;
    private static int[] MQ;
    private static int[] MR;
    private static int[] MS;
    private static int[] MT;
    private static int[] MU;
    private static int[] MV;
    private static int[] MW;
    private static int[] MX;
    private static int[] MY;
    private static int[] MZ;
    private static int[] Ma;
    private static int[] Mb;
    private static int[] Mc;
    private static int[] Md;
    private static int[] Me;
    private static int[] Mf;
    private static int[] Mi;
    private static int[] Mw;

    /* renamed from: w0, reason: collision with root package name */
    private static String f22824w0;

    /* renamed from: x0, reason: collision with root package name */
    private static boolean f22825x0;

    /* renamed from: y0, reason: collision with root package name */
    private static boolean f22826y0;
    private ImageButton A;
    private ImageButton B;
    private ImageButton C;
    private Button D;
    private EditText E;
    private LinearLayout F;
    private LinearLayout G;
    private LinearLayout H;
    private CheckBox I;
    private EditText J;
    private EditText K;
    private EditText L;
    private EditText M;
    private RadioGroup N;
    private RadioButton O;
    private RadioButton P;
    private RadioButton Q;
    private RadioButton R;
    private RadioButton S;
    private MapView T;
    private BaiduMap U;
    private Marker V;
    private f W;
    private GeoCoder X;
    private OnGetGeoCoderResultListener Y;
    private LocationClient Z;

    /* renamed from: i0, reason: collision with root package name */
    private LatLng f22827i0;

    /* renamed from: j0, reason: collision with root package name */
    private String f22828j0;

    /* renamed from: m0, reason: collision with root package name */
    private com.loc.va.ui.widget.t f22831m0;

    /* renamed from: o0, reason: collision with root package name */
    private SQLiteDatabase f22833o0;

    /* renamed from: p0, reason: collision with root package name */
    private o1.a f22834p0;

    /* renamed from: q0, reason: collision with root package name */
    private String f22835q0;

    /* renamed from: r0, reason: collision with root package name */
    private String f22836r0;

    /* renamed from: s0, reason: collision with root package name */
    private int f22837s0;

    /* renamed from: t0, reason: collision with root package name */
    private String f22838t0;

    /* renamed from: u0, reason: collision with root package name */
    private VLocation f22839u0;

    /* renamed from: y, reason: collision with root package name */
    private LinearLayout f22841y;

    /* renamed from: z, reason: collision with root package name */
    private ImageButton f22842z;

    /* renamed from: k0, reason: collision with root package name */
    private String f22829k0 = $(0, 24, 5399);

    /* renamed from: l0, reason: collision with root package name */
    private com.loc.va.model.p f22830l0 = new com.loc.va.model.p();

    /* renamed from: n0, reason: collision with root package name */
    private boolean f22832n0 = true;

    /* renamed from: v0, reason: collision with root package name */
    private int f22840v0 = -1;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class a implements BaiduMap.OnMapClickListener {
        private static short[] $;
        private static int[] qA;
        private static int[] qz;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(44);
            native_special_clinit1();
        }

        a() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // com.baidu.mapapi.map.BaiduMap.OnMapClickListener
        public native void onMapClick(LatLng latLng);

        @Override // com.baidu.mapapi.map.BaiduMap.OnMapClickListener
        public native void onMapPoiClick(MapPoi mapPoi);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class b implements OnGetGeoCoderResultListener {
        private static short[] $;
        private static int[] qf;
        private static int[] qg;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(45);
            native_special_clinit1();
        }

        b() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // com.baidu.mapapi.search.geocode.OnGetGeoCoderResultListener
        public native void onGetGeoCodeResult(GeoCodeResult geoCodeResult);

        @Override // com.baidu.mapapi.search.geocode.OnGetGeoCoderResultListener
        public native void onGetReverseGeoCodeResult(ReverseGeoCodeResult reverseGeoCodeResult);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class c implements c.e {
        static {
            Loader.registerNativesForClass(46);
            native_special_clinit0();
        }

        c() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // com.loc.va.ui.widget.dialog.c.e
        public native void a();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class d implements c.d {
        static {
            Loader.registerNativesForClass(47);
            native_special_clinit0();
        }

        d() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // com.loc.va.ui.widget.dialog.c.d
        public native void a();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class e implements c.InterfaceC0214c {
        private static short[] $;
        private static int[] qs;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(48);
            native_special_clinit1();
        }

        e() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // com.loc.va.ui.widget.dialog.c.InterfaceC0214c
        public native void a(String str);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public class f extends BDAbstractLocationListener {
        private static int[] rw;

        static {
            Loader.registerNativesForClass(49);
            native_special_clinit0();
        }

        public f() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // com.baidu.location.BDAbstractLocationListener
        public native void onReceiveLocation(BDLocation bDLocation);
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(8648);
        Loader.registerNativesForClass(50);
        native_special_clinit1();
    }

    private static native /* synthetic */ void A1();

    private static native /* synthetic */ void B1();

    public static native /* synthetic */ void C0(LocationSettingsActivity locationSettingsActivity, View view);

    private static native /* synthetic */ void C1();

    public static native /* synthetic */ void D0(LocationSettingsActivity locationSettingsActivity);

    private native boolean D1(View view);

    public static native /* synthetic */ void E0();

    public static native /* synthetic */ void F0(LocationSettingsActivity locationSettingsActivity, View view);

    private native void F1();

    public static native /* synthetic */ void G0(LocationSettingsActivity locationSettingsActivity, View view);

    private native void G1();

    public static native /* synthetic */ void H0();

    private native void H1();

    public static native /* synthetic */ void I0(LocationSettingsActivity locationSettingsActivity, View view);

    public static native /* synthetic */ void J0(LocationSettingsActivity locationSettingsActivity, View view);

    public static native /* synthetic */ void K0(LocationSettingsActivity locationSettingsActivity, View view);

    public static native /* synthetic */ void L0();

    public static native /* synthetic */ void M0(LocationSettingsActivity locationSettingsActivity, View view);

    public static native /* synthetic */ void N0(LocationSettingsActivity locationSettingsActivity, View view);

    static native /* synthetic */ LatLng P0(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ LatLng Q0(LocationSettingsActivity locationSettingsActivity, LatLng latLng);

    static native /* synthetic */ void R0(LocationSettingsActivity locationSettingsActivity, LatLng latLng);

    static native /* synthetic */ boolean S0();

    static native /* synthetic */ CheckBox T0(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ LinearLayout U0(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ LinearLayout V0(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ MapView W0(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ BaiduMap X0(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ EditText Y0(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ String Z0(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ String a1(LocationSettingsActivity locationSettingsActivity, String str);

    static native /* synthetic */ GeoCoder b1(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ com.loc.va.model.p c1(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ boolean d1(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ boolean e1(LocationSettingsActivity locationSettingsActivity, boolean z5);

    static native /* synthetic */ void f1(LocationSettingsActivity locationSettingsActivity);

    static native /* synthetic */ boolean g1();

    static native /* synthetic */ boolean h1(boolean z5);

    static native /* synthetic */ VLocation i1(LocationSettingsActivity locationSettingsActivity);

    private native void k1(LatLng latLng);

    private native void l1(View view);

    private native void m1(View view);

    private native void n1(View view);

    private static native /* synthetic */ void native_special_clinit1();

    private native void o1(View view);

    private native void p1(View view);

    private native void q1(View view);

    private native void r1(View view);

    private native void s1(View view);

    private native SQLiteDatabase t1();

    private native void u1();

    private native void v1();

    private native void w1();

    private native boolean y1();

    private native /* synthetic */ void z1();

    public native void E1(RadioGroup radioGroup, int i5);

    public native void O0();

    public native void j1(String str, String str2, String str3);

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, android.app.Activity
    protected native void onActivityResult(int i5, int i6, Intent intent);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, android.app.Activity
    protected native void onDestroy();

    @Override // androidx.fragment.app.FragmentActivity, android.app.Activity
    protected native void onPause();

    @Override // android.app.Activity
    protected native void onRestart();

    @Override // androidx.fragment.app.FragmentActivity, android.app.Activity
    protected native void onResume();

    @Override // androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, android.app.Activity
    protected native void onStop();

    public native boolean x1();
}
