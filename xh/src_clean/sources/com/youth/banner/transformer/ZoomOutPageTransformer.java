package com.youth.banner.transformer;

import android.view.View;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class ZoomOutPageTransformer extends BasePageTransformer {
    private static final float DEFAULT_MIN_ALPHA = 0.5f;
    private static final float DEFAULT_MIN_SCALE = 0.85f;
    private float mMinAlpha;
    private float mMinScale;

    public ZoomOutPageTransformer() {
        this.mMinScale = DEFAULT_MIN_SCALE;
        this.mMinAlpha = 0.5f;
    }

    public ZoomOutPageTransformer(float f5, float f6) {
        this.mMinScale = f5;
        this.mMinAlpha = f6;
    }

    @Override // androidx.viewpager2.widget.ViewPager2.PageTransformer
    public void transformPage(View view, float f5) {
        int width = view.getWidth();
        int height = view.getHeight();
        if (f5 < -1.0f || f5 > 1.0f) {
            view.setAlpha(0.0f);
            return;
        }
        float max = Math.max(this.mMinScale, 1.0f - Math.abs(f5));
        float f6 = 1.0f - max;
        float f7 = (height * f6) / 2.0f;
        float f8 = (width * f6) / 2.0f;
        if (f5 < 0.0f) {
            view.setTranslationX(f8 - (f7 / 2.0f));
        } else {
            view.setTranslationX((-f8) + (f7 / 2.0f));
        }
        view.setScaleX(max);
        view.setScaleY(max);
        float f9 = this.mMinAlpha;
        float f10 = this.mMinScale;
        view.setAlpha(f9 + (((max - f10) / (1.0f - f10)) * (1.0f - f9)));
    }
}
