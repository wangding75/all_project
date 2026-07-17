package com.youth.banner.indicator;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.RectF;
import android.util.AttributeSet;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class RectangleIndicator extends BaseIndicator {
    RectF rectF;

    public RectangleIndicator(Context context) {
        this(context, null);
    }

    public RectangleIndicator(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public RectangleIndicator(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.rectF = new RectF();
    }

    @Override // android.view.View
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        int indicatorSize = this.config.getIndicatorSize();
        if (indicatorSize <= 1) {
            return;
        }
        int i5 = 0;
        float f5 = 0.0f;
        while (i5 < indicatorSize) {
            this.mPaint.setColor(this.config.getCurrentPosition() == i5 ? this.config.getSelectedColor() : this.config.getNormalColor());
            this.rectF.set(f5, 0.0f, (this.config.getCurrentPosition() == i5 ? this.config.getSelectedWidth() : this.config.getNormalWidth()) + f5, this.config.getHeight());
            f5 += r4 + this.config.getIndicatorSpace();
            canvas.drawRoundRect(this.rectF, this.config.getRadius(), this.config.getRadius(), this.mPaint);
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
        int i7 = indicatorSize - 1;
        setMeasuredDimension((this.config.getIndicatorSpace() * i7) + (this.config.getNormalWidth() * i7) + this.config.getSelectedWidth(), this.config.getHeight());
    }
}
