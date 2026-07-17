package com.youth.banner.transformer;

import android.view.View;
import b.j0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class AlphaPageTransformer extends BasePageTransformer {
    private static final float DEFAULT_MIN_ALPHA = 0.5f;
    private float mMinAlpha;

    public AlphaPageTransformer() {
        this.mMinAlpha = 0.5f;
    }

    public AlphaPageTransformer(float f5) {
        this.mMinAlpha = f5;
    }

    @Override // androidx.viewpager2.widget.ViewPager2.PageTransformer
    public void transformPage(@j0 View view, float f5) {
        float f6;
        float f7;
        view.setScaleX(0.999f);
        if (f5 < -1.0f || f5 > 1.0f) {
            view.setAlpha(this.mMinAlpha);
            return;
        }
        if (f5 < 0.0f) {
            f6 = this.mMinAlpha;
            f7 = (1.0f - f6) * (f5 + 1.0f);
        } else {
            f6 = this.mMinAlpha;
            f7 = (1.0f - f6) * (1.0f - f5);
        }
        view.setAlpha(f6 + f7);
    }
}
