package com.loc.va.ui.widget;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Paint;
import android.graphics.Rect;
import android.util.AttributeSet;
import android.view.View;
import android.view.animation.LinearInterpolator;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public abstract class e extends View {

    /* renamed from: a, reason: collision with root package name */
    public ValueAnimator f23242a;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class a implements ValueAnimator.AnimatorUpdateListener {
        a() {
        }

        @Override // android.animation.ValueAnimator.AnimatorUpdateListener
        public void onAnimationUpdate(ValueAnimator valueAnimator) {
            e.this.d(valueAnimator);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class b extends AnimatorListenerAdapter {
        b() {
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            super.onAnimationEnd(animator);
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationRepeat(Animator animator) {
            super.onAnimationRepeat(animator);
            e.this.c(animator);
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationStart(Animator animator) {
            super.onAnimationStart(animator);
        }
    }

    public e(Context context) {
        this(context, null);
    }

    public e(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public e(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        b();
    }

    private ValueAnimator m(float f5, float f6, long j5) {
        ValueAnimator ofFloat = ValueAnimator.ofFloat(f5, f6);
        this.f23242a = ofFloat;
        ofFloat.setDuration(j5);
        this.f23242a.setInterpolator(new LinearInterpolator());
        this.f23242a.setRepeatCount(f());
        if (1 == g()) {
            this.f23242a.setRepeatMode(1);
        } else if (2 == g()) {
            this.f23242a.setRepeatMode(2);
        }
        this.f23242a.addUpdateListener(new a());
        this.f23242a.addListener(new b());
        if (!this.f23242a.isRunning()) {
            a();
            this.f23242a.start();
        }
        return this.f23242a;
    }

    protected abstract void a();

    protected abstract void b();

    protected abstract void c(Animator animator);

    protected abstract void d(ValueAnimator valueAnimator);

    protected abstract int e();

    protected abstract int f();

    protected abstract int g();

    public float h(Paint paint) {
        Paint.FontMetrics fontMetrics = paint.getFontMetrics();
        return fontMetrics.descent - fontMetrics.ascent;
    }

    public float i(Paint paint, String str) {
        paint.getTextBounds(str, 0, str.length(), new Rect());
        return r0.height();
    }

    public float j(Paint paint, String str) {
        paint.getTextBounds(str, 0, str.length(), new Rect());
        return r0.width();
    }

    public void k() {
        n();
        m(0.0f, 1.0f, 500L);
    }

    public void l(int i5) {
        n();
        m(0.0f, 1.0f, i5);
    }

    public void n() {
        if (this.f23242a != null) {
            clearAnimation();
            this.f23242a.setRepeatCount(0);
            this.f23242a.cancel();
            this.f23242a.end();
            if (e() == 0) {
                this.f23242a.setRepeatCount(0);
                this.f23242a.cancel();
                this.f23242a.end();
            }
        }
    }
}
