package com.loc.va.ui.activity;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import arm.Loader;
import com.baidu.mapapi.search.sug.OnGetSuggestionResultListener;
import com.baidu.mapapi.search.sug.SuggestionResult;
import com.baidu.mapapi.search.sug.SuggestionSearch;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class LocationSearchActivity extends BaseActivity {
    private static short[] $;
    private static int[] EG;
    private static int[] EH;
    private static int[] EI;
    private static int[] EJ;
    private static int[] EK;
    private static int[] ES;
    private static int[] EU;
    private static int[] EV;
    private static int[] EW;
    private static int[] EX;
    private static int[] EY;
    private static int[] EZ;
    private static int[] Fb;
    private static int[] Fc;
    private static int[] Fd;
    private static String H;
    private RecyclerView A;
    private List<com.loc.va.model.o> B;
    private com.loc.va.ui.adapters.r C;
    private SQLiteDatabase D;
    private o1.a E;
    private SuggestionSearch F;
    private List<SuggestionResult.SuggestionInfo> G;

    /* renamed from: y, reason: collision with root package name */
    private EditText f22820y;

    /* renamed from: z, reason: collision with root package name */
    private TextView f22821z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class a implements TextWatcher {
        private static short[] $;
        private static int[] KN;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(41);
            native_special_clinit1();
        }

        a() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // android.text.TextWatcher
        public native void afterTextChanged(Editable editable);

        @Override // android.text.TextWatcher
        public native void beforeTextChanged(CharSequence charSequence, int i5, int i6, int i7);

        @Override // android.text.TextWatcher
        public native void onTextChanged(CharSequence charSequence, int i5, int i6, int i7);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    class b implements OnGetSuggestionResultListener {
        private static short[] $;
        private static int[] KV;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(42);
            native_special_clinit1();
        }

        b() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        @Override // com.baidu.mapapi.search.sug.OnGetSuggestionResultListener
        public native void onGetSuggestionResult(SuggestionResult suggestionResult);
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(3275);
        Loader.registerNativesForClass(43);
        native_special_clinit1();
    }

    public static native /* synthetic */ List C0(LocationSearchActivity locationSearchActivity);

    public static native /* synthetic */ void D0(LocationSearchActivity locationSearchActivity, View view);

    public static native /* synthetic */ void E0(LocationSearchActivity locationSearchActivity, Throwable th);

    public static native /* synthetic */ void F0(LocationSearchActivity locationSearchActivity, View view, int i5);

    public static native /* synthetic */ void G0(LocationSearchActivity locationSearchActivity, List list);

    public static native /* synthetic */ void H0(LocationSearchActivity locationSearchActivity, View view, int i5);

    static native /* synthetic */ EditText I0(LocationSearchActivity locationSearchActivity);

    static native /* synthetic */ SuggestionSearch J0(LocationSearchActivity locationSearchActivity);

    static native /* synthetic */ List K0(LocationSearchActivity locationSearchActivity);

    static native /* synthetic */ List L0(LocationSearchActivity locationSearchActivity, List list);

    static native /* synthetic */ List M0(LocationSearchActivity locationSearchActivity);

    static native /* synthetic */ com.loc.va.ui.adapters.r N0(LocationSearchActivity locationSearchActivity);

    static native /* synthetic */ TextView O0(LocationSearchActivity locationSearchActivity);

    private native SQLiteDatabase Q0(Context context);

    private native /* synthetic */ List T0() throws Exception;

    private native /* synthetic */ void U0(List list);

    private native /* synthetic */ void V0(Throwable th);

    private native /* synthetic */ void W0(View view);

    private native /* synthetic */ void X0(View view, int i5);

    private native /* synthetic */ void Y0(View view, int i5);

    private static native /* synthetic */ void native_special_clinit1();

    public native void P0(Context context);

    public native void R0(Context context);

    public native List S0(Context context) throws Exception;

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, android.app.Activity
    protected native void onDestroy();
}
