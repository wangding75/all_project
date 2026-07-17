package com.loc.va.ui.activity;

import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class ActiveCardActivity extends BaseActivity {
    private static short[] $;
    private static int[] Bq;
    private static int[] Br;
    private static int[] Bs;
    private static int[] Bt;
    private static int[] Bu;
    private static int[] Bv;
    private static int[] Bw;
    private static int[] Bx;
    private static int[] By;
    private static int[] Bz;
    private Button A;
    private TextView B;
    private TextView C;
    private TextView D;

    /* renamed from: y, reason: collision with root package name */
    private ImageView f22716y;

    /* renamed from: z, reason: collision with root package name */
    private EditText f22717z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class a extends AsyncTask<String, Integer, String> {
        private static short[] $;
        private static int[] JA;
        private static int[] Jx;
        private static int[] Jz;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(1);
            native_special_clinit1();
        }

        a() {
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
    class b implements Runnable {
        private static short[] $;
        private static int[] KS;

        /* renamed from: a, reason: collision with root package name */
        int f22719a;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(2);
            native_special_clinit1();
        }

        public b(int i5) {
            this.f22719a = i5;
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // java.lang.Runnable
        public native void run();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class c extends AsyncTask<String, Integer, String> {
        private static short[] $;
        private static int[] KZ;
        private static int[] Lb;
        private static int[] Lc;

        /* renamed from: a, reason: collision with root package name */
        private String f22721a;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(3);
            native_special_clinit1();
        }

        c() {
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
    class d extends AsyncTask<String, Integer, String> {
        private static short[] $;
        private static int[] Kw;
        private static int[] Ky;
        private static int[] Kz;

        /* renamed from: a, reason: collision with root package name */
        private String f22723a;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(4);
            native_special_clinit1();
        }

        d() {
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

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(8631);
        Loader.registerNativesForClass(5);
        native_special_clinit1();
    }

    static native /* synthetic */ String C0(ActiveCardActivity activeCardActivity, String str);

    static native /* synthetic */ int D0(ActiveCardActivity activeCardActivity);

    static native /* synthetic */ TextView E0(ActiveCardActivity activeCardActivity);

    static native /* synthetic */ String F0(ActiveCardActivity activeCardActivity, String str, String str2);

    static native /* synthetic */ String G0(ActiveCardActivity activeCardActivity, String str);

    private native void H0();

    private native void J0();

    private native void K0();

    private native Intent L0();

    private native String active(String str, String str2);

    private native String gie();

    private native int gnode();

    private native String info(String str);

    private static native /* synthetic */ void native_special_clinit1();

    private native String sign(String str);

    public native void I0();

    public native void kefu(View view);

    public native void login(View view);

    @Override // androidx.activity.ComponentActivity, android.app.Activity
    public native void onBackPressed();

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, android.app.Activity
    public native void onRequestPermissionsResult(int i5, @b.j0 String[] strArr, @b.j0 int[] iArr);
}
