package com.loc.va.ui.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;
import com.loc.va.ui.adapters.e;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public abstract class d<T, H extends e> extends RecyclerView.g<e> {
    

    /* renamed from: g, reason: collision with root package name */
    protected static String f22987g = "BaseAdapter";

    /* renamed from: a, reason: collision with root package name */
    protected Context f22988a;

    /* renamed from: b, reason: collision with root package name */
    protected List<T> f22989b;

    /* renamed from: c, reason: collision with root package name */
    protected int f22990c;

    /* renamed from: d, reason: collision with root package name */
    public a f22991d;

    /* renamed from: e, reason: collision with root package name */
    public b f22992e;

    /* renamed from: f, reason: collision with root package name */
    protected boolean f22993f;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public interface a {
        void a(View view, int i5);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public interface b {
        void a(View view, int i5);
    }

    

    public d(Context context, int i5) {
        this(context, i5, null);
    }

    public d(Context context, int i5, List<T> list) {
        this.f22991d = null;
        this.f22992e = null;
        this.f22988a = context;
        if (list == null) {
            this.f22989b = new ArrayList();
        } else {
            this.f22989b = list;
        }
        this.f22990c = i5;
    }

    public void a(int i5, T t5) {
        this.f22989b.add(i5, t5);
        notifyItemInserted(i5);
    }

    public void b(int i5, List<T> list) {
        if (list == null || list.size() <= 0) {
            return;
        }
        Iterator<T> it = list.iterator();
        while (it.hasNext()) {
            this.f22989b.add(i5, it.next());
            notifyItemInserted(i5);
        }
    }

    public void c(List<T> list) {
        b(0, list);
    }

    public void d() {
        Iterator<T> it = this.f22989b.iterator();
        while (it.hasNext()) {
            int indexOf = this.f22989b.indexOf(it.next());
            it.remove();
            notifyItemRemoved(indexOf);
        }
    }

    protected abstract void e(H h5, T t5);

    public List<T> f() {
        return this.f22989b;
    }

    public T g(int i5) {
        if (i5 >= this.f22989b.size()) {
            return null;
        }
        return this.f22989b.get(i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemCount() {
        List<T> list = this.f22989b;
        if (list == null || list.size() <= 0) {
            return 0;
        }
        return this.f22989b.size();
    }

    public void h(List<T> list) {
        if (list == null || list.size() <= 0) {
            return;
        }
        int size = list.size();
        int size2 = this.f22989b.size();
        for (int i5 = 0; i5 < size; i5++) {
            this.f22989b.add(list.get(i5));
            notifyItemInserted(i5 + size2);
        }
    }

    /* JADX WARN: Multi-variable type inference failed */
    @Override // androidx.recyclerview.widget.RecyclerView.g
    /* renamed from: i, reason: merged with bridge method [inline-methods] */
    public void onBindViewHolder(e eVar, int i5) {
        e(eVar, g(i5));
        this.f22993f = true;
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    /* renamed from: j, reason: merged with bridge method [inline-methods] */
    public e onCreateViewHolder(ViewGroup viewGroup, int i5) {
        return new e(LayoutInflater.from(viewGroup.getContext()).inflate(this.f22990c, viewGroup, false), this.f22991d, this.f22992e);
    }

    public void k(List<T> list) {
        if (list == null || list.size() <= 0) {
            return;
        }
        d();
        int size = list.size();
        for (int i5 = 0; i5 < size; i5++) {
            this.f22989b.add(i5, list.get(i5));
            notifyItemInserted(i5);
        }
    }

    public void l(T t5) {
        int indexOf = this.f22989b.indexOf(t5);
        this.f22989b.remove(indexOf);
        notifyItemRemoved(indexOf);
        if (indexOf != this.f22989b.size()) {
            notifyItemRangeRemoved(indexOf, this.f22989b.size() - indexOf);
        }
    }

    public void m(a aVar) {
        this.f22991d = aVar;
    }

    public void n(b bVar) {
        this.f22992e = bVar;
    }
}
