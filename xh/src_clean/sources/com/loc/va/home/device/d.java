package com.loc.va.home.device;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ListAdapter;
import android.widget.ListView;
import androidx.fragment.app.Fragment;
import b.k0;
import com.loc.va.c;
import com.loc.va.ui.adapters.j;
import com.lody.virtual.os.VUserInfo;
import java.util.ArrayList;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class d extends Fragment {
    

    /* renamed from: d, reason: collision with root package name */
    private ListView f22584d;

    /* renamed from: e, reason: collision with root package name */
    private j f22585e;

    

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void g(AdapterView adapterView, View view, int i5, long j5) {
        DeviceDetailActiivty.s0(this, this.f22585e.j(i5), i5);
    }

    public static d h() {
        return new d();
    }

    @Override // androidx.fragment.app.Fragment
    public void onActivityResult(int i5, int i6, Intent intent) {
        super.onActivityResult(i5, i6, intent);
        if (i6 != -1 || intent == null || intent.getIntExtra("pos", -1) < 0) {
            return;
        }
        this.f22585e.notifyDataSetChanged();
    }

    @Override // androidx.fragment.app.Fragment
    public void onAttach(Context context) {
        super.onAttach(context);
    }

    @Override // androidx.fragment.app.Fragment
    @k0
    public View onCreateView(LayoutInflater layoutInflater, ViewGroup viewGroup, Bundle bundle) {
        return layoutInflater.inflate(c.l.T0, (ViewGroup) null);
    }

    @Override // androidx.fragment.app.Fragment
    public void onDetach() {
        super.onDetach();
    }

    @Override // androidx.fragment.app.Fragment
    public void onResume() {
        super.onResume();
        j jVar = this.f22585e;
        if (jVar != null) {
            jVar.notifyDataSetChanged();
        }
    }

    @Override // androidx.fragment.app.Fragment
    public void onSaveInstanceState(Bundle bundle) {
        super.onSaveInstanceState(bundle);
    }

    @Override // androidx.fragment.app.Fragment
    public void onViewCreated(View view, Bundle bundle) {
        this.f22584d = (ListView) view.findViewById(c.i.g7);
        this.f22585e = new j(getContext());
        int g5 = com.lody.virtual.os.d.b().g();
        ArrayList arrayList = new ArrayList(g5);
        for (int i5 = 0; i5 < g5; i5++) {
            VUserInfo l5 = com.lody.virtual.os.d.b().l(i5);
            if (l5 != null) {
                com.loc.va.model.j jVar = new com.loc.va.model.j(getContext(), null, l5.f24641a);
                jVar.f22689c = l5.f24643c;
                arrayList.add(jVar);
            }
        }
        this.f22585e.p(arrayList);
        this.f22584d.setAdapter((ListAdapter) this.f22585e);
        this.f22584d.setOnItemClickListener(new AdapterView.OnItemClickListener() { // from class: com.loc.va.home.device.c
            @Override // android.widget.AdapterView.OnItemClickListener
            public final void onItemClick(AdapterView adapterView, View view2, int i6, long j5) {
                d.this.g(adapterView, view2, i6, j5);
            }
        });
    }
}
