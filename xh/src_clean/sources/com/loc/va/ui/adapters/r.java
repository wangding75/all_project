package com.loc.va.ui.adapters;

import android.content.Context;
import android.widget.TextView;
import com.loc.va.c;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class r extends d<com.loc.va.model.o, e> {
    

    

    public r(Context context, int i5, List<com.loc.va.model.o> list) {
        super(context, i5, list);
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // com.loc.va.ui.adapters.d
    /* renamed from: o, reason: merged with bridge method [inline-methods] */
    public void e(e eVar, com.loc.va.model.o oVar) {
        String str;
        TextView d6 = eVar.d(c.i.f21661c1);
        if (d5.b.e(oVar.e())) {
            str = oVar.a();
        } else {
            str = oVar.a() + "(" + oVar.e() + ")";
        }
        d6.setText(str);
    }
}
