package com.loc.va.ui.adapters;

import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class s extends RecyclerView.g {

    /* renamed from: a, reason: collision with root package name */
    protected final RecyclerView.g f23044a;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class a extends RecyclerView.i {
        a() {
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onChanged() {
            s.this.notifyDataSetChanged();
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onItemRangeChanged(int i5, int i6) {
            s.this.notifyItemRangeChanged(i5, i6);
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onItemRangeInserted(int i5, int i6) {
            s.this.notifyItemRangeInserted(i5, i6);
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onItemRangeMoved(int i5, int i6, int i7) {
            s.this.notifyItemMoved(i5, i6);
        }

        @Override // androidx.recyclerview.widget.RecyclerView.i
        public void onItemRangeRemoved(int i5, int i6) {
            s.this.notifyItemRangeRemoved(i5, i6);
        }
    }

    public s(RecyclerView.g gVar) {
        this.f23044a = gVar;
        gVar.registerAdapterDataObserver(new a());
    }

    public RecyclerView.g a() {
        return this.f23044a;
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemCount() {
        return this.f23044a.getItemCount();
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public long getItemId(int i5) {
        return this.f23044a.getItemId(i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemViewType(int i5) {
        return this.f23044a.getItemViewType(i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onAttachedToRecyclerView(RecyclerView recyclerView) {
        this.f23044a.onAttachedToRecyclerView(recyclerView);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onBindViewHolder(RecyclerView.e0 e0Var, int i5) {
        this.f23044a.onBindViewHolder(e0Var, i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public RecyclerView.e0 onCreateViewHolder(ViewGroup viewGroup, int i5) {
        return this.f23044a.onCreateViewHolder(viewGroup, i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onDetachedFromRecyclerView(RecyclerView recyclerView) {
        this.f23044a.onDetachedFromRecyclerView(recyclerView);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public boolean onFailedToRecycleView(RecyclerView.e0 e0Var) {
        return this.f23044a.onFailedToRecycleView(e0Var);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onViewAttachedToWindow(RecyclerView.e0 e0Var) {
        this.f23044a.onViewAttachedToWindow(e0Var);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onViewDetachedFromWindow(RecyclerView.e0 e0Var) {
        this.f23044a.onViewDetachedFromWindow(e0Var);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onViewRecycled(RecyclerView.e0 e0Var) {
        this.f23044a.onViewRecycled(e0Var);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void registerAdapterDataObserver(RecyclerView.i iVar) {
        this.f23044a.registerAdapterDataObserver(iVar);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void setHasStableIds(boolean z5) {
        this.f23044a.setHasStableIds(z5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void unregisterAdapterDataObserver(RecyclerView.i iVar) {
        this.f23044a.unregisterAdapterDataObserver(iVar);
    }
}
