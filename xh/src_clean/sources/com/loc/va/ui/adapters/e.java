package com.loc.va.ui.adapters;

import android.content.Context;
import android.util.SparseArray;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import com.loc.va.c;
import com.loc.va.ui.adapters.d;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class e extends RecyclerView.e0 implements View.OnClickListener, View.OnLongClickListener {

    /* renamed from: a, reason: collision with root package name */
    public d.a f22994a;

    /* renamed from: b, reason: collision with root package name */
    public d.b f22995b;

    /* renamed from: c, reason: collision with root package name */
    private SparseArray<View> f22996c;

    public e(View view) {
        super(view);
        view.setOnClickListener(this);
        view.setOnLongClickListener(this);
        this.f22996c = new SparseArray<>();
    }

    public e(View view, d.a aVar) {
        super(view);
        view.setOnClickListener(this);
        view.setOnLongClickListener(this);
        this.f22994a = aVar;
        this.f22996c = new SparseArray<>();
    }

    public e(View view, d.a aVar, d.b bVar) {
        super(view);
        view.setOnClickListener(this);
        view.setOnLongClickListener(this);
        this.f22994a = aVar;
        this.f22995b = bVar;
        this.f22996c = new SparseArray<>();
    }

    public void a() {
        this.itemView.performClick();
    }

    public Button b(int i5) {
        return (Button) f(i5);
    }

    public ImageView c(int i5) {
        return (ImageView) f(i5);
    }

    public TextView d(int i5) {
        return (TextView) f(i5);
    }

    public View e(int i5) {
        return f(i5);
    }

    protected <T extends View> T f(int i5) {
        T t5 = (T) this.f22996c.get(i5);
        if (t5 != null) {
            return t5;
        }
        T t6 = (T) this.itemView.findViewById(i5);
        this.f22996c.put(i5, t6);
        return t6;
    }

    public e g(Context context, int i5, String str) {
        com.bumptech.glide.b.E(context).t(str).B0(c.n.f21962e0).r1((ImageView) f(i5));
        return this;
    }

    public e h(int i5, String str) {
        ((TextView) f(i5)).setText(str);
        return this;
    }

    @Override // android.view.View.OnClickListener
    public void onClick(View view) {
        d.a aVar = this.f22994a;
        if (aVar != null) {
            aVar.a(view, getLayoutPosition());
        }
    }

    @Override // android.view.View.OnLongClickListener
    public boolean onLongClick(View view) {
        d.b bVar = this.f22995b;
        if (bVar == null) {
            return false;
        }
        bVar.a(view, getLayoutPosition());
        return false;
    }
}
