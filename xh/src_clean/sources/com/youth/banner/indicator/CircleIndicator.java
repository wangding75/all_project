package com.youth.banner.indicator;

import android.content.Context;
import android.graphics.Canvas;
import android.util.AttributeSet;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class CircleIndicator extends BaseIndicator {
    private int mNormalRadius;
    private int mSelectedRadius;
    private int maxRadius;

    public CircleIndicator(Context context) {
        this(context, null);
    }

    public CircleIndicator(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public CircleIndicator(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.mNormalRadius = this.config.getNormalWidth() / 2;
        this.mSelectedRadius = this.config.getSelectedWidth() / 2;
    }

    @Override // android.view.View
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        int indicatorSize = this.config.getIndicatorSize();
        if (indicatorSize <= 1) {
            return;
        }
        float f5 = 0.0f;
        int i5 = 0;
        while (i5 < indicatorSize) {
            this.mPaint.setColor(this.config.getCurrentPosition() == i5 ? this.config.getSelectedColor() : this.config.getNormalColor());
            int selectedWidth = this.config.getCurrentPosition() == i5 ? this.config.getSelectedWidth() : this.config.getNormalWidth();
            float f6 = this.config.getCurrentPosition() == i5 ? this.mSelectedRadius : this.mNormalRadius;
            canvas.drawCircle(f5 + f6, this.maxRadius, f6, this.mPaint);
            f5 += selectedWidth + this.config.getIndicatorSpace();
            i5++;
        }
    }

    @Override // android.view.View
    protected void onMeasure(int i5, int i6) {
        super.onMeasure(i5, i6);
        int indicatorSize = this.config.getIndicatorSize();
        if (indicatorSize <= 1) {
            return;
        }
        this.mNormalRadius = this.config.getNormalWidth() / 2;
        int selectedWidth = this.config.getSelectedWidth() / 2;
        this.mSelectedRadius = selectedWidth;
        this.maxRadius = Math.max(selectedWidth, this.mNormalRadius);
        int i7 = indicatorSize - 1;
        setMeasuredDimension((this.config.getIndicatorSpace() * i7) + this.config.getSelectedWidth() + (this.config.getNormalWidth() * i7), Math.max(this.config.getNormalWidth(), this.config.getSelectedWidth()));
    }
}
