package com.loc.va.ui.widget;

import android.animation.Animator;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.util.AttributeSet;
import androidx.core.view.f2;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class EatBeansView extends e {

    /* renamed from: b, reason: collision with root package name */
    int f23080b;

    /* renamed from: c, reason: collision with root package name */
    private Paint f23081c;

    /* renamed from: d, reason: collision with root package name */
    private Paint f23082d;

    /* renamed from: e, reason: collision with root package name */
    private float f23083e;

    /* renamed from: f, reason: collision with root package name */
    private float f23084f;

    /* renamed from: g, reason: collision with root package name */
    private float f23085g;

    /* renamed from: h, reason: collision with root package name */
    private float f23086h;

    /* renamed from: i, reason: collision with root package name */
    private float f23087i;

    /* renamed from: j, reason: collision with root package name */
    private float f23088j;

    /* renamed from: k, reason: collision with root package name */
    private float f23089k;

    /* renamed from: l, reason: collision with root package name */
    private float f23090l;

    /* renamed from: m, reason: collision with root package name */
    private float f23091m;

    public EatBeansView(Context context) {
        super(context);
        this.f23080b = 5;
        this.f23083e = 0.0f;
        this.f23084f = 0.0f;
        this.f23085g = 5.0f;
        this.f23086h = 60.0f;
        this.f23087i = 0.0f;
        this.f23088j = 10.0f;
        this.f23089k = 34.0f;
        this.f23090l = 34.0f;
        this.f23091m = 360.0f - (34.0f * 2.0f);
    }

    public EatBeansView(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        this.f23080b = 5;
        this.f23083e = 0.0f;
        this.f23084f = 0.0f;
        this.f23085g = 5.0f;
        this.f23086h = 60.0f;
        this.f23087i = 0.0f;
        this.f23088j = 10.0f;
        this.f23089k = 34.0f;
        this.f23090l = 34.0f;
        this.f23091m = 360.0f - (34.0f * 2.0f);
    }

    public EatBeansView(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23080b = 5;
        this.f23083e = 0.0f;
        this.f23084f = 0.0f;
        this.f23085g = 5.0f;
        this.f23086h = 60.0f;
        this.f23087i = 0.0f;
        this.f23088j = 10.0f;
        this.f23089k = 34.0f;
        this.f23090l = 34.0f;
        this.f23091m = 360.0f - (34.0f * 2.0f);
    }

    private void o() {
        Paint paint = new Paint();
        this.f23081c = paint;
        paint.setAntiAlias(true);
        this.f23081c.setStyle(Paint.Style.FILL);
        this.f23081c.setColor(-1);
        Paint paint2 = new Paint();
        this.f23082d = paint2;
        paint2.setAntiAlias(true);
        this.f23082d.setStyle(Paint.Style.FILL);
        this.f23082d.setColor(f2.f6745t);
    }

    @Override // com.loc.va.ui.widget.e
    protected void a() {
    }

    @Override // com.loc.va.ui.widget.e
    protected void b() {
        o();
    }

    @Override // com.loc.va.ui.widget.e
    protected void c(Animator animator) {
    }

    @Override // com.loc.va.ui.widget.e
    protected void d(ValueAnimator valueAnimator) {
        float floatValue = ((Float) valueAnimator.getAnimatedValue()).floatValue();
        this.f23087i = ((this.f23083e - (this.f23085g * 2.0f)) - this.f23086h) * floatValue;
        float f5 = this.f23089k * (1.0f - ((this.f23080b * floatValue) - ((int) (floatValue * r1))));
        this.f23090l = f5;
        this.f23091m = 360.0f - (f5 * 2.0f);
        invalidate();
    }

    @Override // com.loc.va.ui.widget.e
    protected int e() {
        this.f23087i = 0.0f;
        postInvalidate();
        return 1;
    }

    @Override // com.loc.va.ui.widget.e
    protected int f() {
        return -1;
    }

    @Override // com.loc.va.ui.widget.e
    protected int g() {
        return 1;
    }

    @Override // android.view.View
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float f5 = this.f23085g + this.f23086h + this.f23087i;
        float f6 = this.f23085g + this.f23087i;
        float f7 = this.f23084f;
        float f8 = this.f23086h;
        canvas.drawArc(new RectF(f6, (f7 / 2.0f) - (f8 / 2.0f), f5, (f7 / 2.0f) + (f8 / 2.0f)), this.f23090l, this.f23091m, true, this.f23081c);
        float f9 = this.f23085g + this.f23087i;
        float f10 = this.f23086h;
        canvas.drawCircle(f9 + (f10 / 2.0f), (this.f23084f / 2.0f) - (f10 / 4.0f), this.f23088j / 2.0f, this.f23082d);
        int i5 = (int) ((((this.f23083e - (this.f23085g * 2.0f)) - this.f23086h) / this.f23088j) / 2.0f);
        for (int i6 = 0; i6 < i5; i6++) {
            float f11 = this.f23088j;
            float f12 = (i5 * i6) + (f11 / 2.0f) + this.f23085g + this.f23086h;
            if (f12 > f5) {
                canvas.drawCircle(f12, this.f23084f / 2.0f, f11 / 2.0f, this.f23081c);
            }
        }
    }

    @Override // android.view.View
    protected void onMeasure(int i5, int i6) {
        super.onMeasure(i5, i6);
        this.f23083e = getMeasuredWidth();
        this.f23084f = getMeasuredHeight();
    }

    public void setEyeColor(int i5) {
        this.f23082d.setColor(i5);
        postInvalidate();
    }

    public void setViewColor(int i5) {
        this.f23081c.setColor(i5);
        postInvalidate();
    }
}
