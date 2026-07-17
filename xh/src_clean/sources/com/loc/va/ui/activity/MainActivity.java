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
public class MainActivity extends BaseActivity {
    private static int[] qP;

    static {
        StubApp.interface11(3279);
        Loader.registerNativesForClass(51);
        native_special_clinit0();
    }

    private static native /* synthetic */ void native_special_clinit0();

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
