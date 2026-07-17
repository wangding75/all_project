package com.loc.va.ui.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import androidx.recyclerview.widget.StaggeredGridLayoutManager;
import com.loc.va.c;
import com.loc.va.ui.widget.LabelView;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class i extends com.loc.va.ui.widget.k<b> {

    /* renamed from: i, reason: collision with root package name */
    private static final int f23013i = -2;

    /* renamed from: e, reason: collision with root package name */
    private final View f23014e;

    /* renamed from: f, reason: collision with root package name */
    private LayoutInflater f23015f;

    /* renamed from: g, reason: collision with root package name */
    private List<com.loc.va.model.c> f23016g;

    /* renamed from: h, reason: collision with root package name */
    private a f23017h;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    public interface a {
        void a(com.loc.va.model.c cVar, int i5);

        boolean b(int i5);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class b extends RecyclerView.e0 {

        /* renamed from: a, reason: collision with root package name */
        private ImageView f23018a;

        /* renamed from: b, reason: collision with root package name */
        private TextView f23019b;

        /* renamed from: c, reason: collision with root package name */
        private ImageView f23020c;

        /* renamed from: d, reason: collision with root package name */
        private LabelView f23021d;

        b(View view) {
            super(view);
            if (view != i.this.f23014e) {
                this.f23018a = (ImageView) view.findViewById(c.i.D6);
                this.f23019b = (TextView) view.findViewById(c.i.E6);
                this.f23020c = (ImageView) view.findViewById(c.i.B6);
                this.f23021d = (LabelView) view.findViewById(c.i.C6);
            }
        }
    }

    public i(Context context) {
        this.f23015f = LayoutInflater.from(context);
        View view = new View(context);
        this.f23014e = view;
        StaggeredGridLayoutManager.c cVar = new StaggeredGridLayoutManager.c(-1, com.loc.va.abs.ui.c.b(context, 60));
        cVar.j(true);
        view.setLayoutParams(cVar);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void u(com.loc.va.model.c cVar, int i5, View view) {
        this.f23017h.a(cVar, i5);
    }

    @Override // com.loc.va.ui.widget.k
    public boolean e(int i5) {
        return this.f23017h.b(i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemCount() {
        List<com.loc.va.model.c> list = this.f23016g;
        if (list == null) {
            return 1;
        }
        return 1 + list.size();
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemViewType(int i5) {
        if (i5 == getItemCount() - 1) {
            return -2;
        }
        return super.getItemViewType(i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public void onAttachedToRecyclerView(RecyclerView recyclerView) {
        super.onAttachedToRecyclerView(recyclerView);
    }

    public com.loc.va.model.c s(int i5) {
        return this.f23016g.get(i5);
    }

    public List<com.loc.va.model.c> t() {
        return this.f23016g;
    }

    @Override // com.loc.va.ui.widget.k, androidx.recyclerview.widget.RecyclerView.g
    /* renamed from: v, reason: merged with bridge method [inline-methods] */
    public void onBindViewHolder(b bVar, final int i5) {
        ImageView imageView;
        int i6;
        if (getItemViewType(i5) == -2) {
            return;
        }
        super.onBindViewHolder(bVar, i5);
        final com.loc.va.model.c cVar = this.f23016g.get(i5);
        bVar.f23018a.setImageDrawable(cVar.f22638d);
        bVar.f23019b.setText(cVar.f22639e);
        if (f(i5)) {
            bVar.f23018a.setAlpha(1.0f);
            imageView = bVar.f23020c;
            i6 = c.h.f21577m1;
        } else {
            bVar.f23018a.setAlpha(0.65f);
            imageView = bVar.f23020c;
            i6 = c.h.B1;
        }
        imageView.setImageResource(i6);
        if (cVar.f22640f > 0) {
            bVar.f23021d.setVisibility(0);
            bVar.f23021d.setText((cVar.f22640f + 1) + "");
        } else {
            bVar.f23021d.setVisibility(4);
        }
        bVar.itemView.setOnClickListener(new View.OnClickListener() { // from class: com.loc.va.ui.adapters.h
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                i.this.u(cVar, i5, view);
            }
        });
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    /* renamed from: w, reason: merged with bridge method [inline-methods] */
    public b onCreateViewHolder(ViewGroup viewGroup, int i5) {
        return i5 == -2 ? new b(this.f23014e) : new b(this.f23015f.inflate(c.l.X0, viewGroup, false));
    }

    public void x(List<com.loc.va.model.c> list) {
        this.f23016g = list;
        notifyDataSetChanged();
    }

    public void y(a aVar) {
        this.f23017h = aVar;
    }
}
