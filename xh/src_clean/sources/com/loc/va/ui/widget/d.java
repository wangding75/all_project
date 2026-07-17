package com.loc.va.ui.widget;

import android.animation.ValueAnimator;
import android.graphics.Canvas;
import android.graphics.Paint;
import java.util.ArrayList;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class d extends l {

    /* renamed from: i, reason: collision with root package name */
    public static final float f23206i = 1.0f;

    /* renamed from: h, reason: collision with root package name */
    private float[] f23207h = {1.0f, 1.0f, 1.0f};

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void x(int i5, ValueAnimator valueAnimator) {
        this.f23207h[i5] = ((Float) valueAnimator.getAnimatedValue()).floatValue();
        q();
    }

    @Override // com.loc.va.ui.widget.l
    public void g(Canvas canvas, Paint paint) {
        float min = (Math.min(n(), m()) - 8.0f) / 6.0f;
        float f5 = 2.0f * min;
        float n5 = (n() / 2) - (f5 + 4.0f);
        float m5 = m() / 2;
        for (int i5 = 0; i5 < 3; i5++) {
            canvas.save();
            float f6 = i5;
            canvas.translate((f5 * f6) + n5 + (f6 * 4.0f), m5);
            float f7 = this.f23207h[i5];
            canvas.scale(f7, f7);
            canvas.drawCircle(0.0f, 0.0f, min, paint);
            canvas.restore();
        }
    }

    @Override // com.loc.va.ui.widget.l
    public ArrayList<ValueAnimator> p() {
        ArrayList<ValueAnimator> arrayList = new ArrayList<>();
        int[] iArr = {120, 240, 360};
        for (final int i5 = 0; i5 < 3; i5++) {
            ValueAnimator ofFloat = ValueAnimator.ofFloat(1.0f, 0.3f, 1.0f);
            ofFloat.setDuration(750L);
            ofFloat.setRepeatCount(-1);
            ofFloat.setStartDelay(iArr[i5]);
            a(ofFloat, new ValueAnimator.AnimatorUpdateListener() { // from class: com.loc.va.ui.widget.c
                @Override // android.animation.ValueAnimator.AnimatorUpdateListener
                public final void onAnimationUpdate(ValueAnimator valueAnimator) {
                    d.this.x(i5, valueAnimator);
                }
            });
            arrayList.add(ofFloat);
        }
        return arrayList;
    }
}
