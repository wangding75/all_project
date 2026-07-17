package com.loc.va.ui.widget;

import android.R;
import android.annotation.TargetApi;
import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.graphics.drawable.Animatable;
import android.graphics.drawable.Drawable;
import android.text.TextUtils;
import android.util.AttributeSet;
import android.util.Log;
import android.view.View;
import android.view.animation.AnimationUtils;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class m extends View {
    

    /* renamed from: n, reason: collision with root package name */
    private static String f23345n = "LoadingIndicatorView";

    /* renamed from: o, reason: collision with root package name */
    private static final l f23346o = new com.loc.va.ui.widget.b();

    /* renamed from: p, reason: collision with root package name */
    private static final int f23347p = 500;

    /* renamed from: q, reason: collision with root package name */
    private static final int f23348q = 500;

    /* renamed from: a, reason: collision with root package name */
    int f23349a;

    /* renamed from: b, reason: collision with root package name */
    int f23350b;

    /* renamed from: c, reason: collision with root package name */
    int f23351c;

    /* renamed from: d, reason: collision with root package name */
    int f23352d;

    /* renamed from: e, reason: collision with root package name */
    private long f23353e;

    /* renamed from: f, reason: collision with root package name */
    private boolean f23354f;

    /* renamed from: g, reason: collision with root package name */
    private boolean f23355g;

    /* renamed from: h, reason: collision with root package name */
    private boolean f23356h;

    /* renamed from: i, reason: collision with root package name */
    private l f23357i;

    /* renamed from: j, reason: collision with root package name */
    private int f23358j;

    /* renamed from: k, reason: collision with root package name */
    private boolean f23359k;

    /* renamed from: l, reason: collision with root package name */
    private final Runnable f23360l;

    /* renamed from: m, reason: collision with root package name */
    private final Runnable f23361m;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class a implements Runnable {
        a() {
        }

        @Override // java.lang.Runnable
        public void run() {
            m.this.f23354f = false;
            m.this.f23353e = -1L;
            m.this.setVisibility(8);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class b implements Runnable {
        b() {
        }

        @Override // java.lang.Runnable
        public void run() {
            m.this.f23355g = false;
            if (m.this.f23356h) {
                return;
            }
            m.this.f23353e = System.currentTimeMillis();
            m.this.setVisibility(0);
        }
    }

    

    public m(Context context) {
        super(context);
        this.f23353e = -1L;
        this.f23354f = false;
        this.f23355g = false;
        this.f23356h = false;
        this.f23360l = new a();
        this.f23361m = new b();
        g(context, null, 0, 0);
    }

    public m(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        this.f23353e = -1L;
        this.f23354f = false;
        this.f23355g = false;
        this.f23356h = false;
        this.f23360l = new a();
        this.f23361m = new b();
        g(context, attributeSet, 0, c.q.f22155a);
    }

    public m(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23353e = -1L;
        this.f23354f = false;
        this.f23355g = false;
        this.f23356h = false;
        this.f23360l = new a();
        this.f23361m = new b();
        g(context, attributeSet, i5, c.q.f22155a);
    }

    @TargetApi(21)
    public m(Context context, AttributeSet attributeSet, int i5, int i6) {
        super(context, attributeSet, i5, i6);
        this.f23353e = -1L;
        this.f23354f = false;
        this.f23355g = false;
        this.f23356h = false;
        this.f23360l = new a();
        this.f23361m = new b();
        g(context, attributeSet, i5, c.q.f22155a);
    }

    private void g(Context context, AttributeSet attributeSet, int i5, int i6) {
        this.f23349a = 24;
        this.f23350b = 48;
        this.f23351c = 24;
        this.f23352d = 48;
        TypedArray obtainStyledAttributes = context.obtainStyledAttributes(attributeSet, c.r.ek, i5, i6);
        this.f23349a = obtainStyledAttributes.getDimensionPixelSize(5, this.f23349a);
        this.f23350b = obtainStyledAttributes.getDimensionPixelSize(3, this.f23350b);
        this.f23351c = obtainStyledAttributes.getDimensionPixelSize(4, this.f23351c);
        this.f23352d = obtainStyledAttributes.getDimensionPixelSize(2, this.f23352d);
        String string = obtainStyledAttributes.getString(1);
        this.f23358j = obtainStyledAttributes.getColor(0, -1);
        setIndicator(string);
        if (this.f23357i == null) {
            setIndicator(f23346o);
        }
        obtainStyledAttributes.recycle();
    }

    private void h() {
        removeCallbacks(this.f23360l);
        removeCallbacks(this.f23361m);
    }

    private void n(int i5, int i6) {
        int i7;
        int paddingRight = i5 - (getPaddingRight() + getPaddingLeft());
        int paddingTop = i6 - (getPaddingTop() + getPaddingBottom());
        if (this.f23357i != null) {
            float intrinsicWidth = r0.getIntrinsicWidth() / this.f23357i.getIntrinsicHeight();
            float f5 = paddingRight;
            float f6 = paddingTop;
            float f7 = f5 / f6;
            int i8 = 0;
            if (intrinsicWidth == f7) {
                i7 = 0;
            } else if (f7 > intrinsicWidth) {
                int i9 = (int) (f6 * intrinsicWidth);
                int i10 = (paddingRight - i9) / 2;
                i8 = i10;
                paddingRight = i9 + i10;
                i7 = 0;
            } else {
                int i11 = (int) (f5 * (1.0f / intrinsicWidth));
                int i12 = (paddingTop - i11) / 2;
                int i13 = i11 + i12;
                i7 = i12;
                paddingTop = i13;
            }
            this.f23357i.setBounds(i8, i7, paddingRight, paddingTop);
        }
    }

    private void o() {
        int[] drawableState = getDrawableState();
        l lVar = this.f23357i;
        if (lVar == null || !lVar.isStateful()) {
            return;
        }
        this.f23357i.setState(drawableState);
    }

    @Override // android.view.View
    @TargetApi(21)
    public void drawableHotspotChanged(float f5, float f6) {
        super.drawableHotspotChanged(f5, f6);
        l lVar = this.f23357i;
        if (lVar != null) {
            lVar.setHotspot(f5, f6);
        }
    }

    @Override // android.view.View
    protected void drawableStateChanged() {
        super.drawableStateChanged();
        o();
    }

    void e(Canvas canvas) {
        l lVar = this.f23357i;
        if (lVar != null) {
            int save = canvas.save();
            canvas.translate(getPaddingLeft(), getPaddingTop());
            lVar.draw(canvas);
            canvas.restoreToCount(save);
            if (this.f23359k) {
                lVar.start();
                this.f23359k = false;
            }
        }
    }

    public void f() {
        this.f23356h = true;
        removeCallbacks(this.f23361m);
        long currentTimeMillis = System.currentTimeMillis();
        long j5 = this.f23353e;
        long j6 = currentTimeMillis - j5;
        if (j6 >= 500 || j5 == -1) {
            setVisibility(8);
        } else {
            if (this.f23354f) {
                return;
            }
            postDelayed(this.f23360l, 500 - j6);
            this.f23354f = true;
        }
    }

    public l getIndicator() {
        return this.f23357i;
    }

    public void i() {
        this.f23353e = -1L;
        this.f23356h = false;
        removeCallbacks(this.f23360l);
        if (this.f23355g) {
            return;
        }
        postDelayed(this.f23361m, 500L);
        this.f23355g = true;
    }

    @Override // android.view.View, android.graphics.drawable.Drawable.Callback
    public void invalidateDrawable(Drawable drawable) {
        if (!verifyDrawable(drawable)) {
            super.invalidateDrawable(drawable);
            return;
        }
        Rect bounds = drawable.getBounds();
        int scrollX = getScrollX() + getPaddingLeft();
        int scrollY = getScrollY() + getPaddingTop();
        invalidate(bounds.left + scrollX, bounds.top + scrollY, bounds.right + scrollX, bounds.bottom + scrollY);
    }

    public void j() {
        startAnimation(AnimationUtils.loadAnimation(getContext(), R.anim.fade_out));
        setVisibility(8);
    }

    public void k() {
        startAnimation(AnimationUtils.loadAnimation(getContext(), R.anim.fade_in));
        setVisibility(0);
    }

    void l() {
        if (getVisibility() != 0) {
            return;
        }
        if (this.f23357i instanceof Animatable) {
            this.f23359k = true;
        }
        postInvalidate();
    }

    void m() {
        l lVar = this.f23357i;
        if (lVar instanceof Animatable) {
            lVar.stop();
            this.f23359k = false;
        }
        postInvalidate();
    }

    @Override // android.view.View
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        l();
        h();
    }

    @Override // android.view.View
    protected void onDetachedFromWindow() {
        m();
        super.onDetachedFromWindow();
        h();
    }

    @Override // android.view.View
    protected synchronized void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        e(canvas);
    }

    @Override // android.view.View
    protected synchronized void onMeasure(int i5, int i6) {
        int i7;
        int i8;
        l lVar = this.f23357i;
        if (lVar != null) {
            i8 = Math.max(this.f23349a, Math.min(this.f23350b, lVar.getIntrinsicWidth()));
            i7 = Math.max(this.f23351c, Math.min(this.f23352d, lVar.getIntrinsicHeight()));
        } else {
            i7 = 0;
            i8 = 0;
        }
        o();
        setMeasuredDimension(View.resolveSizeAndState(i8 + getPaddingLeft() + getPaddingRight(), i5, 0), View.resolveSizeAndState(i7 + getPaddingTop() + getPaddingBottom(), i6, 0));
    }

    @Override // android.view.View
    protected void onSizeChanged(int i5, int i6, int i7, int i8) {
        n(i5, i6);
    }

    @Override // android.view.View
    protected void onVisibilityChanged(View view, int i5) {
        super.onVisibilityChanged(view, i5);
        if (i5 == 8 || i5 == 4) {
            m();
        } else {
            l();
        }
    }

    public void setIndicator(l lVar) {
        l lVar2 = this.f23357i;
        if (lVar2 != lVar) {
            if (lVar2 != null) {
                lVar2.setCallback(null);
                unscheduleDrawable(this.f23357i);
            }
            this.f23357i = lVar;
            setIndicatorColor(this.f23358j);
            if (lVar != null) {
                lVar.setCallback(this);
            }
            postInvalidate();
        }
    }

    public void setIndicator(String str) {
        if (TextUtils.isEmpty(str)) {
            return;
        }
        StringBuilder sb = new StringBuilder();
        String $2 = ".";
        if (!str.contains($2)) {
            sb.append(getClass().getPackage().getName());
            sb.append($2);
        }
        sb.append(str);
        try {
            setIndicator((l) Class.forName(sb.toString()).newInstance());
        } catch (ClassNotFoundException unused) {
            Log.e("LoadingIndicatorView", "Didn't find your class , check the name again !");
        } catch (IllegalAccessException e6) {
            e = e6;
            e.printStackTrace();
        } catch (InstantiationException e7) {
            e = e7;
            e.printStackTrace();
        }
    }

    public void setIndicatorColor(int i5) {
        this.f23358j = i5;
        this.f23357i.r(i5);
    }

    @Override // android.view.View
    public void setVisibility(int i5) {
        if (getVisibility() != i5) {
            super.setVisibility(i5);
            if (i5 == 8 || i5 == 4) {
                m();
            } else {
                l();
            }
        }
    }

    @Override // android.view.View
    protected boolean verifyDrawable(Drawable drawable) {
        return drawable == this.f23357i || super.verifyDrawable(drawable);
    }
}
