package com.loc.va.ui.activity;

import android.os.AsyncTask;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import arm.Loader;
import com.loc.va.common.activity.BaseActivity;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class FeedbackActivity extends BaseActivity implements View.OnClickListener {
    private static short[] $;
    private static int[] eu;
    private static int[] ev;

    /* renamed from: y, reason: collision with root package name */
    private EditText f22734y;

    /* renamed from: z, reason: collision with root package name */
    private Button f22735z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class a extends AsyncTask<String, Integer, String> {
        private static short[] $;
        private static int[] DK;
        private static int[] DM;
        private static int[] DN;

        /* renamed from: a, reason: collision with root package name */
        private String f22736a;

        private static native String $(int i5, int i6, int i7);

        static {
            Loader.registerNativesForClass(13);
            native_special_clinit1();
        }

        a() {
        }

        private static native /* synthetic */ void native_special_clinit1();

        protected native String a(String... strArr);

        protected native void b(String str);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ String doInBackground(String[] strArr);

        @Override // android.os.AsyncTask
        protected native /* bridge */ /* synthetic */ void onPostExecute(String str);

        @Override // android.os.AsyncTask
        protected native void onPreExecute();
    }

    private static native String $(int i5, int i6, int i7);

    static {
        StubApp.interface11(8634);
        Loader.registerNativesForClass(14);
        native_special_clinit1();
    }

    static native /* synthetic */ String C0(FeedbackActivity feedbackActivity, String str, String str2);

    private native String feedback(String str, String str2);

    private static native /* synthetic */ void native_special_clinit1();

    @Override // android.view.View.OnClickListener
    public native void onClick(View view);

    @Override // com.loc.va.common.activity.BaseActivity, androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected native void onCreate(Bundle bundle);
}
