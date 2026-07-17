package com.loc.va.ui.activity;

import android.os.Bundle;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class DeviceSelectActivity extends BaseActivity {
    private static short[] $;
    private static int[] ob;
    private static int[] oc;

    /* renamed from: y, reason: collision with root package name */
    private RecyclerView f22733y;

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(8633);
        Loader.registerNativesForClass(12);
        native_special_clinit1();
    }

    private static native /* synthetic */ void native_special_clinit1();

    public native void C0(View view, int i5);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
