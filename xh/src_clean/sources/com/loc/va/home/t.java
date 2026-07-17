package com.loc.va.home;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Parcelable;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.Toast;
import androidx.recyclerview.widget.StaggeredGridLayoutManager;
import b.k0;
import com.loc.va.c;
import com.loc.va.home.q;
import com.loc.va.model.AppInfoLite;
import com.loc.va.ui.adapters.i;
import com.loc.va.ui.widget.DragSelectRecyclerView;
import com.loc.va.ui.widget.k;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class t extends com.loc.va.abs.ui.b<q.a> implements q.b {
    

    /* renamed from: j, reason: collision with root package name */
    private static String f22613j = "key_select_from";

    /* renamed from: f, reason: collision with root package name */
    private DragSelectRecyclerView f22614f;

    /* renamed from: g, reason: collision with root package name */
    private ProgressBar f22615g;

    /* renamed from: h, reason: collision with root package name */
    private Button f22616h;

    /* renamed from: i, reason: collision with root package name */
    private com.loc.va.ui.adapters.i f22617i;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a implements i.a {
        a() {
        }

        @Override // com.loc.va.ui.adapters.i.a
        public void a(com.loc.va.model.c cVar, int i5) {
            int c6 = t.this.f22617i.c();
            if (t.this.f22617i.f(i5) || c6 < 9) {
                t.this.f22617i.p(i5);
            } else {
                Toast.makeText(t.this.getContext(), c.p.f22004b2, 0).show();
            }
        }

        @Override // com.loc.va.ui.adapters.i.a
        public boolean b(int i5) {
            return t.this.f22617i.f(i5) || t.this.f22617i.c() < 9;
        }
    }

    

    private File o() {
        String string;
        Bundle arguments = getArguments();
        if (arguments == null || (string = arguments.getString("key_select_from")) == null) {
            return null;
        }
        return new File(string);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void p(int i5) {
        boolean z5 = i5 > 0;
        this.f22616h.setTextColor(z5 ? -1 : Color.parseColor("#cfcfcf"));
        this.f22616h.setEnabled(z5);
        this.f22616h.setText(String.format(Locale.ENGLISH, getResources().getString(c.p.U1), Integer.valueOf(i5)));
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void q(View view) {
        Integer[] d6 = this.f22617i.d();
        ArrayList<? extends Parcelable> arrayList = new ArrayList<>(d6.length);
        for (Integer num : d6) {
            arrayList.add(new AppInfoLite(this.f22617i.s(num.intValue())));
        }
        Intent intent = new Intent();
        intent.putParcelableArrayListExtra("va.extra.APP_INFO_LIST", arrayList);
        getActivity().setResult(-1, intent);
        getActivity().finish();
    }

    public static t r(File file) {
        Bundle bundle = new Bundle();
        if (file != null) {
            bundle.putString("key_select_from", file.getPath());
        }
        t tVar = new t();
        tVar.setArguments(bundle);
        return tVar;
    }

    @Override // com.loc.va.home.q.b
    public void b() {
        this.f22615g.setVisibility(0);
        this.f22614f.setVisibility(8);
    }

    @Override // l1.b
    @k0
    public /* bridge */ /* synthetic */ Activity d() {
        return super.getActivity();
    }

    @Override // com.loc.va.home.q.b
    public void loadFinish(List<com.loc.va.model.c> list) {
        if (j()) {
            this.f22617i.x(list);
            this.f22614f.j(false, 0);
            this.f22617i.n(0, false);
            this.f22615g.setVisibility(8);
            this.f22614f.setVisibility(0);
        }
    }

    @Override // androidx.fragment.app.Fragment
    @k0
    public View onCreateView(LayoutInflater layoutInflater, ViewGroup viewGroup, Bundle bundle) {
        return layoutInflater.inflate(c.l.S0, (ViewGroup) null);
    }

    @Override // androidx.fragment.app.Fragment
    public void onSaveInstanceState(Bundle bundle) {
        super.onSaveInstanceState(bundle);
        this.f22617i.i(bundle);
    }

    @Override // androidx.fragment.app.Fragment
    public void onViewCreated(View view, Bundle bundle) {
        this.f22614f = (DragSelectRecyclerView) view.findViewById(c.i.Ba);
        this.f22615g = (ProgressBar) view.findViewById(c.i.Aa);
        this.f22616h = (Button) view.findViewById(c.i.za);
        this.f22614f.setLayoutManager(new StaggeredGridLayoutManager(3, 1));
        this.f22614f.addItemDecoration(new q1.a(com.loc.va.abs.ui.c.b(getContext(), 2)));
        com.loc.va.ui.adapters.i iVar = new com.loc.va.ui.adapters.i(getActivity());
        this.f22617i = iVar;
        this.f22614f.setAdapter((com.loc.va.ui.widget.k<?>) iVar);
        this.f22617i.y(new a());
        this.f22617i.o(new k.a() { // from class: com.loc.va.home.r
            @Override // com.loc.va.ui.widget.k.a
            public final void a(int i5) {
                t.this.p(i5);
            }
        });
        this.f22616h.setOnClickListener(new View.OnClickListener() { // from class: com.loc.va.home.s
            @Override // android.view.View.OnClickListener
            public final void onClick(View view2) {
                t.this.q(view2);
            }
        });
        new v(getActivity(), this, o()).start();
    }

    @Override // com.loc.va.abs.ui.b
    /* renamed from: s, reason: merged with bridge method [inline-methods] and merged with bridge method [inline-methods] */
    public void k(q.a aVar) {
        this.f20958d = aVar;
    }
}
