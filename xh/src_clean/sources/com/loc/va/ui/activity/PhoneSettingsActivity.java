package com.loc.va.ui.activity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class PhoneSettingsActivity extends BaseActivity implements View.OnClickListener {
    private static short[] $;
    private static int[] sd;
    private static int[] se;
    private static int[] sf;
    private static int[] sh;
    private static int[] si;
    private static int[] sj;
    private static int[] sk;
    private Button A;
    private EditText B;
    private EditText C;
    private int D;
    private String E;

    /* renamed from: y, reason: collision with root package name */
    private Button f22866y;

    /* renamed from: z, reason: collision with root package name */
    private Button f22867z;

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3282);
        Loader.registerNativesForClass(54);
        native_special_clinit1();
    }

    private native void C0();

    private native void D0();

    private native void E0();

    private native void F0();

    private native void G0();

    private static native /* synthetic */ void native_special_clinit1();

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, android.app.Activity
    protected native void onActivityResult(int i5, int i6, Intent intent);

    @Override // android.view.View.OnClickListener
    public native void onClick(View view);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
