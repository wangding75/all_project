package com.loc.va.home;

import android.annotation.TargetApi;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;
import b.j0;
import b.k0;
import com.loc.va.c;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
@TargetApi(23)
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class PermissionRequestActivity extends Activity {

    /* renamed from: d, reason: collision with root package name */
    private static final int f22563d = 995;

    /* renamed from: a, reason: collision with root package name */
    private int f22568a;

    /* renamed from: b, reason: collision with root package name */
    private String f22569b;

    /* renamed from: c, reason: collision with root package name */
    private String f22570c;
    

    /* renamed from: e, reason: collision with root package name */
    private static String f22564e = "extra.permission";

    /* renamed from: f, reason: collision with root package name */
    private static String f22565f = "extra.app_name";

    /* renamed from: g, reason: collision with root package name */
    private static String f22566g = "extra.user_id";

    /* renamed from: h, reason: collision with root package name */
    private static String f22567h = "extra.package_name";

    

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void b() {
        Toast.makeText(this, getString(c.p.f22028e5, this.f22569b), 0).show();
    }

    public static void c(@j0 Activity activity, @j0 String[] strArr, @j0 String str, int i5, @j0 String str2, int i6) {
        Intent intent = new Intent(activity, (Class<?>) PermissionRequestActivity.class);
        intent.putExtra("extra.permission", strArr);
        intent.putExtra("extra.app_name", str);
        intent.putExtra("extra.package_name", str2);
        intent.putExtra("extra.user_id", i5);
        activity.startActivityForResult(intent, i6);
        activity.overridePendingTransition(0, 0);
    }

    @Override // android.app.Activity
    protected void onCreate(@k0 Bundle bundle) {
        super.onCreate(bundle);
        Intent intent = getIntent();
        String[] stringArrayExtra = intent.getStringArrayExtra("extra.permission");
        this.f22569b = intent.getStringExtra("extra.app_name");
        this.f22570c = intent.getStringExtra("extra.package_name");
        this.f22568a = intent.getIntExtra("extra.user_id", -1);
        requestPermissions(stringArrayExtra, f22563d);
    }

    @Override // android.app.Activity
    public void onRequestPermissionsResult(int i5, @j0 String[] strArr, @j0 int[] iArr) {
        StubApp.interface22(i5, strArr, iArr);
        super.onRequestPermissionsResult(i5, strArr, iArr);
        if (com.lody.virtual.helper.compat.s.e(iArr)) {
            Intent intent = new Intent();
            intent.putExtra("pkg", this.f22570c);
            intent.putExtra("user_id", this.f22568a);
            setResult(-1, intent);
        } else {
            runOnUiThread(new Runnable() { // from class: com.loc.va.home.w
                @Override // java.lang.Runnable
                public final void run() {
                    PermissionRequestActivity.this.b();
                }
            });
        }
        finish();
    }
}
