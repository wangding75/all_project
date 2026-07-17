package com.loc.va.abs.percent;

import android.content.Context;
import android.content.res.TypedArray;
import android.util.AttributeSet;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import androidx.percentlayout.widget.b;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class a extends LinearLayout {

    /* renamed from: a, reason: collision with root package name */
    private b f20951a;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* renamed from: com.loc.va.abs.percent.a$a, reason: collision with other inner class name */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public static class C0206a extends LinearLayout.LayoutParams implements b.InterfaceC0089b {

        /* renamed from: a, reason: collision with root package name */
        private b.a f20952a;

        public C0206a(int i5, int i6) {
            super(i5, i6);
        }

        public C0206a(Context context, AttributeSet attributeSet) {
            super(context, attributeSet);
            this.f20952a = b.c(context, attributeSet);
        }

        public C0206a(ViewGroup.LayoutParams layoutParams) {
            super(layoutParams);
        }

        public C0206a(ViewGroup.MarginLayoutParams marginLayoutParams) {
            super(marginLayoutParams);
        }

        @Override // androidx.percentlayout.widget.b.InterfaceC0089b
        public b.a a() {
            return this.f20952a;
        }

        @Override // android.view.ViewGroup.LayoutParams
        protected void setBaseAttributes(TypedArray typedArray, int i5, int i6) {
            b.b(this, typedArray, i5, i6);
        }
    }

    public a(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        this.f20951a = new b(this);
    }

    @Override // android.widget.LinearLayout, android.view.ViewGroup
    /* renamed from: a, reason: merged with bridge method [inline-methods] */
    public C0206a generateLayoutParams(AttributeSet attributeSet) {
        return new C0206a(getContext(), attributeSet);
    }

    @Override // android.widget.LinearLayout, android.view.ViewGroup, android.view.View
    protected void onLayout(boolean z5, int i5, int i6, int i7, int i8) {
        super.onLayout(z5, i5, i6, i7, i8);
        this.f20951a.e();
    }

    @Override // android.widget.LinearLayout, android.view.View
    protected void onMeasure(int i5, int i6) {
        this.f20951a.a(i5, i6);
        super.onMeasure(i5, i6);
        if (this.f20951a.d()) {
            super.onMeasure(i5, i6);
        }
    }
}
