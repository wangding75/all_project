package com.loc.va.ui.activity;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanResult;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.loc.va.ui.adapters.g;
import com.stub.StubApp;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class BluetootSelectActivity extends BaseActivity {
    private static short[] $ = null;
    private static String E = "BluetootSelectActivity";
    private static int[] pM;
    private static int[] pO;
    private static int[] pP;
    private static int[] pR;
    private static int[] pS;
    private Map<String, String> A = new HashMap();
    private final BroadcastReceiver B = new b();
    ScanCallback C = new c();
    BluetoothAdapter.LeScanCallback D = new d();

    /* renamed from: y, reason: collision with root package name */
    private RecyclerView f22725y;

    /* renamed from: z, reason: collision with root package name */
    private com.loc.va.ui.adapters.g f22726z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class a implements g.a {
        private static short[] $;
        private static int[] nD;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(6);
            native_special_clinit1();
        }

        a() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // com.loc.va.ui.adapters.g.a
        public native void a(View view, int i5, com.loc.va.model.i iVar);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class b extends BroadcastReceiver {
        private static short[] $;
        private static int[] nw;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(7);
            native_special_clinit1();
        }

        b() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // android.content.BroadcastReceiver
        public native void onReceive(Context context, Intent intent);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class c extends ScanCallback {
        private static int[] nK;
        private static int[] nL;
        private static int[] nM;

        static {
            Loader.registerNativesForClass(8);
            native_special_clinit0();
        }

        c() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // android.bluetooth.le.ScanCallback
        public native void onBatchScanResults(List<ScanResult> list);

        @Override // android.bluetooth.le.ScanCallback
        public native void onScanFailed(int i5);

        @Override // android.bluetooth.le.ScanCallback
        public native void onScanResult(int i5, ScanResult scanResult);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class d implements BluetoothAdapter.LeScanCallback {
        private static int[] nI;

        static {
            Loader.registerNativesForClass(9);
            native_special_clinit0();
        }

        d() {
        }

        private static native /* synthetic */ void native_special_clinit0();

        @Override // android.bluetooth.BluetoothAdapter.LeScanCallback
        public native void onLeScan(BluetoothDevice bluetoothDevice, int i5, byte[] bArr);
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3255);
        Loader.registerNativesForClass(10);
        native_special_clinit1();
    }

    static native /* synthetic */ String C0();

    static native /* synthetic */ Map D0(BluetootSelectActivity bluetootSelectActivity);

    static native /* synthetic */ com.loc.va.ui.adapters.g E0(BluetootSelectActivity bluetootSelectActivity);

    private native void F0();

    public static native byte[] G0(String str);

    private native void H0();

    private native void I0();

    private native void J0();

    private static native /* synthetic */ void native_special_clinit1();

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, android.app.Activity
    protected native void onDestroy();
}
