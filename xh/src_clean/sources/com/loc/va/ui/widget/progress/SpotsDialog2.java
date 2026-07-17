package com.loc.va.ui.widget.progress;

import android.R;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.os.Bundle;
import android.widget.TextView;
import b.u0;
import b.v0;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class SpotsDialog2 extends AlertDialog {
    private static final int DELAY = 150;
    private static final int DURATION = 1500;
    private AnimatorPlayer animator;
    private CharSequence message;
    private int size;
    private AnimatedView[] spots;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* renamed from: com.loc.va.ui.widget.progress.SpotsDialog2$1, reason: invalid class name */
    static /* synthetic */ class AnonymousClass1 {
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    public static class Builder {
        private DialogInterface.OnCancelListener cancelListener;
        private boolean cancelable = true;
        private Context context;
        private String message;
        private int messageId;
        private int themeId;

        public AlertDialog build() {
            Context context = this.context;
            int i5 = this.messageId;
            String string = i5 != 0 ? context.getString(i5) : this.message;
            int i6 = this.themeId;
            if (i6 == 0) {
                i6 = c.q.M5;
            }
            return new SpotsDialog2(context, string, i6, this.cancelable, this.cancelListener, null);
        }

        public Builder setCancelListener(DialogInterface.OnCancelListener onCancelListener) {
            this.cancelListener = onCancelListener;
            return this;
        }

        public Builder setCancelable(boolean z5) {
            this.cancelable = z5;
            return this;
        }

        public Builder setContext(Context context) {
            this.context = context;
            return this;
        }

        public Builder setMessage(@u0 int i5) {
            this.messageId = i5;
            return this;
        }

        public Builder setMessage(String str) {
            this.message = str;
            return this;
        }

        public Builder setTheme(@v0 int i5) {
            this.themeId = i5;
            return this;
        }
    }

    private SpotsDialog2(Context context, String str, int i5, boolean z5, DialogInterface.OnCancelListener onCancelListener) {
        super(context, i5);
        this.message = str;
        setCancelable(z5);
        if (onCancelListener != null) {
            setOnCancelListener(onCancelListener);
        }
    }

    /* synthetic */ SpotsDialog2(Context context, String str, int i5, boolean z5, DialogInterface.OnCancelListener onCancelListener, AnonymousClass1 anonymousClass1) {
        this(context, str, i5, z5, onCancelListener);
    }

    private void initMessage() {
        CharSequence charSequence = this.message;
        if (charSequence == null || charSequence.length() <= 0) {
            return;
        }
        ((TextView) findViewById(c.i.f21734n4)).setText(this.message);
    }

    @Override // android.app.AlertDialog, android.app.Dialog
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        setContentView(c.l.f21921t0);
        getWindow().setBackgroundDrawableResource(R.color.transparent);
        setCanceledOnTouchOutside(false);
        initMessage();
    }

    @Override // android.app.Dialog
    protected void onStart() {
        super.onStart();
    }

    @Override // android.app.Dialog
    protected void onStop() {
        super.onStop();
    }

    @Override // android.app.AlertDialog
    public void setMessage(CharSequence charSequence) {
        this.message = charSequence;
        if (isShowing()) {
            initMessage();
        }
    }
}
