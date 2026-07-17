package com.loc.va.ui.activity;

import android.content.Intent;
import android.os.Bundle;
import android.view.MenuItem;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentActivity;
import androidx.viewpager2.adapter.FragmentStateAdapter;
import androidx.viewpager2.widget.ViewPager2;
import arm.Loader;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.google.android.material.navigation.NavigationBarView;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class HomeActivity extends BaseActivity implements NavigationBarView.e {
    private static short[] $;
    private static String C;
    private static int[] bI;
    private static int[] bL;
    private static int[] bN;
    private static int[] bQ;
    private static int[] bR;
    private static int[] bS;
    private static int[] bT;
    private int A = 0;
    private List<Fragment> B;

    /* renamed from: y, reason: collision with root package name */
    private ViewPager2 f22738y;

    /* renamed from: z, reason: collision with root package name */
    private BottomNavigationView f22739z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class a extends ViewPager2.OnPageChangeCallback {
        private static int[] Of;

        static {
            Loader.registerNativesForClass(15);
            native_special_clinit0();
        }

        a() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // androidx.viewpager2.widget.ViewPager2.OnPageChangeCallback
        public native void onPageSelected(int i5);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class b extends FragmentStateAdapter {
        static {
            Loader.registerNativesForClass(16);
            native_special_clinit0();
        }

        public b(@b.j0 FragmentActivity fragmentActivity) {
            super(fragmentActivity);
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // androidx.viewpager2.adapter.FragmentStateAdapter
        @b.j0
        public native Fragment createFragment(int i5);

        @Override // androidx.recyclerview.widget.RecyclerView.g
        public native int getItemCount();
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(8635);
        Loader.registerNativesForClass(17);
        native_special_clinit1();
    }

    static native /* synthetic */ int C0(HomeActivity homeActivity);

    static native /* synthetic */ int D0(HomeActivity homeActivity, int i5);

    static native /* synthetic */ void E0(HomeActivity homeActivity, int i5, int i6);

    static native /* synthetic */ BottomNavigationView F0(HomeActivity homeActivity);

    static native /* synthetic */ List G0(HomeActivity homeActivity);

    private native void H0();

    private native void I0();

    private native void J0();

    private native void K0();

    private native void L0(int i5, int i6);

    private static native /* synthetic */ void native_special_clinit1();

    @Override // com.google.android.material.navigation.NavigationBarView.e
    public native boolean a(@b.j0 MenuItem menuItem);

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, android.app.Activity
    protected native void onActivityResult(int i5, int i6, @b.k0 Intent intent);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, android.app.Activity
    public native void onRequestPermissionsResult(int i5, @b.j0 String[] strArr, @b.j0 int[] iArr);
}
