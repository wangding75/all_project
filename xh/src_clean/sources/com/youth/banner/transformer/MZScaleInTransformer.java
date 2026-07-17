package com.youth.banner.transformer;

import android.view.View;
import android.view.ViewParent;
import androidx.recyclerview.widget.RecyclerView;
import androidx.viewpager2.widget.ViewPager2;
import b.j0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class MZScaleInTransformer extends BasePageTransformer {
    
    private static final float DEFAULT_MIN_SCALE = 0.85f;
    private float mMinScale;

    

    public MZScaleInTransformer() {
        this.mMinScale = DEFAULT_MIN_SCALE;
    }

    public MZScaleInTransformer(float f5) {
        this.mMinScale = f5;
    }

    private ViewPager2 requireViewPager(@j0 View view) {
        ViewParent parent = view.getParent();
        ViewParent parent2 = parent.getParent();
        if ((parent instanceof RecyclerView) && (parent2 instanceof ViewPager2)) {
            return (ViewPager2) parent2;
        }
        throw new IllegalStateException("Expected the page view to be managed by a ViewPager2 instance.");
    }

    @Override // androidx.viewpager2.widget.ViewPager2.PageTransformer
    public void transformPage(@j0 View view, float f5) {
        float paddingLeft = requireViewPager(view).getPaddingLeft();
        float measuredWidth = f5 - (paddingLeft / ((r0.getMeasuredWidth() - paddingLeft) - r0.getPaddingRight()));
        float width = view.getWidth();
        float f6 = this.mMinScale;
        float f7 = ((1.0f - f6) * width) / 2.0f;
        if (measuredWidth <= -1.0f) {
            view.setTranslationX(f7);
            view.setScaleX(this.mMinScale);
            view.setScaleY(this.mMinScale);
            return;
        }
        double d6 = measuredWidth;
        if (d6 > 1.0d) {
            view.setScaleX(f6);
            view.setScaleY(this.mMinScale);
            view.setTranslationX(-f7);
            return;
        }
        float abs = (1.0f - f6) * Math.abs(1.0f - Math.abs(measuredWidth));
        float f8 = (-f7) * measuredWidth;
        if (d6 <= -0.5d) {
            f8 += Math.abs(Math.abs(measuredWidth) - 0.5f) / 0.5f;
        } else if (measuredWidth > 0.0f && d6 >= 0.5d) {
            f8 -= Math.abs(Math.abs(measuredWidth) - 0.5f) / 0.5f;
        }
        view.setTranslationX(f8);
        view.setScaleX(this.mMinScale + abs);
        view.setScaleY(abs + this.mMinScale);
    }
}
