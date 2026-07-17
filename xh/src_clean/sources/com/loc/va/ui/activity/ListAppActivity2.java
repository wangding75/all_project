package com.loc.va.ui.activity;

import android.content.Context;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.view.View;
import android.widget.Button;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.loc.va.ui.adapters.i;
import com.loc.va.ui.widget.DragSelectRecyclerView;
import com.loc.va.ui.widget.quicksidebar.QuickSideBarView;
import com.loc.va.ui.widget.quicksidebar.tipsview.QuickSideBarTipsItemView;
import com.stub.StubApp;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class ListAppActivity2 extends BaseActivity {
    private static short[] $;
    private static int[] BP;
    private static int[] BQ;
    private static int[] BV;
    private static int[] BW;
    private static int[] BX;
    private static int[] BY;
    private static int[] BZ;
    private static int[] Ca;
    public static String H;
    private static String I;
    private com.loc.va.ui.adapters.i A;
    private RecyclerView.a0 B;
    private LinearLayoutManager C;
    private com.loc.va.model.b D;
    private QuickSideBarView E;
    private QuickSideBarTipsItemView F;
    private HashMap<String, Integer> G = new HashMap<>();

    /* renamed from: y, reason: collision with root package name */
    private Button f22815y;

    /* renamed from: z, reason: collision with root package name */
    private DragSelectRecyclerView f22816z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class a implements i.a {
        private static int[] uA;

        static {
            Loader.registerNativesForClass(35);
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

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class b extends androidx.recyclerview.widget.q {
        static {
            Loader.registerNativesForClass(36);
            native_special_clinit0();
        }

        b(Context context) {
            super(context);
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // androidx.recyclerview.widget.q
        protected native float calculateSpeedPerPixel(DisplayMetrics displayMetrics);

        @Override // androidx.recyclerview.widget.q
        protected native int getHorizontalSnapPreference();

        @Override // androidx.recyclerview.widget.q
        protected native int getVerticalSnapPreference();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class c implements r1.a {
        private static int[] uI;
        private static int[] uJ;

        static {
            Loader.registerNativesForClass(37);
            native_special_clinit0();
        }

        c() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // r1.a
        public native void a(boolean z5);

        @Override // r1.a
        public native void b(String str, int i5, float f5);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    private static class d implements Comparator<com.loc.va.model.c> {
        private static short[] $;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(38);
            native_special_clinit1();
        }

        private d() {
        }

        /* synthetic */ d(a aVar) {
            this();
        }

        private static native /* synthetic */ void native_special_clinit1();

        public native int a(com.loc.va.model.c cVar, com.loc.va.model.c cVar2);

        @Override // java.util.Comparator
        public native /* bridge */ /* synthetic */ int compare(com.loc.va.model.c cVar, com.loc.va.model.c cVar2);
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3271);
        Loader.registerNativesForClass(39);
        native_special_clinit1();
    }

    public static native /* synthetic */ void C0(ListAppActivity2 listAppActivity2, View view, int i5, int i6, int i7, int i8);

    public static native /* synthetic */ void D0(ListAppActivity2 listAppActivity2, View view);

    public static native /* synthetic */ void E0(ListAppActivity2 listAppActivity2, int i5);

    static native /* synthetic */ com.loc.va.ui.adapters.i F0(ListAppActivity2 listAppActivity2);

    static native /* synthetic */ QuickSideBarTipsItemView G0(ListAppActivity2 listAppActivity2);

    static native /* synthetic */ HashMap H0(ListAppActivity2 listAppActivity2);

    static native /* synthetic */ LinearLayoutManager I0(ListAppActivity2 listAppActivity2);

    private native void J0();

    private native /* synthetic */ void K0(int i5);

    private native /* synthetic */ void L0(View view, int i5, int i6, int i7, int i8);

    private native /* synthetic */ void M0(View view);

    private static native /* synthetic */ void native_special_clinit1();

    public native void N0(List<com.loc.va.model.c> list);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
