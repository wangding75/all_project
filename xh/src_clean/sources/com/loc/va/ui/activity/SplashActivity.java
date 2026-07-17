package com.loc.va.ui.activity;

import android.os.AsyncTask;
import android.os.Bundle;
import android.text.TextPaint;
import android.text.style.ClickableSpan;
import android.text.style.UnderlineSpan;
import android.view.View;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class SplashActivity extends BaseActivity {
    private static short[] $;
    private static int[] LA;
    private static int[] LB;
    private static int[] LD;
    private static int[] LE;
    private static int[] LF;
    private static int[] LG;
    private static int[] LH;
    private static int[] Lz;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* renamed from: com.loc.va.ui.activity.SplashActivity$4, reason: invalid class name */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class AnonymousClass4 extends UnderlineSpan {
        private static short[] $;
        private static int[] vf;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(55);
            native_special_clinit1();
        }

        AnonymousClass4() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // android.text.style.UnderlineSpan, android.text.style.CharacterStyle
        public native void updateDrawState(TextPaint textPaint);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* renamed from: com.loc.va.ui.activity.SplashActivity$5, reason: invalid class name */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class AnonymousClass5 extends UnderlineSpan {
        private static short[] $;
        private static int[] vn;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(56);
            native_special_clinit1();
        }

        AnonymousClass5() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // android.text.style.UnderlineSpan, android.text.style.CharacterStyle
        public native void updateDrawState(TextPaint textPaint);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class a implements Runnable {
        private static int[] Jk;

        static {
            Loader.registerNativesForClass(57);
            native_special_clinit0();
        }

        a() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // java.lang.Runnable
        public native void run();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class b extends ClickableSpan {
        private static short[] $;
        private static int[] Kc;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(58);
            native_special_clinit1();
        }

        b() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // android.text.style.ClickableSpan
        public native void onClick(@b.j0 View view);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* compiled from: fuck */
    class c extends ClickableSpan {
        private static short[] $;
        private static int[] JF;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(59);
            native_special_clinit1();
        }

        c() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // android.text.style.ClickableSpan
        public native void onClick(@b.j0 View view);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class d extends AsyncTask<String, Integer, String> {
        private static short[] $;
        private static int[] Nc;
        private static int[] Nd;
        private static int[] Ne;
        private static int[] Nf;
        private static int[] Ng;
        private static int[] Ni;
        private static int[] Nj;
        private static int[] Nk;

        /* renamed from: a, reason: collision with root package name */
        private String f22873a;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(60);
            native_special_clinit1();
        }

        d() {
        }

        public static native /* synthetic */ void a(d dVar);

        public static native /* synthetic */ void b(d dVar);

        private native /* synthetic */ void d();

        private native /* synthetic */ void e();

        private static native /* synthetic */ void native_special_clinit1();

        protected native String c(String... strArr);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ String doInBackground(String[] strArr);

        protected native void f(String str);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ void onPostExecute(String str);

        @Override // android.os.AsyncTask
        protected native void onPreExecute();
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(8650);
        Loader.registerNativesForClass(61);
        native_special_clinit1();
    }

    public static native /* synthetic */ void C0(SplashActivity splashActivity);

    public static native /* synthetic */ void D0(SplashActivity splashActivity);

    static native /* synthetic */ void E0(SplashActivity splashActivity);

    static native /* synthetic */ String F0(SplashActivity splashActivity, String str);

    private native void G0();

    private native /* synthetic */ void H0();

    private native /* synthetic */ void I0();

    private native void J0();

    private native String info(String str);

    private static native /* synthetic */ void native_special_clinit1();

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
