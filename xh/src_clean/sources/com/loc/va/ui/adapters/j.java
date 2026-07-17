package com.loc.va.ui.adapters;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import com.loc.va.abs.ui.a;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class j extends com.loc.va.abs.ui.a<com.loc.va.model.j> {

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    static class a extends a.C0207a {

        /* renamed from: c, reason: collision with root package name */
        final ImageView f23023c;

        /* renamed from: d, reason: collision with root package name */
        final TextView f23024d;

        /* renamed from: e, reason: collision with root package name */
        final TextView f23025e;

        public a(View view) {
            super(view);
            this.f23023c = (ImageView) a(c.i.D6);
            this.f23024d = (TextView) a(c.i.E6);
            this.f23025e = (TextView) a(c.i.M6);
        }
    }

    public j(Context context) {
        super(context);
    }

    @Override // com.loc.va.abs.ui.a
    protected View f(int i5, ViewGroup viewGroup) {
        View n5 = n(c.l.f21850b1, viewGroup, false);
        n5.setTag(new a(n5));
        return n5;
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // com.loc.va.abs.ui.a
    /* renamed from: q, reason: merged with bridge method [inline-methods] */
    public void d(View view, com.loc.va.model.j jVar, int i5) {
        a aVar = (a) view.getTag();
        if (jVar.f22690d == null) {
            aVar.f23023c.setImageResource(c.h.f21557i1);
        } else {
            aVar.f23023c.setVisibility(0);
            aVar.f23023c.setImageDrawable(jVar.f22690d);
        }
        aVar.f23024d.setText(jVar.f22689c);
    }
}
