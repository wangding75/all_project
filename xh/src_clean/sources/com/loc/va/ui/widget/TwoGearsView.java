package com.loc.va.ui.widget;

import android.animation.Animator;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.util.AttributeSet;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class TwoGearsView extends e {

    /* renamed from: b, reason: collision with root package name */
    ValueAnimator f23185b;

    /* renamed from: c, reason: collision with root package name */
    float f23186c;

    /* renamed from: d, reason: collision with root package name */
    float f23187d;

    /* renamed from: e, reason: collision with root package name */
    float f23188e;

    /* renamed from: f, reason: collision with root package name */
    float f23189f;

    /* renamed from: g, reason: collision with root package name */
    float f23190g;

    /* renamed from: h, reason: collision with root package name */
    float f23191h;

    /* renamed from: i, reason: collision with root package name */
    private float f23192i;

    /* renamed from: j, reason: collision with root package name */
    private Paint f23193j;

    /* renamed from: k, reason: collision with root package name */
    private Paint f23194k;

    /* renamed from: l, reason: collision with root package name */
    private Paint f23195l;

    /* renamed from: m, reason: collision with root package name */
    private float f23196m;

    /* renamed from: n, reason: collision with root package name */
    private float f23197n;

    /* renamed from: o, reason: collision with root package name */
    private int f23198o;

    /* renamed from: p, reason: collision with root package name */
    private int f23199p;

    public TwoGearsView(Context context) {
        super(context);
        this.f23185b = null;
        this.f23186c = 0.0f;
        this.f23187d = 0.0f;
        this.f23188e = 0.0f;
        this.f23189f = 0.0f;
        this.f23190g = 0.0f;
        this.f23191h = 0.0f;
        this.f23192i = 0.0f;
        this.f23196m = 0.0f;
        this.f23198o = 10;
        this.f23199p = 8;
    }

    public TwoGearsView(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        this.f23185b = null;
        this.f23186c = 0.0f;
        this.f23187d = 0.0f;
        this.f23188e = 0.0f;
        this.f23189f = 0.0f;
        this.f23190g = 0.0f;
        this.f23191h = 0.0f;
        this.f23192i = 0.0f;
        this.f23196m = 0.0f;
        this.f23198o = 10;
        this.f23199p = 8;
    }

    public TwoGearsView(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23185b = null;
        this.f23186c = 0.0f;
        this.f23187d = 0.0f;
        this.f23188e = 0.0f;
        this.f23189f = 0.0f;
        this.f23190g = 0.0f;
        this.f23191h = 0.0f;
        this.f23192i = 0.0f;
        this.f23196m = 0.0f;
        this.f23198o = 10;
        this.f23199p = 8;
    }

    private int o(float f5) {
        return (int) ((f5 * getContext().getResources().getDisplayMetrics().density) + 0.5f);
    }

    private void p(Canvas canvas) {
        for (int i5 = 0; i5 < 3; i5++) {
            double d6 = ((i5 * 120) * 3.141592653589793d) / 180.0d;
            float cos = (float) (this.f23188e * Math.cos(d6));
            float sin = (float) (this.f23189f * Math.sin(d6));
            float f5 = this.f23196m;
            float f6 = this.f23188e;
            float f7 = this.f23189f;
            canvas.drawLine(f5 + f6, f5 + f7, (f6 + f5) - cos, (f5 + f7) - sin, this.f23194k);
        }
        for (int i6 = 0; i6 < 3; i6++) {
            double d7 = ((i6 * 120) * 3.141592653589793d) / 180.0d;
            float cos2 = (float) ((this.f23190g - this.f23188e) * Math.cos(d7));
            float sin2 = (float) ((this.f23191h - this.f23189f) * Math.sin(d7));
            float f8 = this.f23190g;
            float f9 = this.f23196m;
            float f10 = this.f23197n;
            float f11 = this.f23191h;
            canvas.drawLine(f8 + f9 + (f10 * 2.0f), f11 + f9 + (f10 * 2.0f), ((f8 + f9) + (f10 * 2.0f)) - cos2, ((f11 + f9) + (f10 * 2.0f)) - sin2, this.f23194k);
        }
    }

    private void q(Canvas canvas) {
        this.f23190g = (float) ((this.f23187d / 2.0f) * Math.cos(0.7853981633974483d));
        this.f23191h = (float) ((this.f23187d / 2.0f) * Math.sin(0.7853981633974483d));
        float o5 = o(1.5f) / 4;
        this.f23193j.setStrokeWidth(o(1.5f));
        int i5 = 0;
        while (i5 < 360) {
            double d6 = (((int) (360.0f - ((this.f23186c * this.f23199p) + i5))) * 3.141592653589793d) / 180.0d;
            float cos = (float) ((this.f23190g - this.f23188e) * Math.cos(d6));
            float sin = (float) ((this.f23191h - this.f23189f) * Math.sin(d6));
            float cos2 = (float) (((this.f23190g - this.f23188e) + this.f23197n) * Math.cos(d6));
            float sin2 = (float) (((this.f23191h - this.f23189f) + this.f23197n) * Math.sin(d6));
            float f5 = this.f23190g;
            float f6 = this.f23196m;
            float f7 = (f5 + f6) - cos2;
            float f8 = this.f23197n;
            float f9 = f7 + (f8 * 2.0f) + o5;
            float f10 = this.f23191h;
            canvas.drawLine(f9, ((f10 + f6) - sin2) + (f8 * 2.0f) + o5, ((f5 + f6) - cos) + (f8 * 2.0f) + o5, ((f10 + f6) - sin) + (f8 * 2.0f) + o5, this.f23193j);
            i5 += this.f23199p;
        }
    }

    private void r(Canvas canvas) {
        float o5 = o(1.5f) / 4;
        this.f23195l.setStrokeWidth(o(1.5f));
        float f5 = this.f23190g;
        float f6 = this.f23196m;
        float f7 = this.f23197n;
        canvas.drawCircle(f5 + f6 + (f7 * 2.0f) + o5, this.f23191h + f6 + (f7 * 2.0f) + o5, (f5 - this.f23188e) - o5, this.f23195l);
        this.f23195l.setStrokeWidth(o(1.5f));
        float f8 = this.f23190g;
        float f9 = this.f23196m;
        float f10 = this.f23197n;
        canvas.drawCircle(f8 + f9 + (f10 * 2.0f) + o5, this.f23191h + f9 + (f10 * 2.0f) + o5, ((f8 - this.f23188e) / 2.0f) - o5, this.f23195l);
    }

    private void s(Canvas canvas) {
        this.f23193j.setStrokeWidth(o(1.0f));
        int i5 = 0;
        while (i5 < 360) {
            double d6 = (((int) ((this.f23186c * this.f23198o) + i5)) * 3.141592653589793d) / 180.0d;
            float cos = (float) (this.f23188e * Math.cos(d6));
            float sin = (float) (this.f23189f * Math.sin(d6));
            float cos2 = (float) ((this.f23188e + this.f23197n) * Math.cos(d6));
            float sin2 = (float) ((this.f23189f + this.f23197n) * Math.sin(d6));
            float f5 = this.f23196m;
            float f6 = this.f23188e;
            float f7 = (f5 + f6) - cos2;
            float f8 = this.f23189f;
            canvas.drawLine(f7, (f8 + f5) - sin2, (f6 + f5) - cos, (f8 + f5) - sin, this.f23193j);
            i5 += this.f23198o;
        }
    }

    private void t(Canvas canvas) {
        this.f23187d = (float) (this.f23192i * Math.sqrt(2.0d));
        this.f23188e = (float) ((r0 / 6.0f) * Math.cos(0.7853981633974483d));
        this.f23189f = (float) ((this.f23187d / 6.0f) * Math.sin(0.7853981633974483d));
        this.f23195l.setStrokeWidth(o(1.0f));
        float f5 = this.f23196m;
        float f6 = this.f23188e;
        canvas.drawCircle(f5 + f6, this.f23189f + f5, f6, this.f23195l);
        this.f23195l.setStrokeWidth(o(1.5f));
        float f7 = this.f23196m;
        float f8 = this.f23188e;
        canvas.drawCircle(f7 + f8, this.f23189f + f7, f8 / 2.0f, this.f23195l);
    }

    private void u() {
        Paint paint = new Paint();
        this.f23195l = paint;
        paint.setAntiAlias(true);
        this.f23195l.setStyle(Paint.Style.STROKE);
        this.f23195l.setColor(-1);
        this.f23195l.setStrokeWidth(o(1.5f));
        Paint paint2 = new Paint();
        this.f23193j = paint2;
        paint2.setAntiAlias(true);
        this.f23193j.setStyle(Paint.Style.STROKE);
        this.f23193j.setColor(-1);
        this.f23193j.setStrokeWidth(o(1.0f));
        Paint paint3 = new Paint();
        this.f23194k = paint3;
        paint3.setAntiAlias(true);
        this.f23194k.setStyle(Paint.Style.FILL);
        this.f23194k.setColor(-1);
        this.f23194k.setStrokeWidth(o(1.5f));
        this.f23197n = o(2.0f);
    }

    @Override // com.loc.va.ui.widget.e
    protected void a() {
    }

    @Override // com.loc.va.ui.widget.e
    protected void b() {
        u();
    }

    @Override // com.loc.va.ui.widget.e
    protected void c(Animator animator) {
    }

    @Override // com.loc.va.ui.widget.e
    protected void d(ValueAnimator valueAnimator) {
        this.f23186c = ((Float) valueAnimator.getAnimatedValue()).floatValue();
        postInvalidate();
    }

    @Override // com.loc.va.ui.widget.e
    protected int e() {
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
        this.f23196m = o(5.0f);
        canvas.save();
        float f5 = this.f23192i;
        canvas.rotate(180.0f, f5 / 2.0f, f5 / 2.0f);
        t(canvas);
        s(canvas);
        q(canvas);
        r(canvas);
        p(canvas);
        canvas.restore();
    }

    @Override // android.view.View
    protected void onMeasure(int i5, int i6) {
        super.onMeasure(i5, i6);
        this.f23192i = getMeasuredWidth() > getHeight() ? getMeasuredHeight() : getMeasuredWidth();
    }

    public void setViewColor(int i5) {
        this.f23193j.setColor(i5);
        this.f23194k.setColor(i5);
        this.f23195l.setColor(i5);
        postInvalidate();
    }
}
