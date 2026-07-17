package com.loc.va.abs.ui;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.SpinnerAdapter;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public abstract class a<T> extends BaseAdapter implements SpinnerAdapter {

    /* renamed from: a, reason: collision with root package name */
    protected Context f20953a;

    /* renamed from: b, reason: collision with root package name */
    private LayoutInflater f20954b;

    /* renamed from: c, reason: collision with root package name */
    protected final List<T> f20955c = new ArrayList();

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* renamed from: com.loc.va.abs.ui.a$a, reason: collision with other inner class name */
    public static class C0207a {

        /* renamed from: a, reason: collision with root package name */
        protected View f20956a;

        /* renamed from: b, reason: collision with root package name */
        protected Context f20957b;

        public C0207a(View view) {
            this.f20956a = view;
            this.f20957b = view.getContext();
        }

        /* JADX WARN: Incorrect return type in method signature: <T:Landroid/view/View;>(I)TT; */
        protected View a(int i5) {
            return this.f20956a.findViewById(i5);
        }
    }

    public a(Context context) {
        this.f20953a = context;
        this.f20954b = LayoutInflater.from(context);
    }

    public boolean a(int i5, T t5, boolean z5) {
        if (t5 != null) {
            if (z5 && g(t5)) {
                return false;
            }
            if (i5 >= 0) {
                this.f20955c.add(i5, t5);
            } else {
                this.f20955c.add(t5);
            }
        }
        return true;
    }

    public boolean b(T t5) {
        return a(-1, t5, false);
    }

    public void c(Collection<T> collection) {
        if (collection != null) {
            this.f20955c.addAll(collection);
        }
    }

    protected abstract void d(View view, T t5, int i5);

    public void e() {
        this.f20955c.clear();
    }

    protected abstract View f(int i5, ViewGroup viewGroup);

    public boolean g(T t5) {
        if (t5 == null) {
            return false;
        }
        return this.f20955c.contains(t5);
    }

    @Override // android.widget.Adapter
    public final int getCount() {
        return this.f20955c.size();
    }

    @Override // android.widget.BaseAdapter, android.widget.SpinnerAdapter
    public View getDropDownView(int i5, View view, ViewGroup viewGroup) {
        if (view == null) {
            view = f(i5, viewGroup);
        }
        d(view, getItem(i5), i5);
        return view;
    }

    @Override // android.widget.Adapter
    public final T getItem(int i5) {
        if (i5 < 0 || i5 >= getCount()) {
            return null;
        }
        return this.f20955c.get(i5);
    }

    @Override // android.widget.Adapter
    public long getItemId(int i5) {
        return i5;
    }

    @Override // android.widget.Adapter
    public final View getView(int i5, View view, ViewGroup viewGroup) {
        if (view == null) {
            view = f(i5, viewGroup);
        }
        d(view, getItem(i5), i5);
        return view;
    }

    public int h(T t5) {
        return this.f20955c.indexOf(t5);
    }

    public Context i() {
        return this.f20953a;
    }

    public final T j(int i5) {
        return this.f20955c.get(i5);
    }

    public final T k(long j5) {
        return getItem((int) j5);
    }

    public List<T> l() {
        return this.f20955c;
    }

    protected <VW extends View> VW m(int i5, ViewGroup viewGroup) {
        return (VW) this.f20954b.inflate(i5, viewGroup);
    }

    protected <VW extends View> VW n(int i5, ViewGroup viewGroup, boolean z5) {
        return (VW) this.f20954b.inflate(i5, viewGroup, z5);
    }

    public T o(int i5) {
        return this.f20955c.remove(i5);
    }

    public void p(Collection<T> collection) {
        e();
        c(collection);
    }
}
