package com.loc.va.ui.widget;

import android.R;
import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.util.Log;
import android.view.View;
import android.view.animation.DecelerateInterpolator;
import com.loc.va.c;
import com.loc.va.ui.widget.s;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class LauncherIconView extends androidx.appcompat.widget.n implements r {

    /* renamed from: v, reason: collision with root package name */
    private static final int f23106v = 5;

    /* renamed from: c, reason: collision with root package name */
    private s f23108c;

    /* renamed from: d, reason: collision with root package name */
    private q f23109d;

    /* renamed from: e, reason: collision with root package name */
    private float f23110e;

    /* renamed from: f, reason: collision with root package name */
    private int f23111f;

    /* renamed from: g, reason: collision with root package name */
    private int f23112g;

    /* renamed from: h, reason: collision with root package name */
    private int f23113h;

    /* renamed from: i, reason: collision with root package name */
    private float f23114i;

    /* renamed from: j, reason: collision with root package name */
    private float f23115j;

    /* renamed from: k, reason: collision with root package name */
    private int f23116k;

    /* renamed from: l, reason: collision with root package name */
    private float f23117l;

    /* renamed from: m, reason: collision with root package name */
    private float f23118m;

    /* renamed from: n, reason: collision with root package name */
    private boolean f23119n;

    /* renamed from: o, reason: collision with root package name */
    private boolean f23120o;

    /* renamed from: p, reason: collision with root package name */
    private long f23121p;

    /* renamed from: q, reason: collision with root package name */
    private Paint f23122q;

    /* renamed from: r, reason: collision with root package name */
    private Paint f23123r;

    /* renamed from: s, reason: collision with root package name */
    private RectF f23124s;

    /* renamed from: t, reason: collision with root package name */
    private ValueAnimator f23125t;

    /* renamed from: u, reason: collision with root package name */
    private ValueAnimator f23126u;
    

    /* renamed from: w, reason: collision with root package name */
    private static String f23107w = "LauncherIconView";

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class a implements ValueAnimator.AnimatorUpdateListener {
        a() {
        }

        @Override // android.animation.ValueAnimator.AnimatorUpdateListener
        public void onAnimationUpdate(ValueAnimator valueAnimator) {
            LauncherIconView.this.f23115j = ((Float) valueAnimator.getAnimatedValue()).floatValue();
            LauncherIconView.this.invalidate();
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class b extends AnimatorListenerAdapter {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ int f23128a;

        b(int i5) {
            this.f23128a = i5;
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationCancel(Animator animator) {
            super.onAnimationCancel(animator);
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            super.onAnimationEnd(animator);
            int i5 = this.f23128a;
            if (i5 > 0) {
                LauncherIconView.this.s(0.0f, i5);
            }
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationStart(Animator animator) {
            super.onAnimationStart(animator);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class c implements ValueAnimator.AnimatorUpdateListener {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ boolean f23130a;

        c(boolean z5) {
            this.f23130a = z5;
        }

        @Override // android.animation.ValueAnimator.AnimatorUpdateListener
        public void onAnimationUpdate(ValueAnimator valueAnimator) {
            LauncherIconView.this.f23110e = ((Float) valueAnimator.getAnimatedValue()).floatValue();
            if (0.0f < LauncherIconView.this.f23110e && LauncherIconView.this.f23110e < 100.0f) {
                LauncherIconView.this.invalidate();
            } else {
                if (LauncherIconView.this.f23110e != 100.0f || this.f23130a) {
                    return;
                }
                LauncherIconView.this.r();
            }
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class d implements ValueAnimator.AnimatorUpdateListener {
        d() {
        }

        @Override // android.animation.ValueAnimator.AnimatorUpdateListener
        public void onAnimationUpdate(ValueAnimator valueAnimator) {
            LauncherIconView.this.f23120o = true;
            LauncherIconView.this.f23118m = ((Float) valueAnimator.getAnimatedValue()).floatValue();
            LauncherIconView.this.invalidate();
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class e extends AnimatorListenerAdapter {
        e() {
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationCancel(Animator animator) {
            super.onAnimationCancel(animator);
            LauncherIconView.this.f23120o = false;
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            super.onAnimationEnd(animator);
            LauncherIconView.this.f23120o = false;
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationStart(Animator animator) {
            super.onAnimationStart(animator);
            LauncherIconView.this.f23120o = true;
        }
    }

    

    public LauncherIconView(Context context) {
        super(context);
        n(context, null);
    }

    public LauncherIconView(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        n(context, attributeSet);
    }

    public LauncherIconView(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        n(context, attributeSet);
    }

    private void l(Canvas canvas) {
        canvas.drawRect(0.0f, 0.0f, this.f23112g, this.f23111f, this.f23123r);
    }

    private void m(Canvas canvas) {
        this.f23123r.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.DST_OUT));
        canvas.drawCircle(this.f23112g / 2.0f, this.f23111f / 2.0f, this.f23114i, this.f23123r);
        this.f23123r.setXfermode(null);
        RectF rectF = this.f23124s;
        float f5 = this.f23110e;
        canvas.drawArc(rectF, (-90.0f) + (f5 * 3.6f), 360.0f - (f5 * 3.6f), true, this.f23123r);
    }

    private void n(Context context, AttributeSet attributeSet) {
        this.f23121p = getContext().getResources().getInteger(R.integer.config_mediumAnimTime);
        TypedArray obtainStyledAttributes = context.obtainStyledAttributes(attributeSet, c.r.Lp);
        try {
            this.f23110e = obtainStyledAttributes.getInteger(2, 0);
            this.f23113h = obtainStyledAttributes.getDimensionPixelOffset(4, 8);
            this.f23114i = obtainStyledAttributes.getDimensionPixelOffset(3, 0);
            this.f23119n = obtainStyledAttributes.getBoolean(0, false);
            this.f23116k = obtainStyledAttributes.getColor(1, Color.argb(180, 0, 0, 0));
            Paint paint = new Paint();
            this.f23123r = paint;
            paint.setColor(this.f23116k);
            this.f23123r.setAntiAlias(true);
            Paint paint2 = new Paint();
            this.f23122q = paint2;
            paint2.setColor(-1);
            obtainStyledAttributes.recycle();
            this.f23108c = new s(this, this.f23122q, attributeSet);
        } catch (Throwable th) {
            obtainStyledAttributes.recycle();
            throw th;
        }
    }

    private void o() {
        int i5;
        if (this.f23112g == 0) {
            this.f23112g = getWidth();
        }
        if (this.f23111f == 0) {
            this.f23111f = getHeight();
        }
        if (this.f23112g == 0 || (i5 = this.f23111f) == 0) {
            return;
        }
        if (this.f23114i == 0.0f) {
            this.f23114i = Math.min(r0, i5) / 4.0f;
        }
        if (this.f23117l == 0.0f) {
            int i6 = this.f23112g;
            int i7 = this.f23111f;
            this.f23117l = (float) (Math.sqrt((i6 * i6) + (i7 * i7)) * 0.5d);
        }
        if (this.f23124s == null) {
            int i8 = this.f23112g;
            float f5 = this.f23114i;
            int i9 = this.f23113h;
            int i10 = this.f23111f;
            this.f23124s = new RectF(((i8 / 2.0f) - f5) + i9, ((i10 / 2.0f) - f5) + i9, ((i8 / 2.0f) + f5) - i9, ((i10 / 2.0f) + f5) - i9);
        }
    }

    private void q(int i5) {
        ValueAnimator valueAnimator = this.f23125t;
        if (valueAnimator != null) {
            valueAnimator.cancel();
        }
        ValueAnimator ofFloat = ValueAnimator.ofFloat(0.0f, this.f23113h);
        this.f23125t = ofFloat;
        ofFloat.setInterpolator(new DecelerateInterpolator());
        this.f23125t.setDuration(getContext().getResources().getInteger(R.integer.config_shortAnimTime));
        this.f23125t.addUpdateListener(new a());
        this.f23125t.addListener(new b(i5));
        this.f23125t.start();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void r() {
        ValueAnimator valueAnimator = this.f23126u;
        if (valueAnimator != null) {
            valueAnimator.cancel();
        }
        ValueAnimator ofFloat = ValueAnimator.ofFloat(0.0f, this.f23117l);
        ofFloat.setInterpolator(new DecelerateInterpolator());
        ofFloat.setDuration(this.f23121p);
        ofFloat.addUpdateListener(new d());
        ofFloat.addListener(new e());
        ofFloat.start();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void s(float f5, float f6) {
        ValueAnimator valueAnimator = this.f23126u;
        if (valueAnimator != null) {
            valueAnimator.cancel();
        }
        boolean z5 = f5 > f6;
        ValueAnimator ofFloat = ValueAnimator.ofFloat(f5, f6);
        this.f23126u = ofFloat;
        ofFloat.setInterpolator(new DecelerateInterpolator());
        this.f23126u.setDuration(this.f23121p);
        this.f23126u.addUpdateListener(new c(z5));
        this.f23126u.start();
    }

    private void v(Canvas canvas) {
        this.f23123r.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.DST_OUT));
        canvas.drawCircle(this.f23112g / 2.0f, this.f23111f / 2.0f, this.f23114i, this.f23123r);
        this.f23123r.setXfermode(null);
        canvas.drawCircle(this.f23112g / 2.0f, this.f23111f / 2.0f, this.f23114i - this.f23115j, this.f23123r);
    }

    private void w(Canvas canvas) {
        canvas.drawRect(0.0f, 0.0f, this.f23112g, this.f23111f, this.f23123r);
        this.f23123r.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.DST_OUT));
        canvas.drawCircle(this.f23112g / 2.0f, this.f23111f / 2.0f, this.f23114i + this.f23118m, this.f23123r);
        this.f23123r.setXfermode(null);
    }

    @Override // com.loc.va.ui.widget.r
    public boolean a() {
        return this.f23108c.f();
    }

    @Override // com.loc.va.ui.widget.r
    public boolean c() {
        return this.f23108c.e();
    }

    @Override // com.loc.va.ui.widget.r
    public float getGradientX() {
        return this.f23108c.a();
    }

    public int getMaskColor() {
        return this.f23116k;
    }

    @Override // com.loc.va.ui.widget.r
    public int getPrimaryColor() {
        return this.f23108c.b();
    }

    public int getProgress() {
        return (int) this.f23110e;
    }

    public float getRadius() {
        return this.f23114i;
    }

    @Override // com.loc.va.ui.widget.r
    public int getReflectionColor() {
        return this.f23108c.c();
    }

    public int getStrokeWidth() {
        return this.f23113h;
    }

    @Override // android.widget.ImageView, android.view.View
    protected void onDraw(Canvas canvas) {
        s sVar = this.f23108c;
        if (sVar != null) {
            sVar.g();
        }
        super.onDraw(canvas);
        int saveLayer = canvas.saveLayer(0.0f, 0.0f, getWidth(), getHeight(), null, 31);
        o();
        if (this.f23110e < 100.0f) {
            l(canvas);
            if (this.f23110e == 0.0f) {
                v(canvas);
            } else {
                m(canvas);
            }
        }
        if (this.f23120o) {
            w(canvas);
        }
        canvas.restoreToCount(saveLayer);
    }

    @Override // android.widget.ImageView, android.view.View
    protected void onMeasure(int i5, int i6) {
        super.onMeasure(i5, i6);
        if (this.f23119n) {
            int size = View.MeasureSpec.getSize(i5);
            if (size == 0) {
                size = View.MeasureSpec.getSize(i6);
            }
            setMeasuredDimension(size, size);
        }
    }

    @Override // android.view.View
    protected void onSizeChanged(int i5, int i6, int i7, int i8) {
        super.onSizeChanged(i5, i6, i7, i8);
        s sVar = this.f23108c;
        if (sVar != null) {
            sVar.h();
        }
    }

    public void p(int i5, boolean z5) {
        int min = Math.min(Math.max(i5, 0), 100);
        Log.d("LauncherIconView", "setProgress: p:" + min + ",mp:" + this.f23110e);
        float f5 = (float) min;
        if (Math.abs(f5 - this.f23110e) > 5.0f && z5) {
            float f6 = this.f23110e;
            if (f6 == 0.0f) {
                q(min);
                return;
            } else {
                s(f6, f5);
                return;
            }
        }
        if (min == 100 && z5) {
            this.f23110e = 100.0f;
            r();
        } else {
            this.f23110e = f5;
            if (f5 == 0.0f) {
                this.f23115j = 0.0f;
            }
            invalidate();
        }
    }

    @Override // com.loc.va.ui.widget.r
    public void setAnimationSetupCallback(s.a aVar) {
        this.f23108c.j(aVar);
    }

    @Override // com.loc.va.ui.widget.r
    public void setGradientX(float f5) {
        this.f23108c.k(f5);
    }

    public void setMaskColor(int i5) {
        this.f23116k = i5;
        this.f23123r.setColor(i5);
        invalidate();
    }

    @Override // com.loc.va.ui.widget.r
    public void setPrimaryColor(int i5) {
        this.f23108c.l(i5);
    }

    public void setProgress(int i5) {
        p(i5, true);
    }

    public void setRadius(float f5) {
        this.f23114i = f5;
        this.f23124s = null;
        invalidate();
    }

    @Override // com.loc.va.ui.widget.r
    public void setReflectionColor(int i5) {
        this.f23108c.m(i5);
    }

    @Override // com.loc.va.ui.widget.r
    public void setShimmering(boolean z5) {
        this.f23108c.n(z5);
    }

    public void setStrokeWidth(int i5) {
        this.f23113h = i5;
        this.f23124s = null;
        invalidate();
    }

    public void t() {
        u();
        q qVar = new q();
        this.f23109d = qVar;
        qVar.r(1).s(800L).p(0).t(this);
    }

    public void u() {
        q qVar = this.f23109d;
        if (qVar == null || !qVar.n()) {
            return;
        }
        this.f23109d.h();
        this.f23109d = null;
    }
}
