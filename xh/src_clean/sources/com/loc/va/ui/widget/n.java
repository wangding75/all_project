package com.loc.va.ui.widget;

import android.animation.Animator;
import android.animation.ObjectAnimator;
import android.annotation.SuppressLint;
import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RadialGradient;
import android.graphics.Rect;
import android.graphics.Shader;
import android.util.AttributeSet;
import android.util.Log;
import android.view.MotionEvent;
import android.view.animation.AccelerateDecelerateInterpolator;
import androidx.core.view.f2;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
@SuppressLint({"ClickableViewAccessibility"})
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class n extends androidx.appcompat.widget.f {
    

    /* renamed from: c, reason: collision with root package name */
    private float f23364c;

    /* renamed from: d, reason: collision with root package name */
    private float f23365d;

    /* renamed from: e, reason: collision with root package name */
    private float f23366e;

    /* renamed from: f, reason: collision with root package name */
    private float f23367f;

    /* renamed from: g, reason: collision with root package name */
    private float f23368g;

    /* renamed from: h, reason: collision with root package name */
    private float f23369h;

    /* renamed from: i, reason: collision with root package name */
    private int f23370i;

    /* renamed from: j, reason: collision with root package name */
    private boolean f23371j;

    /* renamed from: k, reason: collision with root package name */
    private boolean f23372k;

    /* renamed from: l, reason: collision with root package name */
    private RadialGradient f23373l;

    /* renamed from: m, reason: collision with root package name */
    private Paint f23374m;

    /* renamed from: n, reason: collision with root package name */
    private ObjectAnimator f23375n;

    /* renamed from: o, reason: collision with root package name */
    private boolean f23376o;

    /* renamed from: p, reason: collision with root package name */
    private Rect f23377p;

    /* renamed from: q, reason: collision with root package name */
    private Path f23378q;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a implements Animator.AnimatorListener {
        a() {
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationCancel(Animator animator) {
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            n.this.setRadius(0.0f);
            n.this.setAlpha(1.0f);
            n.this.f23371j = false;
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationRepeat(Animator animator) {
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationStart(Animator animator) {
            n.this.f23371j = true;
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class b implements Animator.AnimatorListener {
        b() {
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationCancel(Animator animator) {
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            n.this.setRadius(0.0f);
            n.this.setAlpha(1.0f);
            n.this.f23371j = false;
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationRepeat(Animator animator) {
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationStart(Animator animator) {
            n.this.f23371j = true;
        }
    }

    

    public n(Context context) {
        this(context, null);
    }

    public n(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public n(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23371j = false;
        this.f23372k = true;
        this.f23378q = new Path();
        d();
        TypedArray obtainStyledAttributes = context.obtainStyledAttributes(attributeSet, c.r.zq);
        this.f23370i = obtainStyledAttributes.getColor(2, this.f23370i);
        this.f23366e = obtainStyledAttributes.getFloat(0, this.f23366e);
        this.f23372k = obtainStyledAttributes.getBoolean(1, this.f23372k);
        obtainStyledAttributes.recycle();
    }

    private int c(int i5) {
        return (int) ((i5 * this.f23367f) + 0.5f);
    }

    public int b(int i5, float f5) {
        return Color.argb(Math.round(Color.alpha(i5) * f5), Color.red(i5), Color.green(i5), Color.blue(i5));
    }

    public void d() {
        this.f23367f = getContext().getResources().getDisplayMetrics().density;
        Paint paint = new Paint(1);
        this.f23374m = paint;
        paint.setAlpha(100);
        e(f2.f6745t, 0.2f);
    }

    public void e(int i5, float f5) {
        this.f23370i = i5;
        this.f23366e = f5;
    }

    @Override // android.widget.TextView, android.view.View
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (isInEditMode()) {
            return;
        }
        canvas.save();
        this.f23378q.reset();
        this.f23378q.addCircle(this.f23364c, this.f23365d, this.f23368g, Path.Direction.CW);
        canvas.clipPath(this.f23378q);
        canvas.drawCircle(this.f23364c, this.f23365d, this.f23368g, this.f23374m);
    }

    @Override // android.view.View
    protected void onSizeChanged(int i5, int i6, int i7, int i8) {
        super.onSizeChanged(i5, i6, i7, i8);
        this.f23369h = (float) Math.sqrt((i5 * i5) + (i6 * i6));
    }

    @Override // android.widget.TextView, android.view.View
    public boolean onTouchEvent(MotionEvent motionEvent) {
        Log.d("TouchEvent", String.valueOf(motionEvent.getActionMasked()));
        Log.d("mIsAnimating", String.valueOf(this.f23371j));
        Log.d("mAnimationIsCancel", String.valueOf(this.f23376o));
        boolean onTouchEvent = super.onTouchEvent(motionEvent);
        int actionMasked = motionEvent.getActionMasked();
        String $2 = "radius";
        if (actionMasked == 0 && isEnabled() && this.f23372k) {
            this.f23377p = new Rect(getLeft(), getTop(), getRight(), getBottom());
            this.f23376o = false;
            this.f23364c = motionEvent.getX();
            this.f23365d = motionEvent.getY();
            ObjectAnimator duration = ObjectAnimator.ofFloat(this, $2, 0.0f, c(50)).setDuration(400L);
            this.f23375n = duration;
            duration.setInterpolator(new AccelerateDecelerateInterpolator());
            this.f23375n.addListener(new a());
            this.f23375n.start();
            if (!onTouchEvent) {
                return true;
            }
        } else if (motionEvent.getActionMasked() == 2 && isEnabled() && this.f23372k) {
            this.f23364c = motionEvent.getX();
            this.f23365d = motionEvent.getY();
            boolean z5 = !this.f23377p.contains(getLeft() + ((int) motionEvent.getX()), getTop() + ((int) motionEvent.getY()));
            this.f23376o = z5;
            if (z5) {
                setRadius(0.0f);
            } else {
                setRadius(c(50));
            }
            if (!onTouchEvent) {
                return true;
            }
        } else if (motionEvent.getActionMasked() == 1 && !this.f23376o && isEnabled()) {
            this.f23364c = motionEvent.getX();
            this.f23365d = motionEvent.getY();
            float f5 = this.f23364c;
            float max = Math.max((float) Math.sqrt((f5 * f5) + (r13 * r13)), this.f23369h);
            if (this.f23371j) {
                this.f23375n.cancel();
            }
            ObjectAnimator ofFloat = ObjectAnimator.ofFloat(this, $2, c(50), max);
            this.f23375n = ofFloat;
            ofFloat.setDuration(500L);
            this.f23375n.setInterpolator(new AccelerateDecelerateInterpolator());
            this.f23375n.addListener(new b());
            this.f23375n.start();
            if (!onTouchEvent) {
                return true;
            }
        }
        return onTouchEvent;
    }

    public void setHover(boolean z5) {
        this.f23372k = z5;
    }

    public void setRadius(float f5) {
        this.f23368g = f5;
        if (f5 > 0.0f) {
            RadialGradient radialGradient = new RadialGradient(this.f23364c, this.f23365d, this.f23368g, b(this.f23370i, this.f23366e), this.f23370i, Shader.TileMode.MIRROR);
            this.f23373l = radialGradient;
            this.f23374m.setShader(radialGradient);
        }
        invalidate();
    }
}
