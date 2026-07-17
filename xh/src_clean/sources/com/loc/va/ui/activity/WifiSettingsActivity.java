package com.loc.va.ui.activity;

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
public class WifiSettingsActivity extends BaseActivity implements View.OnClickListener {
    private static short[] $;
    private static int[] qk;
    private static int[] ql;
    private static int[] qn;
    private static int[] qo;
    private static int[] qp;
    private EditText A;
    private EditText B;
    private Button C;
    private int D;
    private String E;

    /* renamed from: y, reason: collision with root package name */
    private Button f22889y;

    /* renamed from: z, reason: collision with root package name */
    private Button f22890z;

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3294);
        Loader.registerNativesForClass(72);
        native_special_clinit1();
    }

    private native void C0();

    private native void D0();

    private native void E0();

    private native void F0();

    private native void G0();

    private static native /* synthetic */ void native_special_clinit1();

    @Override // android.view.View.OnClickListener
    public native void onClick(View view);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
