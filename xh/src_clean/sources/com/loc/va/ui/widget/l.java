package com.loc.va.ui.widget;

import android.animation.ValueAnimator;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.drawable.Animatable;
import android.graphics.drawable.Drawable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public abstract class l extends Drawable implements Animatable {

    /* renamed from: g, reason: collision with root package name */
    private static final Rect f23338g = new Rect();

    /* renamed from: c, reason: collision with root package name */
    private ArrayList<ValueAnimator> f23341c;

    /* renamed from: e, reason: collision with root package name */
    private boolean f23343e;

    /* renamed from: f, reason: collision with root package name */
    private Paint f23344f;

    /* renamed from: a, reason: collision with root package name */
    protected Rect f23339a = f23338g;

    /* renamed from: b, reason: collision with root package name */
    private HashMap<ValueAnimator, ValueAnimator.AnimatorUpdateListener> f23340b = new HashMap<>();

    /* renamed from: d, reason: collision with root package name */
    private int f23342d = 255;

    public l() {
        Paint paint = new Paint();
        this.f23344f = paint;
        paint.setColor(-1);
        this.f23344f.setStyle(Paint.Style.FILL);
        this.f23344f.setAntiAlias(true);
    }

    private void h() {
        if (this.f23343e) {
            return;
        }
        this.f23341c = p();
        this.f23343e = true;
    }

    private boolean o() {
        Iterator<ValueAnimator> iterator2 = this.f23341c.iterator2();
        if (iterator2.hasNext()) {
            return iterator2.next().isStarted();
        }
        return false;
    }

    private void u() {
        for (int i5 = 0; i5 < this.f23341c.size(); i5++) {
            ValueAnimator valueAnimator = this.f23341c.get(i5);
            ValueAnimator.AnimatorUpdateListener animatorUpdateListener = this.f23340b.get(valueAnimator);
            if (animatorUpdateListener != null) {
                valueAnimator.addUpdateListener(animatorUpdateListener);
            }
            valueAnimator.start();
        }
    }

    private void v() {
        ArrayList<ValueAnimator> arrayList = this.f23341c;
        if (arrayList != null) {
            Iterator<ValueAnimator> iterator2 = arrayList.iterator2();
            while (iterator2.hasNext()) {
                ValueAnimator next = iterator2.next();
                if (next != null && next.isStarted()) {
                    next.removeAllUpdateListeners();
                    next.end();
                }
            }
        }
    }

    public void a(ValueAnimator valueAnimator, ValueAnimator.AnimatorUpdateListener animatorUpdateListener) {
        this.f23340b.put(valueAnimator, animatorUpdateListener);
    }

    @Override // android.graphics.drawable.Drawable
    public void draw(Canvas canvas) {
        g(canvas, this.f23344f);
    }

    public int e() {
        return this.f23339a.centerX();
    }

    public int f() {
        return this.f23339a.centerY();
    }

    public abstract void g(Canvas canvas, Paint paint);

    @Override // android.graphics.drawable.Drawable
    public int getAlpha() {
        return this.f23342d;
    }

    @Override // android.graphics.drawable.Drawable
    public int getOpacity() {
        return -1;
    }

    public float i() {
        return this.f23339a.exactCenterX();
    }

    @Override // android.graphics.drawable.Animatable
    public boolean isRunning() {
        Iterator<ValueAnimator> iterator2 = this.f23341c.iterator2();
        if (iterator2.hasNext()) {
            return iterator2.next().isRunning();
        }
        return false;
    }

    public float j() {
        return this.f23339a.exactCenterY();
    }

    public int k() {
        return this.f23344f.getColor();
    }

    public Rect l() {
        return this.f23339a;
    }

    public int m() {
        return this.f23339a.height();
    }

    public int n() {
        return this.f23339a.width();
    }

    @Override // android.graphics.drawable.Drawable
    protected void onBoundsChange(Rect rect) {
        super.onBoundsChange(rect);
        t(rect);
    }

    public abstract ArrayList<ValueAnimator> p();

    public void q() {
        invalidateSelf();
    }

    public void r(int i5) {
        this.f23344f.setColor(i5);
    }

    public void s(int i5, int i6, int i7, int i8) {
        this.f23339a = new Rect(i5, i6, i7, i8);
    }

    @Override // android.graphics.drawable.Drawable
    public void setAlpha(int i5) {
        this.f23342d = i5;
    }

    @Override // android.graphics.drawable.Drawable
    public void setColorFilter(ColorFilter colorFilter) {
    }

    @Override // android.graphics.drawable.Animatable
    public void start() {
        h();
        if (this.f23341c == null || o()) {
            return;
        }
        u();
        invalidateSelf();
    }

    @Override // android.graphics.drawable.Animatable
    public void stop() {
        v();
    }

    public void t(Rect rect) {
        s(rect.left, rect.top, rect.right, rect.bottom);
    }
}
