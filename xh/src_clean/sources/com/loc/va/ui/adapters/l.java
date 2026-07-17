package com.loc.va.ui.adapters;

import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;
import com.loc.va.App;
import com.loc.va.c;
import java.util.ArrayList;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class l extends androidx.fragment.app.p {

    /* renamed from: n, reason: collision with root package name */
    private List<String> f23026n;

    public l(FragmentManager fragmentManager) {
        super(fragmentManager);
        ArrayList arrayList = new ArrayList();
        this.f23026n = arrayList;
        arrayList.add(App.a().getResources().getString(c.p.x5));
    }

    @Override // androidx.viewpager.widget.a
    public int e() {
        return this.f23026n.size();
    }

    @Override // androidx.viewpager.widget.a
    public CharSequence g(int i5) {
        return this.f23026n.get(i5);
    }

    @Override // androidx.fragment.app.p
    public Fragment v(int i5) {
        return com.loc.va.home.device.d.h();
    }
}
