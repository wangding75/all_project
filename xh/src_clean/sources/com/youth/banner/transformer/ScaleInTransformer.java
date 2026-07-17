package com.youth.banner.transformer;

import android.view.View;
import b.j0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class ScaleInTransformer extends BasePageTransformer {
    private static final float DEFAULT_MIN_SCALE = 0.85f;
    private float mMinScale;

    public ScaleInTransformer() {
        this.mMinScale = DEFAULT_MIN_SCALE;
    }

    public ScaleInTransformer(float f5) {
        this.mMinScale = f5;
    }

    @Override // androidx.viewpager2.widget.ViewPager2.PageTransformer
    public void transformPage(@j0 View view, float f5) {
        float f6;
        float f7;
        int width = view.getWidth();
        view.setPivotY(view.getHeight() / 2);
        view.setPivotX(width / 2);
        if (f5 < -1.0f) {
            view.setScaleX(this.mMinScale);
            view.setScaleY(this.mMinScale);
            view.setPivotX(width);
            return;
        }
        if (f5 > 1.0f) {
            view.setPivotX(0.0f);
            view.setScaleX(this.mMinScale);
            view.setScaleY(this.mMinScale);
            return;
        }
        if (f5 < 0.0f) {
            float f8 = this.mMinScale;
            float f9 = ((f5 + 1.0f) * (1.0f - f8)) + f8;
            view.setScaleX(f9);
            view.setScaleY(f9);
            f6 = width;
            f7 = ((-f5) * 0.5f) + 0.5f;
        } else {
            float f10 = 1.0f - f5;
            float f11 = this.mMinScale;
            float f12 = ((1.0f - f11) * f10) + f11;
            view.setScaleX(f12);
            view.setScaleY(f12);
            f6 = width;
            f7 = f10 * 0.5f;
        }
        view.setPivotX(f6 * f7);
    }
}
