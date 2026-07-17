package com.loc.va.ui.widget;

import android.app.AlertDialog;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.widget.ImageButton;
import android.widget.TextView;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class t extends AlertDialog {

    /* renamed from: a, reason: collision with root package name */
    private View.OnClickListener f23455a;

    /* renamed from: b, reason: collision with root package name */
    private CharSequence f23456b;

    /* renamed from: c, reason: collision with root package name */
    private TextView f23457c;

    /* renamed from: d, reason: collision with root package name */
    private ImageButton f23458d;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    static /* synthetic */ class a {
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    public static class b {

        /* renamed from: a, reason: collision with root package name */
        private boolean f23459a = true;

        /* renamed from: b, reason: collision with root package name */
        private Context f23460b;

        /* renamed from: c, reason: collision with root package name */
        private View.OnClickListener f23461c;

        /* renamed from: d, reason: collision with root package name */
        private String f23462d;

        /* renamed from: e, reason: collision with root package name */
        private int f23463e;

        public t a() {
            int i5 = this.f23463e;
            return new t(this.f23460b, i5 != 0 ? this.f23460b.getString(i5) : this.f23462d, this.f23459a, this.f23461c, null);
        }

        public b b(boolean z5) {
            this.f23459a = z5;
            return this;
        }

        public b c(Context context) {
            this.f23460b = context;
            return this;
        }

        public b d(int i5) {
            this.f23463e = i5;
            return this;
        }

        public b e(String str) {
            this.f23462d = str;
            return this;
        }

        public b f(View.OnClickListener onClickListener) {
            this.f23461c = onClickListener;
            return this;
        }
    }

    private t(Context context, String str, boolean z5, View.OnClickListener onClickListener) {
        super(context);
        this.f23456b = str;
        setCancelable(z5);
        this.f23455a = onClickListener;
    }

    /* synthetic */ t(Context context, String str, boolean z5, View.OnClickListener onClickListener, a aVar) {
        this(context, str, z5, onClickListener);
    }

    private void a() {
        if (this.f23455a != null) {
            ImageButton imageButton = (ImageButton) findViewById(2131296892);
            this.f23458d = imageButton;
            imageButton.setOnClickListener(this.f23455a);
        }
    }

    private void b() {
        CharSequence charSequence = this.f23456b;
        if (charSequence == null || charSequence.length() <= 0) {
            return;
        }
        TextView textView = (TextView) findViewById(c.i.Vc);
        this.f23457c = textView;
        textView.setText(this.f23456b);
    }

    @Override // android.app.AlertDialog, android.app.Dialog
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        setContentView(c.l.f21887k2);
        setCanceledOnTouchOutside(false);
        setCancelable(false);
        b();
        a();
    }

    @Override // android.app.AlertDialog
    public void setMessage(CharSequence charSequence) {
        this.f23456b = charSequence;
        if (isShowing()) {
            b();
        }
    }
}
