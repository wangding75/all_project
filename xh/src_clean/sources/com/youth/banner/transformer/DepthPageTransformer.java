package com.youth.banner.transformer;

import android.view.View;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class DepthPageTransformer extends BasePageTransformer {
    private static final float DEFAULT_MIN_SCALE = 0.75f;
    private float mMinScale;

    public DepthPageTransformer() {
        this.mMinScale = 0.75f;
    }

    public DepthPageTransformer(float f5) {
        this.mMinScale = f5;
    }

    @Override // androidx.viewpager2.widget.ViewPager2.PageTransformer
    public void transformPage(View view, float f5) {
        int width = view.getWidth();
        if (f5 >= -1.0f) {
            if (f5 <= 0.0f) {
                view.setAlpha(1.0f);
                view.setTranslationX(0.0f);
                view.setScaleX(1.0f);
                view.setScaleY(1.0f);
                return;
            }
            if (f5 <= 1.0f) {
                view.setVisibility(0);
                view.setAlpha(1.0f - f5);
                view.setTranslationX(width * (-f5));
                float f6 = this.mMinScale;
                float abs = f6 + ((1.0f - f6) * (1.0f - Math.abs(f5)));
                view.setScaleX(abs);
                view.setScaleY(abs);
                if (f5 == 1.0f) {
                    view.setVisibility(4);
                    return;
                }
                return;
            }
        }
        view.setAlpha(0.0f);
    }
}
