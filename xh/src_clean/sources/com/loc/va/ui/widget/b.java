package com.loc.va.ui.widget;

import android.animation.ValueAnimator;
import android.graphics.Canvas;
import android.graphics.Paint;
import java.net.HttpURLConnection;
import java.util.ArrayList;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class b extends l {

    /* renamed from: h, reason: collision with root package name */
    private static final int f23202h = 255;

    /* renamed from: i, reason: collision with root package name */
    private static final int[] f23203i = {255, 255, 255, 255, 255, 255, 255, 255, 255};

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void x(int i5, ValueAnimator valueAnimator) {
        f23203i[i5] = ((Integer) valueAnimator.getAnimatedValue()).intValue();
        q();
    }

    @Override // com.loc.va.ui.widget.l
    public void g(Canvas canvas, Paint paint) {
        float n5 = (n() - 16.0f) / 6.0f;
        float f5 = 2.0f * n5;
        float f6 = f5 + 4.0f;
        float n6 = (n() / 2) - f6;
        float n7 = (n() / 2) - f6;
        for (int i5 = 0; i5 < 3; i5++) {
            for (int i6 = 0; i6 < 3; i6++) {
                canvas.save();
                float f7 = i6;
                float f8 = (f5 * f7) + n6 + (f7 * 4.0f);
                float f9 = i5;
                canvas.translate(f8, (f5 * f9) + n7 + (f9 * 4.0f));
                paint.setAlpha(f23203i[(i5 * 3) + i6]);
                canvas.drawCircle(0.0f, 0.0f, n5, paint);
                canvas.restore();
            }
        }
    }

    @Override // com.loc.va.ui.widget.l
    public ArrayList<ValueAnimator> p() {
        ArrayList<ValueAnimator> arrayList = new ArrayList<>();
        int[] iArr = {960, 930, 1190, 1130, 1340, 940, 1200, 820, 1190};
        int[] iArr2 = {360, 400, 680, HttpURLConnection.HTTP_GONE, 710, -150, -120, 10, 320};
        for (final int i5 = 0; i5 < 9; i5++) {
            ValueAnimator ofInt = ValueAnimator.ofInt(255, 168, 255);
            ofInt.setDuration(iArr[i5]);
            ofInt.setRepeatCount(-1);
            ofInt.setStartDelay(iArr2[i5]);
            a(ofInt, new ValueAnimator.AnimatorUpdateListener() { // from class: com.loc.va.ui.widget.a
                @Override // android.animation.ValueAnimator.AnimatorUpdateListener
                public final void onAnimationUpdate(ValueAnimator valueAnimator) {
                    b.this.x(i5, valueAnimator);
                }
            });
            arrayList.add(ofInt);
        }
        return arrayList;
    }
}
