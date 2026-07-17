package com.loc.va.ui.widget.dialog;

import android.R;
import android.app.Dialog;
import android.content.Context;
import android.os.Bundle;
import android.text.Html;
import android.text.SpannableStringBuilder;
import android.text.method.LinkMovementMethod;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class c extends Dialog {
    

    /* renamed from: a, reason: collision with root package name */
    private Context f23219a;

    /* renamed from: b, reason: collision with root package name */
    public LinearLayout f23220b;

    /* renamed from: c, reason: collision with root package name */
    private TextView f23221c;

    /* renamed from: d, reason: collision with root package name */
    private TextView f23222d;

    /* renamed from: e, reason: collision with root package name */
    private EditText f23223e;

    /* renamed from: f, reason: collision with root package name */
    private Button f23224f;

    /* renamed from: g, reason: collision with root package name */
    private View f23225g;

    /* renamed from: h, reason: collision with root package name */
    private Button f23226h;

    /* renamed from: i, reason: collision with root package name */
    private String f23227i;

    /* renamed from: j, reason: collision with root package name */
    private String f23228j;

    /* renamed from: k, reason: collision with root package name */
    private SpannableStringBuilder f23229k;

    /* renamed from: l, reason: collision with root package name */
    private String f23230l;

    /* renamed from: m, reason: collision with root package name */
    private String f23231m;

    /* renamed from: n, reason: collision with root package name */
    private int f23232n;

    /* renamed from: o, reason: collision with root package name */
    private int f23233o;

    /* renamed from: p, reason: collision with root package name */
    private d f23234p;

    /* renamed from: q, reason: collision with root package name */
    private e f23235q;

    /* renamed from: r, reason: collision with root package name */
    private InterfaceC0214c f23236r;

    /* renamed from: s, reason: collision with root package name */
    private boolean f23237s;

    /* renamed from: t, reason: collision with root package name */
    private String f23238t;

    /* renamed from: u, reason: collision with root package name */
    private String f23239u;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class a implements View.OnClickListener {
        a() {
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            if (c.this.f23237s) {
                c cVar = c.this;
                cVar.f23238t = cVar.f23223e.getText().toString().trim();
            }
            c.this.dismiss();
            if (c.this.f23235q != null) {
                c.this.f23235q.a();
            }
            if (!c.this.f23237s || c.this.f23236r == null || d5.b.e(c.this.f23223e.getText().toString().trim())) {
                return;
            }
            c.this.f23236r.a(c.this.f23223e.getText().toString().trim());
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class b implements View.OnClickListener {
        b() {
        }

        @Override // android.view.View.OnClickListener
        public void onClick(View view) {
            c.this.dismiss();
            if (c.this.f23234p != null) {
                c.this.f23234p.a();
            }
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* renamed from: com.loc.va.ui.widget.dialog.c$c, reason: collision with other inner class name */
    public interface InterfaceC0214c {
        void a(String str);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    public interface d {
        void a();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    public interface e {
        void a();
    }

    

    public c(Context context) {
        super(context);
        this.f23219a = context;
    }

    public c(Context context, int i5) {
        super(context, i5);
        this.f23219a = context;
    }

    private void h() {
        String str = this.f23227i;
        if (str != null) {
            this.f23221c.setText(str);
        }
        String str2 = this.f23228j;
        if (str2 != null) {
            if (str2.contains("<")) {
                this.f23222d.setText(Html.fromHtml(this.f23228j));
                this.f23222d.setMovementMethod(LinkMovementMethod.getInstance());
            } else {
                this.f23222d.setAutoLinkMask(15);
                this.f23222d.setText(this.f23228j);
            }
        }
        SpannableStringBuilder spannableStringBuilder = this.f23229k;
        if (spannableStringBuilder != null) {
            this.f23222d.setText(spannableStringBuilder);
            this.f23222d.setMovementMethod(LinkMovementMethod.getInstance());
            this.f23222d.setHighlightColor(R.color.transparent);
            if (this.f23222d.length() > 200) {
                this.f23222d.setHeight(this.f23219a.getResources().getDisplayMetrics().heightPixels / 3);
            }
        }
        if (this.f23237s) {
            this.f23223e.setVisibility(0);
        }
        String str3 = this.f23238t;
        if (str3 != null) {
            this.f23223e.setText(str3);
        }
        String str4 = this.f23239u;
        if (str4 != null) {
            this.f23223e.setHint(str4);
            this.f23222d.setVisibility(8);
        }
        int i5 = this.f23232n;
        if (i5 != 0) {
            this.f23224f.setTextColor(i5);
        }
        int i6 = this.f23233o;
        if (i6 != 0) {
            this.f23226h.setTextColor(i6);
        }
        String str5 = this.f23230l;
        if (str5 != null) {
            this.f23224f.setText(str5);
        }
        if (this.f23231m != null) {
            this.f23226h.setVisibility(0);
            this.f23225g.setVisibility(0);
            this.f23226h.setText(this.f23231m);
        } else {
            this.f23226h.setVisibility(8);
            this.f23225g.setVisibility(8);
            this.f23224f.setBackgroundResource(c.h.M2);
        }
    }

    private void i() {
        this.f23224f.setOnClickListener(new a());
        this.f23226h.setOnClickListener(new b());
    }

    private void j() {
        this.f23220b = (LinearLayout) findViewById(c.i.Xb);
        this.f23221c = (TextView) findViewById(c.i.ac);
        this.f23222d = (TextView) findViewById(c.i.Yb);
        this.f23223e = (EditText) findViewById(c.i.Tb);
        this.f23224f = (Button) findViewById(c.i.fc);
        this.f23225g = findViewById(c.i.cc);
        this.f23226h = (Button) findViewById(c.i.Zb);
    }

    public String g() {
        return this.f23238t;
    }

    public void k(boolean z5) {
        this.f23237s = z5;
    }

    public void l(String str) {
        this.f23239u = str;
    }

    public void m(String str) {
        this.f23238t = str;
    }

    public void n(InterfaceC0214c interfaceC0214c) {
        this.f23236r = interfaceC0214c;
    }

    public void o(SpannableStringBuilder spannableStringBuilder) {
        this.f23229k = spannableStringBuilder;
    }

    @Override // android.app.Dialog
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        setContentView(c.l.f21939x2);
        getWindow().setBackgroundDrawableResource(R.color.transparent);
        j();
        h();
        i();
    }

    public void p(String str) {
        this.f23228j = str;
    }

    public void q(String str, int i5, d dVar) {
        if (str != null) {
            this.f23231m = str;
        }
        this.f23233o = i5;
        this.f23234p = dVar;
    }

    public void r(String str, d dVar) {
        if (str != null) {
            this.f23231m = str;
        }
        this.f23234p = dVar;
    }

    public void s(String str) {
        this.f23227i = str;
    }

    @Override // android.app.Dialog
    public void show() {
        super.show();
        Window window = getWindow();
        WindowManager.LayoutParams attributes = window.getAttributes();
        int width = window.getWindowManager().getDefaultDisplay().getWidth();
        if (attributes.width >= 1 || width <= 0) {
            return;
        }
        attributes.width = width - 200;
        window.setAttributes(attributes);
    }

    public void t(String str, int i5, e eVar) {
        if (str != null) {
            this.f23230l = str;
        }
        this.f23232n = i5;
        this.f23235q = eVar;
    }

    public void u(String str, e eVar) {
        if (str != null) {
            this.f23230l = str;
        }
        this.f23235q = eVar;
    }
}
