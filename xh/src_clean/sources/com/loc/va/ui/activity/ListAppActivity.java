package com.loc.va.ui.activity;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.loc.va.ui.adapters.i;
import com.loc.va.ui.widget.DragSelectRecyclerView;
import com.stub.StubApp;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class ListAppActivity extends BaseActivity {
    private static short[] $;
    public static String C;
    private static int[] sG;
    private static int[] sH;
    private static int[] sJ;
    private static int[] sK;
    private static int[] sL;
    private static int[] sM;
    private static int[] sN;
    private DragSelectRecyclerView A;
    private com.loc.va.model.b B;

    /* renamed from: y, reason: collision with root package name */
    private com.loc.va.ui.adapters.i f22812y;

    /* renamed from: z, reason: collision with root package name */
    private Button f22813z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class a implements i.a {
        private static int[] bX;

        static {
            Loader.registerNativesForClass(34);
            native_special_clinit0();
        }

        a() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // com.loc.va.ui.adapters.i.a
        public native void a(com.loc.va.model.c cVar, int i5);

        @Override // com.loc.va.ui.adapters.i.a
        public native boolean b(int i5);
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3272);
        Loader.registerNativesForClass(40);
        native_special_clinit1();
    }

    public static native /* synthetic */ void C0(ListAppActivity listAppActivity, View view);

    public static native /* synthetic */ void D0(ListAppActivity listAppActivity, int i5);

    static native /* synthetic */ com.loc.va.ui.adapters.i E0(ListAppActivity listAppActivity);

    private native void F0();

    private native /* synthetic */ void G0(int i5);

    private native /* synthetic */ void H0(View view);

    private static native /* synthetic */ void native_special_clinit1();

    public native void I0(List<com.loc.va.model.c> list);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
