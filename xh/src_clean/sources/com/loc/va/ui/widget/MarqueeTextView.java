package com.loc.va.ui.widget;

import android.content.Context;
import android.util.AttributeSet;
import androidx.appcompat.widget.g0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class MarqueeTextView extends g0 {

    /* renamed from: e, reason: collision with root package name */
    private boolean f23135e;

    public MarqueeTextView(Context context) {
        super(context);
        this.f23135e = false;
    }

    public MarqueeTextView(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        this.f23135e = false;
    }

    public MarqueeTextView(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23135e = false;
    }

    public void c() {
        this.f23135e = false;
    }

    public void i() {
        this.f23135e = true;
    }

    @Override // android.view.View
    public boolean isFocused() {
        if (this.f23135e) {
            return super.isFocused();
        }
        return true;
    }

    @Override // android.view.View
    protected void onDetachedFromWindow() {
        i();
        super.onDetachedFromWindow();
    }
}
