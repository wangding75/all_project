package com.youth.banner.indicator;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.AttributeSet;
import b.k0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class RoundLinesIndicator extends BaseIndicator {
    public RoundLinesIndicator(Context context) {
        this(context, null);
    }

    public RoundLinesIndicator(Context context, @k0 AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public RoundLinesIndicator(Context context, @k0 AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.mPaint.setStyle(Paint.Style.FILL);
    }

    @Override // android.view.View
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (this.config.getIndicatorSize() <= 1) {
            return;
        }
        this.mPaint.setColor(this.config.getNormalColor());
        canvas.drawRoundRect(new RectF(0.0f, 0.0f, canvas.getWidth(), this.config.getHeight()), this.config.getRadius(), this.config.getRadius(), this.mPaint);
        this.mPaint.setColor(this.config.getSelectedColor());
        canvas.drawRoundRect(new RectF(this.config.getCurrentPosition() * this.config.getSelectedWidth(), 0.0f, r0 + this.config.getSelectedWidth(), this.config.getHeight()), this.config.getRadius(), this.config.getRadius(), this.mPaint);
    }

    @Override // android.view.View
    protected void onMeasure(int i5, int i6) {
        super.onMeasure(i5, i6);
        int indicatorSize = this.config.getIndicatorSize();
        if (indicatorSize <= 1) {
            return;
        }
        setMeasuredDimension(this.config.getSelectedWidth() * indicatorSize, this.config.getHeight());
    }
}
