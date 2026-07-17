package com.loc.va.abs.nestedadapter;

import android.view.View;
import android.view.ViewGroup;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import androidx.recyclerview.widget.StaggeredGridLayoutManager;
import b.j0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class b extends com.loc.va.abs.nestedadapter.a {

    /* renamed from: e, reason: collision with root package name */
    public static final int f20943e = -1;

    /* renamed from: f, reason: collision with root package name */
    public static final int f20944f = -2;

    /* renamed from: b, reason: collision with root package name */
    private RecyclerView.o f20945b;

    /* renamed from: c, reason: collision with root package name */
    private View f20946c;

    /* renamed from: d, reason: collision with root package name */
    private View f20947d;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a extends GridLayoutManager.c {

        /* renamed from: e, reason: collision with root package name */
        final /* synthetic */ GridLayoutManager f20948e;

        a(GridLayoutManager gridLayoutManager) {
            this.f20948e = gridLayoutManager;
        }

        @Override // androidx.recyclerview.widget.GridLayoutManager.c
        public int f(int i5) {
            boolean z5 = false;
            boolean z6 = i5 == 0 && b.this.e();
            if (i5 == b.this.getItemCount() - 1 && b.this.d()) {
                z5 = true;
            }
            if (z5 || z6) {
                return this.f20948e.k();
            }
            return 1;
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* renamed from: com.loc.va.abs.nestedadapter.b$b, reason: collision with other inner class name */
    class C0205b extends RecyclerView.e0 {
        C0205b(View view) {
            super(view);
        }
    }

    public b(@j0 RecyclerView.g gVar) {
        super(gVar);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public boolean d() {
        return this.f20947d != null;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public boolean e() {
        return this.f20946c != null;
    }

    private void i(RecyclerView.o oVar) {
        if (oVar instanceof GridLayoutManager) {
            GridLayoutManager gridLayoutManager = (GridLayoutManager) oVar;
            gridLayoutManager.u(new a(gridLayoutManager));
        }
    }

    public void f() {
        this.f20947d = null;
        a().notifyDataSetChanged();
    }

    public void g() {
        this.f20946c = null;
        a().notifyDataSetChanged();
    }

    @Override // com.loc.va.abs.nestedadapter.a, androidx.recyclerview.widget.RecyclerView.g
    public int getItemCount() {
        return super.getItemCount() + (e() ? 1 : 0) + (d() ? 1 : 0);
    }

    @Override // com.loc.va.abs.nestedadapter.a, androidx.recyclerview.widget.RecyclerView.g
    public int getItemViewType(int i5) {
        if (e() && i5 == 0) {
            return -1;
        }
        if (d() && i5 == getItemCount() - 1) {
            return -2;
        }
        if (e()) {
            i5--;
        }
        return super.getItemViewType(i5);
    }

    public void h(View view) {
        this.f20947d = view;
        a().notifyDataSetChanged();
    }

    public void j(View view) {
        this.f20946c = view;
        a().notifyDataSetChanged();
    }

    @Override // com.loc.va.abs.nestedadapter.a, androidx.recyclerview.widget.RecyclerView.g
    public void onAttachedToRecyclerView(RecyclerView recyclerView) {
        super.onAttachedToRecyclerView(recyclerView);
        RecyclerView.o layoutManager = recyclerView.getLayoutManager();
        this.f20945b = layoutManager;
        i(layoutManager);
    }

    @Override // com.loc.va.abs.nestedadapter.a, androidx.recyclerview.widget.RecyclerView.g
    public void onBindViewHolder(RecyclerView.e0 e0Var, int i5) {
        if (getItemViewType(i5) == -1 || getItemViewType(i5) == -2) {
            return;
        }
        if (e()) {
            i5--;
        }
        super.onBindViewHolder(e0Var, i5);
    }

    @Override // com.loc.va.abs.nestedadapter.a, androidx.recyclerview.widget.RecyclerView.g
    public RecyclerView.e0 onCreateViewHolder(ViewGroup viewGroup, int i5) {
        View view = i5 == -1 ? this.f20946c : i5 == -2 ? this.f20947d : null;
        if (view == null) {
            return super.onCreateViewHolder(viewGroup, i5);
        }
        if (this.f20945b instanceof StaggeredGridLayoutManager) {
            ViewGroup.LayoutParams layoutParams = view.getLayoutParams();
            StaggeredGridLayoutManager.c cVar = layoutParams != null ? new StaggeredGridLayoutManager.c(layoutParams.width, layoutParams.height) : new StaggeredGridLayoutManager.c(-1, -2);
            cVar.j(true);
            view.setLayoutParams(cVar);
        }
        return new C0205b(view);
    }
}
