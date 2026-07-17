package com.loc.va.ui.widget;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.content.Context;
import android.content.res.Resources;
import android.util.Property;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.animation.DecelerateInterpolator;
import android.widget.FrameLayout;
import com.loc.va.c;
import java.util.ArrayList;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public abstract class g implements View.OnTouchListener, View.OnClickListener {

    /* renamed from: t, reason: collision with root package name */
    public static final int f23269t = 600;

    /* renamed from: u, reason: collision with root package name */
    public static final int f23270u = 2;

    /* renamed from: v, reason: collision with root package name */
    public static final int f23271v = -1;

    /* renamed from: a, reason: collision with root package name */
    private final int f23272a;

    /* renamed from: b, reason: collision with root package name */
    private final int f23273b;

    /* renamed from: c, reason: collision with root package name */
    private float f23274c;

    /* renamed from: d, reason: collision with root package name */
    private float f23275d;

    /* renamed from: e, reason: collision with root package name */
    private int f23276e;

    /* renamed from: f, reason: collision with root package name */
    private boolean f23277f;

    /* renamed from: g, reason: collision with root package name */
    private boolean f23278g;

    /* renamed from: h, reason: collision with root package name */
    private int f23279h;

    /* renamed from: i, reason: collision with root package name */
    private View[] f23280i;

    /* renamed from: j, reason: collision with root package name */
    private float f23281j;

    /* renamed from: k, reason: collision with root package name */
    private i f23282k;

    /* renamed from: q, reason: collision with root package name */
    private float f23288q;

    /* renamed from: l, reason: collision with root package name */
    private boolean f23283l = false;

    /* renamed from: m, reason: collision with root package name */
    private float f23284m = -1.0f;

    /* renamed from: n, reason: collision with root package name */
    private float f23285n = -1.0f;

    /* renamed from: o, reason: collision with root package name */
    private float f23286o = 0.0f;

    /* renamed from: p, reason: collision with root package name */
    private int f23287p = -1;

    /* renamed from: r, reason: collision with root package name */
    private int f23289r = 0;

    /* renamed from: s, reason: collision with root package name */
    private int f23290s = 0;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class a extends AnimatorListenerAdapter {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ Runnable f23291a;

        /* renamed from: b, reason: collision with root package name */
        final /* synthetic */ boolean f23292b;

        a(Runnable runnable, boolean z5) {
            this.f23291a = runnable;
            this.f23292b = z5;
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            Runnable runnable = this.f23291a;
            if (runnable != null) {
                runnable.run();
            }
            g.this.t(true);
            if (this.f23292b) {
                g.this.f23287p = -1;
            }
        }
    }

    public g(Context context) {
        Resources resources = context.getResources();
        this.f23272a = Resources.getSystem().getDisplayMetrics().heightPixels;
        this.f23273b = (int) resources.getDimension(c.g.V1);
        this.f23288q = (int) resources.getDimension(c.g.W1);
        this.f23281j = (int) resources.getDimension(c.g.W1);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void o(View view) {
        t(true);
        if (this.f23282k.getOnCardSelectedListener() != null) {
            this.f23282k.getOnCardSelectedListener().a(view, this.f23287p);
        }
    }

    private void p(int i5, float f5) {
        int k5;
        int i6;
        if (f5 < 0.0f || i5 < 0 || i5 >= k()) {
            return;
        }
        while (i5 < k()) {
            View view = this.f23280i[i5];
            float f6 = f5 / this.f23288q;
            if (this.f23277f) {
                int i7 = this.f23276e;
                if (i7 > 0) {
                    f6 *= i7 / 3;
                    i6 = (k() + 1) - i5;
                    view.setY(i(i5) + (f6 * i6));
                    i5++;
                } else {
                    k5 = ((i7 * (-1)) / 3) * i5;
                }
            } else {
                k5 = k() * 2;
            }
            i6 = k5 + 1;
            view.setY(i(i5) + (f6 * i6));
            i5++;
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void t(boolean z5) {
        this.f23283l = z5;
    }

    private void u(List<Animator> list, Runnable runnable, boolean z5) {
        AnimatorSet animatorSet = new AnimatorSet();
        animatorSet.playTogether(list);
        animatorSet.setDuration(600L);
        animatorSet.setInterpolator(new DecelerateInterpolator(2.0f));
        animatorSet.addListener(new a(runnable, z5));
        animatorSet.start();
    }

    void d(int i5) {
        boolean z5;
        View e6 = e(i5, this.f23282k);
        e6.setOnTouchListener(this);
        e6.setTag(c.i.M2, Integer.valueOf(i5));
        e6.setLayerType(2, null);
        this.f23290s = e6.getPaddingTop();
        e6.setLayoutParams(new FrameLayout.LayoutParams(-1, this.f23279h));
        if (this.f23278g) {
            e6.setY(g(i5));
            z5 = false;
        } else {
            e6.setY(i(i5) - this.f23289r);
            z5 = true;
        }
        t(z5);
        this.f23280i[i5] = e6;
        this.f23282k.addView(e6);
    }

    public abstract View e(int i5, ViewGroup viewGroup);

    protected Animator f(View view, int i5, int i6) {
        return i5 != i6 ? ObjectAnimator.ofFloat(view, (Property<View, Float>) View.Y, (int) view.getY(), g(i5)) : ObjectAnimator.ofFloat(view, (Property<View, Float>) View.Y, (int) view.getY(), i(0) + (i5 * this.f23274c));
    }

    protected float g(int i5) {
        return ((this.f23272a - this.f23273b) - ((k() - i5) * this.f23274c)) - this.f23290s;
    }

    protected float h() {
        return this.f23274c;
    }

    protected float i(int i5) {
        return this.f23289r + (this.f23275d * i5);
    }

    public View j(int i5) {
        View[] viewArr = this.f23280i;
        if (viewArr == null) {
            return null;
        }
        return viewArr[i5];
    }

    public abstract int k();

    public int l() {
        return this.f23287p;
    }

    public boolean m() {
        return this.f23287p != -1;
    }

    public boolean n() {
        return this.f23283l;
    }

    @Override // android.view.View.OnClickListener
    public void onClick(final View view) {
        if (n()) {
            t(false);
            if (this.f23287p == -1) {
                this.f23287p = ((Integer) view.getTag(c.i.M2)).intValue();
                ArrayList arrayList = new ArrayList(k());
                for (int i5 = 0; i5 < k(); i5++) {
                    arrayList.add(f(this.f23280i[i5], i5, this.f23287p));
                }
                u(arrayList, new Runnable() { // from class: com.loc.va.ui.widget.f
                    @Override // java.lang.Runnable
                    public final void run() {
                        g.this.o(view);
                    }
                }, false);
            }
        }
    }

    /* JADX WARN: Code restructure failed: missing block: B:12:0x002a, code lost:
    
        if (r10 != 3) goto L32;
     */
    @Override // android.view.View.OnTouchListener
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public boolean onTouch(View view, MotionEvent motionEvent) {
        if (!n()) {
            return false;
        }
        float rawY = motionEvent.getRawY();
        int intValue = ((Integer) view.getTag(c.i.M2)).intValue();
        int action = motionEvent.getAction();
        if (action != 0) {
            if (action != 1) {
                if (action == 2) {
                    if (this.f23287p == -1) {
                        p(intValue, rawY - this.f23284m);
                    }
                    this.f23286o += Math.abs(rawY - this.f23285n);
                }
            }
            if (this.f23286o >= this.f23281j || Math.abs(rawY - this.f23284m) >= this.f23281j || this.f23287p != -1) {
                q();
            } else {
                onClick(view);
            }
            this.f23284m = -1.0f;
            this.f23285n = -1.0f;
            this.f23286o = 0.0f;
            return false;
        }
        if (this.f23284m != -1.0f) {
            return false;
        }
        this.f23284m = rawY;
        this.f23285n = rawY;
        this.f23286o = 0.0f;
        return true;
    }

    public void q() {
        r(null);
    }

    public void r(Runnable runnable) {
        ArrayList arrayList = new ArrayList(k());
        for (int i5 = 0; i5 < k(); i5++) {
            arrayList.add(ObjectAnimator.ofFloat(this.f23280i[i5], (Property<View, Float>) View.Y, (int) r3.getY(), i(i5)));
        }
        u(arrayList, runnable, true);
    }

    void s(i iVar) {
        this.f23282k = iVar;
        this.f23280i = new View[k()];
        this.f23274c = iVar.getCardGapBottom();
        this.f23275d = iVar.getCardGap();
        this.f23276e = iVar.getParallaxScale();
        boolean c6 = iVar.c();
        this.f23277f = c6;
        if (c6 && this.f23276e == 0) {
            this.f23277f = false;
        }
        this.f23278g = iVar.d();
        this.f23289r = iVar.getPaddingTop();
        this.f23279h = (int) (((this.f23272a - this.f23273b) - this.f23281j) - (k() * this.f23274c));
    }
}
