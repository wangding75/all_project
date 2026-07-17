package com.youth.banner.transformer;

import android.view.View;
import b.j0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class RotateYTransformer extends BasePageTransformer {
    private static final float DEFAULT_MAX_ROTATE = 35.0f;
    private float mMaxRotate;

    public RotateYTransformer() {
        this.mMaxRotate = DEFAULT_MAX_ROTATE;
    }

    public RotateYTransformer(float f5) {
        this.mMaxRotate = f5;
    }

    @Override // androidx.viewpager2.widget.ViewPager2.PageTransformer
    public void transformPage(@j0 View view, float f5) {
        view.setPivotY(view.getHeight() / 2);
        if (f5 >= -1.0f) {
            if (f5 <= 1.0f) {
                view.setRotationY(this.mMaxRotate * f5);
                if (f5 < 0.0f) {
                    view.setPivotX(view.getWidth() * (((-f5) * 0.5f) + 0.5f));
                } else {
                    view.setPivotX(view.getWidth() * 0.5f * (1.0f - f5));
                }
            } else {
                view.setRotationY(this.mMaxRotate * 1.0f);
            }
            view.setPivotX(0.0f);
            return;
        }
        view.setRotationY(this.mMaxRotate * (-1.0f));
        view.setPivotX(view.getWidth());
    }
}
