package com.loc.va.common.activity;

import android.R;
import android.app.Activity;
import android.content.Context;
import android.os.Bundle;
import androidx.fragment.app.Fragment;
import b.k0;
import com.hjq.toast.ToastUtils;
import com.loc.va.App;
import com.loc.va.ui.widget.dialog.c;
import com.loc.va.ui.widget.progress.SpotsDialog2;
import d5.b;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class a extends Fragment {
    

    /* renamed from: d, reason: collision with root package name */
    private Activity f22495d;

    /* renamed from: e, reason: collision with root package name */
    private Context f22496e;

    /* renamed from: f, reason: collision with root package name */
    private SpotsDialog2 f22497f;

    

    public void f(String str, c.e eVar, c.d dVar) {
        g(null, str, null, null, eVar, dVar);
    }

    public void g(String str, String str2, String str3, String str4, c.e eVar, c.d dVar) {
        String str5 = str;
        String str6 = str4;
        c cVar = new c(getContext(), R.style.Theme.Material.Light.Dialog.NoActionBar);
        if (b.e(str5)) {
            str5 = "提示";
        }
        cVar.s(str5);
        cVar.p(str2);
        cVar.u(b.e(str3) ? "确定" : str3, eVar);
        if (dVar != null) {
            if (b.e(str3)) {
                str6 = "取消";
            }
            cVar.r(str6, dVar);
            cVar.setCancelable(false);
        }
        cVar.setCancelable(false);
        cVar.show();
    }

    @Override // androidx.fragment.app.Fragment
    public Context getContext() {
        Context context = super.getContext();
        return context != null ? context : App.a();
    }

    public void h(String str, String str2, String str3, String str4, String str5, String str6, c.e eVar, c.d dVar, c.InterfaceC0214c interfaceC0214c) {
        String str7 = str;
        String str8 = str5;
        String str9 = str6;
        c cVar = new c(getContext(), R.style.Theme.Material.Light.Dialog.NoActionBar);
        if (b.e(str7)) {
            str7 = "提示";
        }
        cVar.s(str7);
        if (b.e(str2)) {
            cVar.l(str4);
        } else {
            cVar.p(str2);
        }
        if (!b.e(str3)) {
            cVar.m(str3);
        }
        if (b.e(str8)) {
            str8 = "确定";
        }
        cVar.u(str8, eVar);
        if (dVar != null) {
            if (b.e(str9)) {
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

    public void hideLoading() {
        SpotsDialog2 spotsDialog2 = this.f22497f;
        if (spotsDialog2 != null) {
            spotsDialog2.dismiss();
        }
        this.f22497f = null;
    }

    public void i(String str) {
        if (this.f22497f == null) {
            SpotsDialog2 spotsDialog2 = (SpotsDialog2) new SpotsDialog2.Builder().setContext(getContext()).setMessage(str).build();
            this.f22497f = spotsDialog2;
            spotsDialog2.setCancelable(false);
            this.f22497f.show();
        }
        this.f22497f.setMessage(str);
    }

    public void j(int i5) {
        ToastUtils.show(i5);
    }

    public void k(String str) {
        ToastUtils.show((CharSequence) str);
    }

    @Override // androidx.fragment.app.Fragment
    public void onAttach(Context context) {
        super.onAttach(context);
        this.f22495d = getActivity();
    }

    @Override // androidx.fragment.app.Fragment
    public void onCreate(@k0 Bundle bundle) {
        super.onCreate(bundle);
        this.f22496e = getContext();
    }

    public void showLoading() {
        i("loading...");
    }
}
