package com.loc.va.ui.widget.progress;

import android.content.Context;
import android.view.View;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
class AnimatedView extends View {
    private int target;

    public AnimatedView(Context context) {
        super(context);
    }

    public int getTarget() {
        return this.target;
    }

    public float getXFactor() {
        return getX() / this.target;
    }

    public void setTarget(int i5) {
        this.target = i5;
    }

    public void setXFactor(float f5) {
        setX(this.target * f5);
    }
}
