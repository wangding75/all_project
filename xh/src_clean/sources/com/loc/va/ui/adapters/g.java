package com.loc.va.ui.adapters;

import android.content.Context;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import androidx.recyclerview.widget.RecyclerView;
import b.j0;
import com.loc.va.c;
import java.util.ArrayList;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class g extends RecyclerView.g<b> {
    

    /* renamed from: d, reason: collision with root package name */
    private static String f23000d = "BluetootAdapter";

    /* renamed from: a, reason: collision with root package name */
    private LayoutInflater f23001a;

    /* renamed from: b, reason: collision with root package name */
    private List<com.loc.va.model.i> f23002b;

    /* renamed from: c, reason: collision with root package name */
    private a f23003c;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    public interface a {
        void a(View view, int i5, com.loc.va.model.i iVar);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    public class b extends RecyclerView.e0 {

        /* renamed from: a, reason: collision with root package name */
        TextView f23004a;

        /* renamed from: b, reason: collision with root package name */
        TextView f23005b;

        /* renamed from: c, reason: collision with root package name */
        TextView f23006c;

        /* renamed from: d, reason: collision with root package name */
        TextView f23007d;

        /* renamed from: e, reason: collision with root package name */
        Button f23008e;

        b(View view) {
            super(view);
            this.f23004a = (TextView) view.findViewById(c.i.Z4);
            this.f23005b = (TextView) view.findViewById(c.i.W4);
            this.f23006c = (TextView) view.findViewById(c.i.N4);
            this.f23007d = (TextView) view.findViewById(c.i.M4);
            this.f23008e = (Button) view.findViewById(c.i.f21792x2);
        }
    }

    

    public g(Context context) {
        this.f23001a = LayoutInflater.from(context);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void c(int i5, com.loc.va.model.i iVar, View view) {
        a aVar = this.f23003c;
        if (aVar != null) {
            aVar.a(view, i5, iVar);
        }
    }

    public void b(com.loc.va.model.i iVar) {
        if (this.f23002b == null) {
            this.f23002b = new ArrayList();
        }
        this.f23002b.add(iVar);
        notifyDataSetChanged();
    }

    public void d(int i5, int i6) {
        this.f23002b.add(i6, this.f23002b.remove(i5));
        notifyItemMoved(i5, i6);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    /* renamed from: e, reason: merged with bridge method [inline-methods] */
    public void onBindViewHolder(@j0 b bVar, final int i5) {
        TextView textView;
        String $2;
        final com.loc.va.model.i iVar = this.f23002b.get(i5);
        String str = iVar.f22654a;
        if (str != null) {
            bVar.f23004a.setText(str);
        }
        String str2 = iVar.f22655b;
        if (str2 != null) {
            bVar.f23005b.setText(str2);
        }
        String str3 = iVar.f22656c;
        if (str3 != null) {
            bVar.f23006c.setText(str3);
        }
        if (TextUtils.isEmpty(iVar.f22657d)) {
            textView = bVar.f23007d;
            $2 = "未知";
        } else {
            textView = bVar.f23007d;
            $2 = iVar.f22657d;
        }
        textView.setText($2);
        bVar.f23008e.setOnClickListener(new View.OnClickListener() { // from class: com.loc.va.ui.adapters.f
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                g.this.c(i5, iVar, view);
            }
        });
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    @j0
    /* renamed from: f, reason: merged with bridge method [inline-methods] */
    public b onCreateViewHolder(@j0 ViewGroup viewGroup, int i5) {
        return new b(this.f23001a.inflate(c.l.W0, viewGroup, false));
    }

    public void g(com.loc.va.model.i iVar) {
        int indexOf = this.f23002b.indexOf(iVar);
        if (indexOf >= 0) {
            notifyItemChanged(indexOf);
        }
        notifyDataSetChanged();
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemCount() {
        List<com.loc.va.model.i> list = this.f23002b;
        if (list == null) {
            return 0;
        }
        return list.size();
    }

    public void h(int i5) {
        this.f23002b.remove(i5);
        notifyItemRemoved(i5);
        notifyItemRangeChanged(i5, this.f23002b.size());
    }

    public void i(List<com.loc.va.model.i> list) {
        this.f23002b = list;
        notifyDataSetChanged();
    }

    public void j(a aVar) {
        this.f23003c = aVar;
    }
}
