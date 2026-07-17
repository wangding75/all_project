package com.youth.banner.indicator;

import android.content.Context;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.View;
import android.widget.FrameLayout;
import b.j0;
import b.k0;
import com.google.android.material.badge.BadgeDrawable;
import com.youth.banner.config.IndicatorConfig;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class BaseIndicator extends View implements Indicator {
    protected IndicatorConfig config;
    protected Paint mPaint;
    protected float offset;

    public BaseIndicator(Context context) {
        this(context, null);
    }

    public BaseIndicator(Context context, @k0 AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public BaseIndicator(Context context, @k0 AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.config = new IndicatorConfig();
        Paint paint = new Paint();
        this.mPaint = paint;
        paint.setAntiAlias(true);
        this.mPaint.setColor(this.config.getNormalColor());
    }

    @Override // com.youth.banner.indicator.Indicator
    public IndicatorConfig getIndicatorConfig() {
        return this.config;
    }

    @Override // com.youth.banner.indicator.Indicator
    @j0
    public View getIndicatorView() {
        int i5;
        if (this.config.isAttachToBanner()) {
            FrameLayout.LayoutParams layoutParams = new FrameLayout.LayoutParams(-2, -2);
            int gravity = this.config.getGravity();
            if (gravity == 0) {
                i5 = BadgeDrawable.f18614t;
            } else if (gravity != 1) {
                if (gravity == 2) {
                    i5 = BadgeDrawable.f18613s;
                }
                layoutParams.leftMargin = this.config.getMargins().leftMargin;
                layoutParams.rightMargin = this.config.getMargins().rightMargin;
                layoutParams.topMargin = this.config.getMargins().topMargin;
                layoutParams.bottomMargin = this.config.getMargins().bottomMargin;
                setLayoutParams(layoutParams);
            } else {
                i5 = 81;
            }
            layoutParams.gravity = i5;
            layoutParams.leftMargin = this.config.getMargins().leftMargin;
            layoutParams.rightMargin = this.config.getMargins().rightMargin;
            layoutParams.topMargin = this.config.getMargins().topMargin;
            layoutParams.bottomMargin = this.config.getMargins().bottomMargin;
            setLayoutParams(layoutParams);
        }
        return this;
    }

    @Override // com.youth.banner.indicator.Indicator
    public void onPageChanged(int i5, int i6) {
        this.config.setIndicatorSize(i5);
        this.config.setCurrentPosition(i6);
        requestLayout();
    }

    @Override // com.youth.banner.listener.OnPageChangeListener
    public void onPageScrollStateChanged(int i5) {
    }

    @Override // com.youth.banner.listener.OnPageChangeListener
    public void onPageScrolled(int i5, float f5, int i6) {
        this.offset = f5;
        invalidate();
    }

    @Override // com.youth.banner.listener.OnPageChangeListener
    public void onPageSelected(int i5) {
        this.config.setCurrentPosition(i5);
        invalidate();
    }
}
