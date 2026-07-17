package com.loc.va.ui.widget;

import android.os.Bundle;
import androidx.recyclerview.widget.RecyclerView;
import androidx.recyclerview.widget.RecyclerView.e0;
import java.util.ArrayList;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public abstract class k<VH extends RecyclerView.e0> extends RecyclerView.g<VH> {
    

    /* renamed from: b, reason: collision with root package name */
    private a f23335b;

    /* renamed from: c, reason: collision with root package name */
    private int f23336c = -1;

    /* renamed from: d, reason: collision with root package name */
    private int f23337d = -1;

    /* renamed from: a, reason: collision with root package name */
    private ArrayList<Integer> f23334a = new ArrayList<>();

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    public interface a {
        void a(int i5);
    }

    

    protected k() {
    }

    private void b() {
        if (this.f23336c == this.f23334a.size()) {
            return;
        }
        int size = this.f23334a.size();
        this.f23336c = size;
        a aVar = this.f23335b;
        if (aVar != null) {
            aVar.a(size);
        }
    }

    public final void a() {
        this.f23334a.clear();
        notifyDataSetChanged();
        b();
    }

    public final int c() {
        return this.f23334a.size();
    }

    public final Integer[] d() {
        ArrayList<Integer> arrayList = this.f23334a;
        return (Integer[]) arrayList.toArray(new Integer[arrayList.size()]);
    }

    protected boolean e(int i5) {
        return true;
    }

    public final boolean f(int i5) {
        return this.f23334a.contains(Integer.valueOf(i5));
    }

    public void g(Bundle bundle) {
        h("selected_indices", bundle);
    }

    public void h(String str, Bundle bundle) {
        if (bundle == null || !bundle.containsKey(str)) {
            return;
        }
        ArrayList<Integer> arrayList = (ArrayList) bundle.getSerializable(str);
        this.f23334a = arrayList;
        if (arrayList == null) {
            this.f23334a = new ArrayList<>();
        } else {
            b();
        }
    }

    public void i(Bundle bundle) {
        j("selected_indices", bundle);
    }

    public void j(String str, Bundle bundle) {
        bundle.putSerializable(str, this.f23334a);
    }

    public final void k() {
        int itemCount = getItemCount();
        this.f23334a.clear();
        for (int i5 = 0; i5 < itemCount; i5++) {
            if (e(i5)) {
                this.f23334a.add(Integer.valueOf(i5));
            }
        }
        notifyDataSetChanged();
        b();
    }

    public final void l(int i5, int i6, int i7, int i8) {
        int i9 = i7;
        if (i5 == i6) {
            while (i9 <= i8) {
                if (i9 != i5) {
                    n(i9, false);
                }
                i9++;
            }
            b();
            return;
        }
        if (i6 < i5) {
            for (int i10 = i6; i10 <= i5; i10++) {
                n(i10, true);
            }
            if (i9 > -1 && i9 < i6) {
                while (i9 < i6) {
                    if (i9 != i5) {
                        n(i9, false);
                    }
                    i9++;
                }
            }
            if (i8 > -1) {
                for (int i11 = i5 + 1; i11 <= i8; i11++) {
                    n(i11, false);
                }
            }
        } else {
            for (int i12 = i5; i12 <= i6; i12++) {
                n(i12, true);
            }
            if (i8 > -1 && i8 > i6) {
                for (int i13 = i6 + 1; i13 <= i8; i13++) {
                    if (i13 != i5) {
                        n(i13, false);
                    }
                }
            }
            if (i9 > -1) {
                while (i9 < i5) {
                    n(i9, false);
                    i9++;
                }
            }
        }
        b();
    }

    public void m(int i5) {
        this.f23337d = i5;
    }

    public final void n(int i5, boolean z5) {
        boolean z6 = z5;
        if (!e(i5)) {
            z6 = false;
        }
        if (z6) {
            if (!this.f23334a.contains(Integer.valueOf(i5)) && (this.f23337d == -1 || this.f23334a.size() < this.f23337d)) {
                this.f23334a.add(Integer.valueOf(i5));
                notifyItemChanged(i5);
            }
        } else if (this.f23334a.contains(Integer.valueOf(i5))) {
            this.f23334a.remove(Integer.valueOf(i5));
            notifyItemChanged(i5);
        }
        b();
    }

    public void o(a aVar) {
        this.f23335b = aVar;
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    @b.i
    public void onBindViewHolder(VH vh, int i5) {
        vh.itemView.setTag(vh);
    }

    public final boolean p(int i5) {
        boolean z5 = false;
        if (e(i5)) {
            if (this.f23334a.contains(Integer.valueOf(i5))) {
                this.f23334a.remove(Integer.valueOf(i5));
            } else if (this.f23337d == -1 || this.f23334a.size() < this.f23337d) {
                this.f23334a.add(Integer.valueOf(i5));
                z5 = true;
            }
            notifyItemChanged(i5);
        }
        b();
        return z5;
    }
}
