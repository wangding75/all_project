package com.hjq.toast;

import android.R;
import android.app.Application;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import android.widget.Toast;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
class a extends Toast {
    

    /* renamed from: a, reason: collision with root package name */
    private TextView f20845a;

    

    a(Application application) {
        super(application);
    }

    private static TextView a(ViewGroup viewGroup) {
        TextView a6;
        for (int i5 = 0; i5 < viewGroup.getChildCount(); i5++) {
            View childAt = viewGroup.getChildAt(i5);
            if (childAt instanceof TextView) {
                return (TextView) childAt;
            }
            if ((childAt instanceof ViewGroup) && (a6 = a((ViewGroup) childAt)) != null) {
                return a6;
            }
        }
        return null;
    }

    private static TextView b(View view) {
        TextView a6;
        if (view instanceof TextView) {
            return (TextView) view;
        }
        if (view.findViewById(R.id.message) instanceof TextView) {
            return (TextView) view.findViewById(R.id.message);
        }
        if (!(view instanceof ViewGroup) || (a6 = a((ViewGroup) view)) == null) {
            throw new IllegalArgumentException("The layout must contain a TextView");
        }
        return a6;
    }

    @Override // android.widget.Toast
    public void setText(CharSequence charSequence) {
        this.f20845a.setText(charSequence);
    }

    @Override // android.widget.Toast
    public void setView(View view) {
        super.setView(view);
        this.f20845a = b(view);
    }
}
