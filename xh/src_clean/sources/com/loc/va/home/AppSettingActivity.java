package com.loc.va.home;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.os.Bundle;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import b.k0;
import com.loc.va.abs.ui.VActivity;
import com.loc.va.c;
import com.lody.virtual.client.ipc.VPackageManager;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class AppSettingActivity extends VActivity {
    

    /* renamed from: t, reason: collision with root package name */
    private com.loc.va.model.r f22560t;

    /* renamed from: u, reason: collision with root package name */
    private int f22561u;

    /* renamed from: v, reason: collision with root package name */
    private PackageInfo f22562v;

    

    private void l0() {
        boolean d6 = com.lody.virtual.client.core.j.h().d(this.f22562v.packageName, this.f22561u);
        StringBuilder sb = new StringBuilder();
        sb.append("clean app data ");
        sb.append(d6 ? "success." : "failed.");
        Toast.makeText(this, sb.toString(), 0).show();
    }

    public static void m0(Context context, String str, int i5) {
        Intent intent = new Intent(context, (Class<?>) AppSettingActivity.class);
        intent.putExtra("extra.PKG", str);
        intent.putExtra("extra.UserId", i5);
        context.startActivity(intent);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void n0(View view) {
        l0();
    }

    @Override // androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected void onCreate(@k0 Bundle bundle) {
        super.onCreate(bundle);
        Intent intent = getIntent();
        String stringExtra = intent.getStringExtra("extra.PKG");
        this.f22561u = intent.getIntExtra("extra.UserId", -1);
        this.f22560t = com.loc.va.model.u.d().e(stringExtra);
        PackageInfo packageInfo = VPackageManager.get().getPackageInfo(stringExtra, 0, this.f22561u);
        this.f22562v = packageInfo;
        if (this.f22560t == null || packageInfo == null) {
            finish();
            return;
        }
        f0();
        setTitle(c.p.U);
        setContentView(c.l.C);
        ImageView imageView = (ImageView) findViewById(c.i.f21713k1);
        TextView textView = (TextView) findViewById(c.i.f21725m1);
        imageView.setImageDrawable(this.f22560t.f22680e);
        textView.setText(this.f22560t.f22679d);
        findViewById(c.i.f21780v2).setOnClickListener(new View.OnClickListener() { // from class: com.loc.va.home.a
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                AppSettingActivity.this.n0(view);
            }
        });
    }
}
