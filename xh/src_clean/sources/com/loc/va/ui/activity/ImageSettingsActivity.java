package com.loc.va.ui.activity;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class ImageSettingsActivity extends BaseActivity implements View.OnClickListener {
    private static short[] $ = null;
    public static final int D = 2;
    private static int[] ek;
    private static int[] el;
    private static int[] em;
    private static int[] en;
    private static int[] eo;
    private String A;
    private int B;
    private String C;

    /* renamed from: y, reason: collision with root package name */
    private ImageView f22810y;

    /* renamed from: z, reason: collision with root package name */
    private Button f22811z;

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3265);
        Loader.registerNativesForClass(33);
        native_special_clinit1();
    }

    private native void C0(String str);

    private native void D0(Uri uri);

    private static native /* synthetic */ void native_special_clinit1();

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, android.app.Activity
    protected native void onActivityResult(int i5, int i6, Intent intent);

    @Override // android.view.View.OnClickListener
    public native void onClick(View view);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
