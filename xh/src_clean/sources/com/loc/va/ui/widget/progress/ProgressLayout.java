package com.loc.va.ui.widget.progress;

import android.annotation.TargetApi;
import android.content.Context;
import android.content.res.TypedArray;
import android.util.AttributeSet;
import android.widget.FrameLayout;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class ProgressLayout extends FrameLayout {
    private static final int DEFAULT_COUNT = 5;
    private int spotsCount;

    public ProgressLayout(Context context) {
        this(context, null);
    }

    public ProgressLayout(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public ProgressLayout(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        init(attributeSet, i5, 0);
    }

    @TargetApi(21)
    public ProgressLayout(Context context, AttributeSet attributeSet, int i5, int i6) {
        super(context, attributeSet, i5, i6);
        init(attributeSet, i5, i6);
    }

    private void init(AttributeSet attributeSet, int i5, int i6) {
        TypedArray obtainStyledAttributes = getContext().getTheme().obtainStyledAttributes(attributeSet, c.r.fe, i5, i6);
        this.spotsCount = obtainStyledAttributes.getInt(1, 5);
        obtainStyledAttributes.recycle();
    }

    public int getSpotsCount() {
        return this.spotsCount;
    }
}
