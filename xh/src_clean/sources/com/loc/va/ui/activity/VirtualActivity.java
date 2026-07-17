package com.loc.va.ui.activity;

import android.os.Bundle;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class VirtualActivity extends BaseActivity {
    private static short[] $;
    private static int[] IL;

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3290);
        Loader.registerNativesForClass(66);
        native_special_clinit1();
    }

    private static native /* synthetic */ void native_special_clinit1();

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
