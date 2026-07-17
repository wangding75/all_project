package com.loc.va.ui.widget.quicksidebar;

import android.content.Context;
import android.util.AttributeSet;
import android.widget.RelativeLayout;
import com.loc.va.ui.widget.quicksidebar.tipsview.QuickSideBarTipsItemView;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class a extends RelativeLayout {

    /* renamed from: a, reason: collision with root package name */
    private QuickSideBarTipsItemView f23430a;

    public a(Context context) {
        this(context, null);
    }

    public a(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public a(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        a(context, attributeSet);
    }

    private void a(Context context, AttributeSet attributeSet) {
        this.f23430a = new QuickSideBarTipsItemView(context, attributeSet);
        addView(this.f23430a, new RelativeLayout.LayoutParams(-1, -2));
    }

    public void b(String str, int i5, float f5) {
        this.f23430a.setText(str);
        RelativeLayout.LayoutParams layoutParams = (RelativeLayout.LayoutParams) this.f23430a.getLayoutParams();
        layoutParams.topMargin = (int) (f5 - (getWidth() / 2.8d));
        this.f23430a.setLayoutParams(layoutParams);
    }
}
