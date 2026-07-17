package com.youth.banner.transformer;

import android.view.View;
import b.j0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class RotateDownPageTransformer extends BasePageTransformer {
    private static final float DEFAULT_MAX_ROTATE = 15.0f;
    private float mMaxRotate;

    public RotateDownPageTransformer() {
        this.mMaxRotate = DEFAULT_MAX_ROTATE;
    }

    public RotateDownPageTransformer(float f5) {
        this.mMaxRotate = f5;
    }

    @Override // androidx.viewpager2.widget.ViewPager2.PageTransformer
    public void transformPage(@j0 View view, float f5) {
        int width;
        if (f5 < -1.0f) {
            view.setRotation(this.mMaxRotate * (-1.0f));
            width = view.getWidth();
        } else {
            if (f5 <= 1.0f) {
                if (f5 < 0.0f) {
                    view.setPivotX(view.getWidth() * (((-f5) * 0.5f) + 0.5f));
                } else {
                    view.setPivotX(view.getWidth() * 0.5f * (1.0f - f5));
                }
                view.setPivotY(view.getHeight());
                view.setRotation(this.mMaxRotate * f5);
                return;
            }
            view.setRotation(this.mMaxRotate);
            width = view.getWidth() * 0;
        }
        view.setPivotX(width);
        view.setPivotY(view.getHeight());
    }
}
