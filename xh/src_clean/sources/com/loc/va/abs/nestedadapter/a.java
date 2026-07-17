package com.loc.va.abs.nestedadapter;

import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class a extends RecyclerView.g {

    /* renamed from: a, reason: collision with root package name */
    protected final RecyclerView.g f20941a;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* renamed from: com.loc.va.abs.nestedadapter.a$a, reason: collision with other inner class name */
    class C0204a extends RecyclerView.i {
        C0204a() {
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onChanged() {
            a.this.notifyDataSetChanged();
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onItemRangeChanged(int i5, int i6) {
            a.this.notifyItemRangeChanged(i5, i6);
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onItemRangeInserted(int i5, int i6) {
            a.this.notifyItemRangeInserted(i5, i6);
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onItemRangeMoved(int i5, int i6, int i7) {
            a.this.notifyItemMoved(i5, i6);
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onItemRangeRemoved(int i5, int i6) {
            a.this.notifyItemRangeRemoved(i5, i6);
        }
    }

    public a(RecyclerView.g gVar) {
        this.f20941a = gVar;
        gVar.registerAdapterDataObserver(new C0204a());
    }

    public RecyclerView.g a() {
        return this.f20941a;
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemCount() {
        return this.f20941a.getItemCount();
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public long getItemId(int i5) {
        return this.f20941a.getItemId(i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemViewType(int i5) {
        return this.f20941a.getItemViewType(i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onAttachedToRecyclerView(RecyclerView recyclerView) {
        this.f20941a.onAttachedToRecyclerView(recyclerView);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onBindViewHolder(RecyclerView.e0 e0Var, int i5) {
        this.f20941a.onBindViewHolder(e0Var, i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public RecyclerView.e0 onCreateViewHolder(ViewGroup viewGroup, int i5) {
        return this.f20941a.onCreateViewHolder(viewGroup, i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onDetachedFromRecyclerView(RecyclerView recyclerView) {
        this.f20941a.onDetachedFromRecyclerView(recyclerView);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public boolean onFailedToRecycleView(RecyclerView.e0 e0Var) {
        return this.f20941a.onFailedToRecycleView(e0Var);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onViewAttachedToWindow(RecyclerView.e0 e0Var) {
        this.f20941a.onViewAttachedToWindow(e0Var);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onViewDetachedFromWindow(RecyclerView.e0 e0Var) {
        this.f20941a.onViewDetachedFromWindow(e0Var);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onViewRecycled(RecyclerView.e0 e0Var) {
        this.f20941a.onViewRecycled(e0Var);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void registerAdapterDataObserver(RecyclerView.i iVar) {
        this.f20941a.registerAdapterDataObserver(iVar);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void setHasStableIds(boolean z5) {
        this.f20941a.setHasStableIds(z5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void unregisterAdapterDataObserver(RecyclerView.i iVar) {
        this.f20941a.unregisterAdapterDataObserver(iVar);
    }
}
