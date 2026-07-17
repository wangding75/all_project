package com.loc.va.ui.adapters;

import android.content.Context;
import com.loc.va.c;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class k extends d<com.loc.va.model.k, e> {
    public k(Context context, int i5) {
        super(context, i5);
    }

    public k(Context context, int i5, List<com.loc.va.model.k> list) {
        super(context, i5, list);
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // com.loc.va.ui.adapters.d
    /* renamed from: o, reason: merged with bridge method [inline-methods] */
    public void e(e eVar, com.loc.va.model.k kVar) {
        eVar.d(c.i.f21650a4).setText(kVar.c());
    }

    public String p(int i5) {
        return ((com.loc.va.model.k) this.f22989b.get(i5)).a();
    }

    public boolean q(int i5) {
        if (i5 == 0) {
            return true;
        }
        return !((com.loc.va.model.k) this.f22989b.get(i5 - 1)).a().equals(((com.loc.va.model.k) this.f22989b.get(i5)).a());
    }
}
