package com.loc.va.ui.widget.progress;

import android.view.animation.Interpolator;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
class HesitateInterpolator implements Interpolator {
    private static double POW = 0.5d;

    HesitateInterpolator() {
    }

    @Override // android.animation.TimeInterpolator
    public float getInterpolation(float f5) {
        return ((double) f5) < 0.5d ? ((float) Math.pow(f5 * 2.0f, POW)) * 0.5f : (((float) Math.pow((1.0f - f5) * 2.0f, POW)) * (-0.5f)) + 1.0f;
    }
}
