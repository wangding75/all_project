package com.loc.va.ui.widget.dialog;

import android.R;
import android.content.Context;
import android.content.DialogInterface;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ListAdapter;
import android.widget.ListView;
import android.widget.TextView;
import b.j0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class b extends com.google.android.material.bottomsheet.a {

    /* renamed from: n, reason: collision with root package name */
    private Context f23208n;

    /* renamed from: o, reason: collision with root package name */
    private TextView f23209o;

    /* renamed from: p, reason: collision with root package name */
    private TextView f23210p;

    /* renamed from: q, reason: collision with root package name */
    private View f23211q;

    /* renamed from: r, reason: collision with root package name */
    private View f23212r;

    /* renamed from: s, reason: collision with root package name */
    private ListView f23213s;

    /* renamed from: t, reason: collision with root package name */
    private String f23214t;

    /* renamed from: u, reason: collision with root package name */
    private String f23215u;

    /* renamed from: v, reason: collision with root package name */
    private String[] f23216v;

    /* renamed from: w, reason: collision with root package name */
    private InterfaceC0213b f23217w;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a implements AdapterView.OnItemClickListener {
        a() {
        }

        @Override // android.widget.AdapterView.OnItemClickListener
        public void onItemClick(AdapterView<?> adapterView, View view, int i5, long j5) {
            if (b.this.f23217w != null) {
                b.this.f23217w.a(i5, b.this.f23216v[i5]);
            }
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* renamed from: com.loc.va.ui.widget.dialog.b$b, reason: collision with other inner class name */
    /* loaded from: D:\github\xh\blackdex_out\classes10.dex */
    public interface InterfaceC0213b {
        void a(int i5, String str);
    }

    public b(@j0 Context context) {
        super(context);
        this.f23208n = context;
    }

    public b(@j0 Context context, int i5) {
        super(context, i5);
        this.f23208n = context;
    }

    protected b(@j0 Context context, boolean z5, DialogInterface.OnCancelListener onCancelListener) {
        super(context, z5, onCancelListener);
        this.f23208n = context;
    }

    private void A() {
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static /* synthetic */ void B(View view) {
    }

    private void y() {
        String str = this.f23214t;
        if (str == null) {
            this.f23209o.setVisibility(8);
            this.f23211q.setVisibility(8);
        } else {
            this.f23209o.setText(str);
        }
        String str2 = this.f23215u;
        if (str2 == null) {
            this.f23212r.setVisibility(8);
            this.f23210p.setVisibility(8);
        } else {
            this.f23210p.setText(str2);
        }
        this.f23213s.setAdapter((ListAdapter) new ArrayAdapter(this.f23208n, R.layout.simple_list_item_1, this.f23216v));
    }

    private void z() {
        this.f23210p.setOnClickListener(new View.OnClickListener() { // from class: com.loc.va.ui.widget.dialog.a
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                b.B(view);
            }
        });
        this.f23213s.setOnItemClickListener(new a());
    }

    public void C(String str) {
        this.f23215u = str;
    }

    public void D(String[] strArr) {
        this.f23216v = strArr;
    }

    public void E(InterfaceC0213b interfaceC0213b) {
        this.f23217w = interfaceC0213b;
    }

    public void F(String str) {
        this.f23214t = str;
    }

    @Override // com.google.android.material.bottomsheet.a, androidx.appcompat.app.l, android.app.Dialog
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        A();
        y();
        z();
    }

    @Override // android.app.Dialog
    public void show() {
        super.show();
        Window window = getWindow();
        WindowManager.LayoutParams attributes = window.getAttributes();
        int width = window.getWindowManager().getDefaultDisplay().getWidth();
        if (width <= 0 || width <= attributes.width) {
            return;
        }
        attributes.width = width;
        window.setAttributes(attributes);
    }
}
