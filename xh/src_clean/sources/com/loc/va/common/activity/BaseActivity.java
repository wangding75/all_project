package com.loc.va.common.activity;

import android.R;
import android.graphics.Color;
import android.icu.impl.Normalizer2Impl;
import android.os.Bundle;
import android.view.MenuItem;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.constraintlayout.widget.ConstraintLayout;
import com.hjq.toast.ToastUtils;
import com.loc.va.App;
import com.loc.va.c;
import com.loc.va.ui.widget.dialog.c;
import com.loc.va.ui.widget.progress.SpotsDialog2;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public abstract class BaseActivity extends AppCompatActivity {
    

    /* renamed from: t, reason: collision with root package name */
    private ConstraintLayout f22488t;

    /* renamed from: u, reason: collision with root package name */
    private TextView f22489u;

    /* renamed from: v, reason: collision with root package name */
    private ImageButton f22490v;

    /* renamed from: w, reason: collision with root package name */
    private ImageButton f22491w;

    /* renamed from: x, reason: collision with root package name */
    private SpotsDialog2 f22492x;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a implements View.OnClickListener {
        a() {
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            BaseActivity.this.onClickBack(view);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes10.dex */
    class b implements View.OnClickListener {
        b() {
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            BaseActivity.this.onClickMore(view);
        }
    }

    

    private int g0() {
        return getResources().getDimensionPixelSize(getResources().getIdentifier("status_bar_height", "1<80;", "android"));
    }

    public void A0(int i5) {
        ToastUtils.show(i5);
    }

    public void B0(String str) {
        if (str == null) {
            return;
        }
        if (str.length() > 50) {
            Toast.makeText(this, str, 0).show();
        } else {
            ToastUtils.show((CharSequence) str);
        }
    }

    public boolean d0() {
        return false;
    }

    public void e0() {
        InputMethodManager inputMethodManager = (InputMethodManager) getSystemService("input_method");
        if (inputMethodManager != null) {
            inputMethodManager.hideSoftInputFromWindow(getWindow().getDecorView().getWindowToken(), 0);
        }
    }

    public App f0() {
        return App.a();
    }

    public boolean h0() {
        ConstraintLayout constraintLayout = this.f22488t;
        if (constraintLayout == null) {
            return false;
        }
        constraintLayout.setVisibility(8);
        return true;
    }

    public void i0() {
        if (this.f22488t != null) {
            this.f22490v.setVisibility(8);
        }
    }

    public void j0() {
        SpotsDialog2 spotsDialog2 = this.f22492x;
        if (spotsDialog2 != null) {
            spotsDialog2.dismiss();
        }
        this.f22492x = null;
    }

    public void k0() {
        if (this.f22488t != null) {
            this.f22491w.setVisibility(8);
        }
    }

    protected void l0() {
        ConstraintLayout constraintLayout = (ConstraintLayout) findViewById(c.i.vc);
        this.f22488t = constraintLayout;
        if (constraintLayout != null) {
            this.f22489u = (TextView) constraintLayout.findViewById(c.i.uc);
            this.f22490v = (ImageButton) this.f22488t.findViewById(c.i.f21803z1);
            this.f22491w = (ImageButton) this.f22488t.findViewById(c.i.i8);
            this.f22489u.setText(getTitle());
            this.f22490v.setVisibility(8);
            this.f22491w.setVisibility(8);
            this.f22490v.setOnClickListener(new a());
            this.f22491w.setOnClickListener(new b());
        }
    }

    /* JADX WARN: Code restructure failed: missing block: B:8:0x0012, code lost:
    
        if (r9 != 3) goto L13;
     */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public void m0(int i5, int i6) {
        if (i6 != 0) {
            if (i6 == 1 || i6 == 2) {
                getWindow().getDecorView().setSystemUiVisibility(8192);
            }
            getWindow().setBackgroundDrawableResource(i5);
        }
        getWindow().getDecorView().setSystemUiVisibility(0);
        getWindow().setBackgroundDrawableResource(i5);
    }

    protected void n0(MenuItem menuItem) {
        finish();
    }

    public void o0(int i5) {
        getWindow().clearFlags(201326592);
        getWindow().getDecorView().setSystemUiVisibility(i5 | 1024);
        getWindow().addFlags(Integer.MIN_VALUE);
    }

    public void onClickBack(View view) {
        finish();
    }

    public void onClickMore(View view) {
    }

    @Override // androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
    }

    @Override // androidx.appcompat.app.AppCompatActivity, androidx.fragment.app.FragmentActivity, android.app.Activity
    protected void onDestroy() {
        super.onDestroy();
        SpotsDialog2 spotsDialog2 = this.f22492x;
        if (spotsDialog2 != null) {
            spotsDialog2.dismiss();
        }
    }

    @Override // android.app.Activity
    public boolean onOptionsItemSelected(MenuItem menuItem) {
        if (menuItem.getItemId() == 16908332) {
            n0(menuItem);
        }
        return super.onOptionsItemSelected(menuItem);
    }

    public void p0(int i5) {
        if (this.f22488t != null) {
            this.f22491w.setImageResource(i5);
        }
    }

    public void q0(int i5) {
        getWindow().setNavigationBarColor(i5);
    }

    public void r0() {
        q0(Color.parseColor("#FFFFFF"));
    }

    public boolean s0() {
        ConstraintLayout constraintLayout = this.f22488t;
        if (constraintLayout == null) {
            return false;
        }
        constraintLayout.setVisibility(0);
        return true;
    }

    @Override // android.app.Activity
    public void setTitle(CharSequence charSequence) {
        super.setTitle(charSequence);
        TextView textView = this.f22489u;
        if (textView != null) {
            textView.setText(charSequence);
        }
    }

    public void t0() {
        if (this.f22488t != null) {
            this.f22490v.setVisibility(0);
        }
    }

    public void u0(String str, c.e eVar, c.d dVar) {
        v0(null, str, null, null, eVar, dVar);
    }

    public void v0(String str, String str2, String str3, String str4, c.e eVar, c.d dVar) {
        String str5 = str;
        String str6 = str4;
        com.loc.va.ui.widget.dialog.c cVar = new com.loc.va.ui.widget.dialog.c(this, R.style.Theme.Material.Light.Dialog.NoActionBar);
        if (d5.b.e(str5)) {
            str5 = "提示";
        }
        cVar.s(str5);
        cVar.p(str2);
        cVar.u(d5.b.e(str3) ? "确定" : str3, eVar);
        if (dVar != null) {
            if (d5.b.e(str3)) {
                str6 = "取消";
            }
            cVar.r(str6, dVar);
            cVar.setCancelable(false);
        }
        cVar.setCancelable(false);
        cVar.show();
    }

    public void w0(String str, String str2, String str3, String str4, String str5, String str6, c.e eVar, c.d dVar, c.InterfaceC0214c interfaceC0214c) {
        String str7 = str;
        String str8 = str5;
        String str9 = str6;
        com.loc.va.ui.widget.dialog.c cVar = new com.loc.va.ui.widget.dialog.c(this, R.style.Theme.Material.Light.Dialog.NoActionBar);
        if (d5.b.e(str7)) {
            str7 = "提示";
        }
        cVar.s(str7);
        if (d5.b.e(str2)) {
            cVar.l(str4);
        } else {
            cVar.p(str2);
        }
        if (!d5.b.e(str3)) {
            cVar.m(str3);
        }
        if (d5.b.e(str8)) {
            str8 = "确定";
        }
        cVar.u(str8, eVar);
        if (dVar != null) {
            if (d5.b.e(str9)) {
                str9 = "取消";
            }
            cVar.r(str9, dVar);
        }
        cVar.k(true);
        if (interfaceC0214c != null) {
            cVar.n(interfaceC0214c);
        }
        cVar.setCancelable(false);
        cVar.show();
    }

    public void x0() {
        y0("loading...");
    }

    public void y0(String str) {
        if (this.f22492x == null) {
            SpotsDialog2 spotsDialog2 = (SpotsDialog2) new SpotsDialog2.Builder().setContext(this).setMessage(str).build();
            this.f22492x = spotsDialog2;
            spotsDialog2.setCancelable(false);
            this.f22492x.show();
        }
        this.f22492x.setMessage(str);
    }

    public void z0() {
        if (this.f22488t != null) {
            this.f22491w.setVisibility(0);
        }
    }
}
