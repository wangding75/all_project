package com.loc.va.ui.adapters;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import com.loc.va.abs.ui.a;
import com.loc.va.c;
import dalvik.bytecode.Opcodes;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class a extends com.loc.va.abs.ui.a<com.loc.va.model.n> {
    

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* renamed from: com.loc.va.ui.adapters.a$a, reason: collision with other inner class name */
    static class C0212a extends a.C0207a {

        /* renamed from: c, reason: collision with root package name */
        final ImageView f22982c;

        /* renamed from: d, reason: collision with root package name */
        final TextView f22983d;

        /* renamed from: e, reason: collision with root package name */
        final TextView f22984e;

        public C0212a(View view) {
            super(view);
            this.f22982c = (ImageView) a(c.i.D6);
            this.f22983d = (TextView) a(c.i.E6);
            this.f22984e = (TextView) a(c.i.M6);
        }
    }

    

    public a(Context context) {
        super(context);
    }

    @Override // com.loc.va.abs.ui.a
    protected View f(int i5, ViewGroup viewGroup) {
        View n5 = n(c.l.f21850b1, viewGroup, false);
        n5.setTag(new C0212a(n5));
        return n5;
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // com.loc.va.abs.ui.a
    /* renamed from: q, reason: merged with bridge method [inline-methods] */
    public void d(View view, com.loc.va.model.n nVar, int i5) {
        TextView textView;
        String str;
        C0212a c0212a = (C0212a) view.getTag();
        c0212a.f22982c.setImageDrawable(nVar.f22690d);
        if (nVar.f22688b > 0) {
            textView = c0212a.f22983d;
            str = nVar.f22689c + " (" + (nVar.f22688b + 1) + "V";
        } else {
            textView = c0212a.f22983d;
            str = nVar.f22689c;
        }
        textView.setText(str);
        if (nVar.f22666f == null || nVar.f22665e == 0) {
            c0212a.f22984e.setText(c.p.f22136w4);
            return;
        }
        c0212a.f22984e.setText(nVar.f22666f.f24845i + "," + nVar.f22666f.f24846j);
    }
}
