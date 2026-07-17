package com.loc.va.abs.ui;

import android.content.Context;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentActivity;
import l1.a;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class b<T extends l1.a> extends Fragment {

    /* renamed from: d, reason: collision with root package name */
    protected T f20958d;

    /* renamed from: e, reason: collision with root package name */
    private boolean f20959e;

    protected org.jdeferred.android.b f() {
        return c.a();
    }

    public void g() {
        h();
    }

    public void h() {
        FragmentActivity activity = getActivity();
        if (activity != null) {
            activity.finish();
        }
    }

    public T i() {
        return this.f20958d;
    }

    public boolean j() {
        return this.f20959e;
    }

    public void k(T t5) {
        this.f20958d = t5;
    }

    @Override // androidx.fragment.app.Fragment
    public void onAttach(Context context) {
        this.f20959e = true;
        super.onAttach(context);
    }

    @Override // androidx.fragment.app.Fragment
    public void onDetach() {
        this.f20959e = false;
        super.onDetach();
    }
}
