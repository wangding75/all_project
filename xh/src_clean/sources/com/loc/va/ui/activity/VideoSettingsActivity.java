package com.loc.va.ui.activity;

import android.content.Intent;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class VideoSettingsActivity extends BaseActivity implements View.OnClickListener {
    private static short[] $ = null;
    public static final int D = 2;
    private static String E;
    private static int[] bi;
    private static int[] bk;
    private static int[] bl;
    private static int[] bo;
    private static int[] bq;
    private static int[] br;
    private static int[] bs;
    private static int[] bt;
    private static int[] bu;
    private String A;
    private int B;
    private String C;

    /* renamed from: y, reason: collision with root package name */
    private ImageView f22876y;

    /* renamed from: z, reason: collision with root package name */
    private Button f22877z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public class a extends Thread {
        private static short[] $;
        private static int[] rY;

        /* renamed from: a, reason: collision with root package name */
        private int f22878a;

        /* renamed from: b, reason: collision with root package name */
        private String f22879b;

        /* renamed from: c, reason: collision with root package name */
        private int f22880c;

        /* renamed from: d, reason: collision with root package name */
        private int f22881d;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(64);
            native_special_clinit1();
        }

        public a(int i5, String str, int i6, int i7) {
            this.f22878a = i5;
            this.f22879b = str;
            this.f22880c = i6;
            this.f22881d = i7;
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // java.lang.Thread, java.lang.Runnable
        public native void run();
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(8652);
        Loader.registerNativesForClass(65);
        native_special_clinit1();
    }

    private native void C0(String str);

    private native String D0();

    public static native String E0();

    public static native Bitmap F0(String str);

    public static native boolean G0(String str);

    public static native boolean H0(String str);

    public static native boolean I0(String str, int i5);

    private static native /* synthetic */ void native_special_clinit1();

    public native void add_url(View view);

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, android.app.Activity
    protected native void onActivityResult(int i5, int i6, Intent intent);

    @Override // android.view.View.OnClickListener
    public native void onClick(View view);

    @Override // com.loc.va.common.activity.BaseActivity
    public native void onClickMore(View view);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);

    public native void url_scan(View view);
}
