package com.loc.va.ui.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import com.loc.va.c;
import com.loc.va.model.AppData;
import com.loc.va.ui.widget.LabelView;
import com.loc.va.ui.widget.LauncherIconView;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class q extends RecyclerView.g<c> {
    

    /* renamed from: a, reason: collision with root package name */
    private LayoutInflater f23034a;

    /* renamed from: b, reason: collision with root package name */
    private List<AppData> f23035b;

    /* renamed from: c, reason: collision with root package name */
    private a f23036c;

    /* renamed from: d, reason: collision with root package name */
    private b f23037d;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public interface a {
        void a(View view, int i5, AppData appData);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public interface b {
        void a(View view, int i5, AppData appData);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public class c extends RecyclerView.e0 {

        /* renamed from: a, reason: collision with root package name */
        LauncherIconView f23038a;

        /* renamed from: b, reason: collision with root package name */
        TextView f23039b;

        /* renamed from: c, reason: collision with root package name */
        LabelView f23040c;

        /* renamed from: d, reason: collision with root package name */
        LabelView f23041d;

        /* renamed from: e, reason: collision with root package name */
        View f23042e;

        c(View view) {
            super(view);
            this.f23038a = (LauncherIconView) view.findViewById(c.i.D6);
            this.f23039b = (TextView) view.findViewById(c.i.E6);
            this.f23040c = (LabelView) view.findViewById(c.i.F6);
            this.f23041d = (LabelView) view.findViewById(c.i.G6);
            this.f23042e = view.findViewById(c.i.L6);
        }
    }

    

    public q(Context context) {
        this.f23034a = LayoutInflater.from(context);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void g(int i5, AppData appData, View view) {
        a aVar = this.f23036c;
        if (aVar != null) {
            aVar.a(view, i5, appData);
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ boolean h(int i5, AppData appData, View view) {
        b bVar = this.f23037d;
        if (bVar == null) {
            return true;
        }
        bVar.a(view, i5, appData);
        return true;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static /* synthetic */ void i() {
        try {
            Thread.sleep(300L);
        } catch (InterruptedException e6) {
            e6.printStackTrace();
        }
    }

    private void t(final LauncherIconView launcherIconView) {
        launcherIconView.p(40, true);
        com.loc.va.abs.ui.c.a().j(new Runnable() { // from class: com.loc.va.ui.adapters.m
            @Override // java.lang.Runnable
            public final void run() {
                q.i();
            }
        }).h(new org.jdeferred.g() { // from class: com.loc.va.ui.adapters.n
            @Override // org.jdeferred.g
            public final void b(Object obj) {
                LauncherIconView.this.p(80, true);
            }
        });
    }

    public void e(AppData appData) {
        int size = this.f23035b.size() - 1;
        if (size == -1) {
            size = 0;
        }
        this.f23035b.add(size, appData);
        notifyItemRangeChanged(size, this.f23035b.size() - size);
    }

    public List<AppData> f() {
        return this.f23035b;
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemCount() {
        List<AppData> list = this.f23035b;
        if (list == null) {
            return 0;
        }
        return list.size();
    }

    public void k(int i5, int i6) {
        this.f23035b.add(i6, this.f23035b.remove(i5));
        notifyItemMoved(i5, i6);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    /* renamed from: l, reason: merged with bridge method [inline-methods] */
    public void onBindViewHolder(c cVar, final int i5) {
        LabelView labelView;
        String $2;
        final AppData appData = this.f23035b.get(i5);
        cVar.f23038a.setImageDrawable(appData.e());
        cVar.f23039b.setText(appData.f());
        if (!appData.j() || appData.k()) {
            cVar.f23042e.setVisibility(4);
        } else {
            cVar.f23042e.setVisibility(0);
        }
        cVar.itemView.setOnClickListener(new View.OnClickListener() { // from class: com.loc.va.ui.adapters.o
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                q.this.g(i5, appData, view);
            }
        });
        cVar.itemView.setOnLongClickListener(new View.OnLongClickListener() { // from class: com.loc.va.ui.adapters.p
            @Override // android.view.View.OnLongClickListener
            public final boolean onLongClick(View view) {
                boolean h5;
                h5 = q.this.h(i5, appData, view);
                return h5;
            }
        });
        if (appData instanceof com.loc.va.model.q) {
            cVar.f23040c.setVisibility(0);
            cVar.f23040c.setText((((com.loc.va.model.q) appData).f22674d + 1) + "");
        } else {
            cVar.f23040c.setVisibility(4);
        }
        boolean z5 = !appData.i();
        if (appData.c() && z5) {
            cVar.f23041d.setVisibility(0);
            if (z5) {
                labelView = cVar.f23041d;
                $2 = "32";
            } else {
                labelView = cVar.f23041d;
                $2 = "64";
            }
            labelView.setText($2);
        } else {
            cVar.f23041d.setVisibility(4);
        }
        boolean k5 = appData.k();
        LauncherIconView launcherIconView = cVar.f23038a;
        if (k5) {
            t(launcherIconView);
        } else {
            launcherIconView.p(100, false);
        }
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    /* renamed from: m, reason: merged with bridge method [inline-methods] */
    public c onCreateViewHolder(ViewGroup viewGroup, int i5) {
        return new c(this.f23034a.inflate(c.l.f21858d1, (ViewGroup) null));
    }

    public void n(AppData appData) {
        int indexOf = this.f23035b.indexOf(appData);
        if (indexOf >= 0) {
            notifyItemChanged(indexOf);
        }
        notifyDataSetChanged();
    }

    public void o(AppData appData) {
        if (this.f23035b.remove(appData)) {
            notifyDataSetChanged();
        }
    }

    public void p(int i5, AppData appData) {
        this.f23035b.set(i5, appData);
        notifyItemChanged(i5);
    }

    public void q(a aVar) {
        this.f23036c = aVar;
    }

    public void r(b bVar) {
        this.f23037d = bVar;
    }

    public void s(List<AppData> list) {
        this.f23035b = list;
        notifyDataSetChanged();
    }
}
