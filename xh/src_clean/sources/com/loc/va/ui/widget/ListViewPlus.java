package com.loc.va.ui.widget;

import android.content.Context;
import android.util.AttributeSet;
import android.widget.ListView;
import androidx.core.view.p0;
import androidx.core.view.q0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class ListViewPlus extends ListView implements p0 {

    /* renamed from: a, reason: collision with root package name */
    private final q0 f23134a;

    public ListViewPlus(Context context) {
        this(context, null);
    }

    public ListViewPlus(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public ListViewPlus(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23134a = new q0(this);
        setNestedScrollingEnabled(true);
    }

    @Override // android.view.View, androidx.core.view.p0
    public boolean dispatchNestedFling(float f5, float f6, boolean z5) {
        return this.f23134a.a(f5, f6, z5);
    }

    @Override // android.view.View, androidx.core.view.p0
    public boolean dispatchNestedPreFling(float f5, float f6) {
        return this.f23134a.b(f5, f6);
    }

    @Override // android.view.View, androidx.core.view.p0
    public boolean dispatchNestedPreScroll(int i5, int i6, int[] iArr, int[] iArr2) {
        return this.f23134a.c(i5, i6, iArr, iArr2);
    }

    @Override // android.view.View, androidx.core.view.p0
    public boolean dispatchNestedScroll(int i5, int i6, int i7, int i8, int[] iArr) {
        return this.f23134a.f(i5, i6, i7, i8, iArr);
    }

    @Override // android.view.View, androidx.core.view.p0
    public boolean hasNestedScrollingParent() {
        return this.f23134a.k();
    }

    @Override // android.view.View, androidx.core.view.p0
    public boolean isNestedScrollingEnabled() {
        return this.f23134a.m();
    }

    @Override // android.view.View, androidx.core.view.p0
    public void setNestedScrollingEnabled(boolean z5) {
        this.f23134a.p(z5);
    }

    @Override // android.view.View, androidx.core.view.p0
    public boolean startNestedScroll(int i5) {
        return this.f23134a.r(i5);
    }

    @Override // android.view.View, androidx.core.view.p0
    public void stopNestedScroll() {
        this.f23134a.t();
    }
}
