package com.loc.va.home.device;

import android.os.Bundle;
import android.view.MenuItem;
import androidx.appcompat.widget.Toolbar;
import androidx.viewpager.widget.ViewPager;
import b.j0;
import b.k0;
import com.google.android.material.tabs.TabLayout;
import com.loc.va.abs.ui.VActivity;
import com.loc.va.c;
import com.loc.va.ui.adapters.l;
import com.lody.virtual.client.core.j;
import com.stub.StubApp;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class DeviceSettingsActivity extends VActivity {
    

    /* renamed from: t, reason: collision with root package name */
    private Toolbar f22579t;

    /* renamed from: u, reason: collision with root package name */
    private TabLayout f22580u;

    /* renamed from: v, reason: collision with root package name */
    private ViewPager f22581v;

    

    private void k0() {
        U(this.f22579t);
        androidx.appcompat.app.a N = N();
        if (N != null) {
            N.Y(true);
        }
    }

    @Override // androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected void onCreate(@k0 Bundle bundle) {
        super.onCreate(bundle);
        setContentView(c.l.L);
        Toolbar toolbar = (Toolbar) findViewById(c.i.f21727m3);
        this.f22579t = toolbar;
        this.f22580u = (TabLayout) toolbar.findViewById(c.i.f21721l3);
        this.f22581v = (ViewPager) findViewById(c.i.f21733n3);
        k0();
        this.f22581v.setAdapter(new l(v()));
        if (j.h().O() >= 23) {
            androidx.core.app.b.C(this, new String[]{"android.permission.READ_PHONE_STATE"}, 0);
        } else {
            this.f22580u.setupWithViewPager(this.f22581v);
        }
    }

    @Override // com.loc.va.abs.ui.VActivity, android.app.Activity
    public boolean onOptionsItemSelected(MenuItem menuItem) {
        if (menuItem.getItemId() != 16908332) {
            return super.onOptionsItemSelected(menuItem);
        }
        finish();
        return true;
    }

    @Override // androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, android.app.Activity
    public void onRequestPermissionsResult(int i5, @j0 String[] strArr, @j0 int[] iArr) {
        StubApp.interface22(i5, strArr, iArr);
        for (int i6 : iArr) {
            if (i6 == 0) {
                this.f22580u.setupWithViewPager(this.f22581v);
                return;
            }
        }
    }
}
