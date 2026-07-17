package com.loc.va.abs.ui;

import android.app.Activity;
import android.content.Context;
import android.view.MenuItem;
import android.view.View;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;
import b.y;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public abstract class VActivity extends AppCompatActivity {
    protected <T extends View> T d0(int i5) {
        return (T) findViewById(i5);
    }

    protected org.jdeferred.android.b e0() {
        return c.a();
    }

    public void f0() {
        androidx.appcompat.app.a N = N();
        if (N != null) {
            N.Y(true);
        }
    }

    public Fragment g0(@y int i5) {
        return v().p0(i5);
    }

    public Activity h0() {
        return this;
    }

    public Context i0() {
        return this;
    }

    public void j0(@y int i5, Fragment fragment) {
        v().r().D(i5, fragment).r();
    }

    @Override // android.app.Activity
    public boolean onOptionsItemSelected(MenuItem menuItem) {
        if (menuItem.getItemId() == 16908332) {
            finish();
        }
        return super.onOptionsItemSelected(menuItem);
    }

    @Override // androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, android.app.Activity
    protected void onStart() {
        super.onStart();
    }

    @Override // androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, android.app.Activity
    protected void onStop() {
        super.onStop();
    }
}
