package com.loc.va.ui.activity;

import android.app.Activity;
import android.os.Bundle;
import arm.Loader;
import com.stub.StubApp;
import java.io.InputStream;
import java.io.OutputStream;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class VirtualCameraActivity extends Activity {
    private static short[] $;
    private static int[] sp;
    private static int[] sq;

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3291);
        Loader.registerNativesForClass(67);
        native_special_clinit1();
    }

    private static native /* synthetic */ void native_special_clinit1();

    public native void a(InputStream inputStream, OutputStream outputStream);

    @Override // android.app.Activity
    protected native void onCreate(@b.k0 Bundle bundle);
}
