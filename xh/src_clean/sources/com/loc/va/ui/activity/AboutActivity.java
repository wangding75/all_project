package com.loc.va.ui.activity;

import android.os.Bundle;
import android.view.View;
import android.widget.ImageView;
import android.widget.PopupWindow;
import android.widget.TextView;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class AboutActivity extends BaseActivity {
    private static short[] $;
    private static int[] IZ;
    private static int[] Ja;
    private static int[] Jb;
    private static int[] Jc;
    private PopupWindow A;
    private View B;
    private TextView C;
    private TextView D;

    /* renamed from: y, reason: collision with root package name */
    private ImageView f22714y;

    /* renamed from: z, reason: collision with root package name */
    private TextView f22715z;

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3248);
        Loader.registerNativesForClass(0);
        native_special_clinit1();
    }

    private static native /* synthetic */ void native_special_clinit1();

    public native void click_pp(View view);

    public native void click_xy(View view);

    @Override // com.loc.va.common.activity.BaseActivity
    public native void onClickMore(View view);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
