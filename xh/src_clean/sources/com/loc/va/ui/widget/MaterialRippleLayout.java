package com.loc.va.ui.widget;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.content.Context;
import android.content.res.Resources;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Point;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import android.util.AttributeSet;
import android.util.Property;
import android.util.TypedValue;
import android.view.GestureDetector;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.ViewGroup;
import android.view.ViewParent;
import android.view.animation.AccelerateInterpolator;
import android.view.animation.DecelerateInterpolator;
import android.view.animation.LinearInterpolator;
import android.widget.AdapterView;
import android.widget.FrameLayout;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class MaterialRippleLayout extends FrameLayout {
    
    private static final int G = 350;
    private static final int H = 75;
    private static final float I = 35.0f;
    private static final float J = 0.2f;
    private static final int K = -16777216;
    private static final int L = 0;
    private static final boolean M = true;
    private static final boolean N = true;
    private static final boolean O = false;
    private static final boolean P = false;
    private static final boolean Q = false;
    private static final int R = 0;
    private static final int S = 50;
    private static final long T = 2500;
    private f A;
    private g B;
    private boolean C;
    private Property<MaterialRippleLayout, Float> D;
    private Property<MaterialRippleLayout, Integer> E;
    private GestureDetector.SimpleOnGestureListener F;

    /* renamed from: a, reason: collision with root package name */
    private final Paint f23136a;

    /* renamed from: b, reason: collision with root package name */
    private final Rect f23137b;

    /* renamed from: c, reason: collision with root package name */
    private int f23138c;

    /* renamed from: d, reason: collision with root package name */
    private boolean f23139d;

    /* renamed from: e, reason: collision with root package name */
    private boolean f23140e;

    /* renamed from: f, reason: collision with root package name */
    private int f23141f;

    /* renamed from: g, reason: collision with root package name */
    private int f23142g;

    /* renamed from: h, reason: collision with root package name */
    private int f23143h;

    /* renamed from: i, reason: collision with root package name */
    private boolean f23144i;

    /* renamed from: j, reason: collision with root package name */
    private int f23145j;

    /* renamed from: k, reason: collision with root package name */
    private boolean f23146k;

    /* renamed from: l, reason: collision with root package name */
    private Drawable f23147l;

    /* renamed from: m, reason: collision with root package name */
    private boolean f23148m;

    /* renamed from: n, reason: collision with root package name */
    private float f23149n;

    /* renamed from: o, reason: collision with root package name */
    private float f23150o;

    /* renamed from: p, reason: collision with root package name */
    private AdapterView f23151p;

    /* renamed from: q, reason: collision with root package name */
    private View f23152q;

    /* renamed from: r, reason: collision with root package name */
    private AnimatorSet f23153r;

    /* renamed from: s, reason: collision with root package name */
    private ObjectAnimator f23154s;

    /* renamed from: t, reason: collision with root package name */
    private Point f23155t;

    /* renamed from: u, reason: collision with root package name */
    private Point f23156u;

    /* renamed from: v, reason: collision with root package name */
    private int f23157v;

    /* renamed from: w, reason: collision with root package name */
    private boolean f23158w;

    /* renamed from: x, reason: collision with root package name */
    private boolean f23159x;

    /* renamed from: y, reason: collision with root package name */
    private int f23160y;

    /* renamed from: z, reason: collision with root package name */
    private GestureDetector f23161z;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a extends Property<MaterialRippleLayout, Float> {
        a(Class cls, String str) {
            super(cls, str);
        }

        @Override // android.util.Property
        /* renamed from: a, reason: merged with bridge method [inline-methods] */
        public Float get(MaterialRippleLayout materialRippleLayout) {
            return Float.valueOf(materialRippleLayout.getRadius());
        }

        @Override // android.util.Property
        /* renamed from: b, reason: merged with bridge method [inline-methods] */
        public void set(MaterialRippleLayout materialRippleLayout, Float f5) {
            materialRippleLayout.setRadius(f5.floatValue());
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class b extends Property<MaterialRippleLayout, Integer> {
        b(Class cls, String str) {
            super(cls, str);
        }

        @Override // android.util.Property
        /* renamed from: a, reason: merged with bridge method [inline-methods] */
        public Integer get(MaterialRippleLayout materialRippleLayout) {
            return Integer.valueOf(materialRippleLayout.getRippleAlpha());
        }

        @Override // android.util.Property
        /* renamed from: b, reason: merged with bridge method [inline-methods] */
        public void set(MaterialRippleLayout materialRippleLayout, Integer num) {
            materialRippleLayout.setRippleAlpha(num);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes10.dex */
    class c extends GestureDetector.SimpleOnGestureListener {
        c() {
        }

        @Override // android.view.GestureDetector.SimpleOnGestureListener, android.view.GestureDetector.OnGestureListener
        public boolean onDown(MotionEvent motionEvent) {
            MaterialRippleLayout.this.C = false;
            return super.onDown(motionEvent);
        }

        @Override // android.view.GestureDetector.SimpleOnGestureListener, android.view.GestureDetector.OnGestureListener
        public void onLongPress(MotionEvent motionEvent) {
            MaterialRippleLayout materialRippleLayout = MaterialRippleLayout.this;
            materialRippleLayout.C = materialRippleLayout.f23152q.performLongClick();
            if (MaterialRippleLayout.this.C) {
                if (MaterialRippleLayout.this.f23140e) {
                    MaterialRippleLayout.this.B(null);
                }
                MaterialRippleLayout.this.q();
            }
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class d implements Runnable {
        d() {
        }

        @Override // java.lang.Runnable
        public void run() {
            MaterialRippleLayout.this.f23152q.setPressed(false);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class e extends AnimatorListenerAdapter {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ Runnable f23166a;

        e(Runnable runnable) {
            this.f23166a = runnable;
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            if (!MaterialRippleLayout.this.f23146k) {
                MaterialRippleLayout.this.setRadius(0.0f);
                MaterialRippleLayout materialRippleLayout = MaterialRippleLayout.this;
                materialRippleLayout.setRippleAlpha(Integer.valueOf(materialRippleLayout.f23143h));
            }
            if (this.f23166a != null && MaterialRippleLayout.this.f23144i) {
                this.f23166a.run();
            }
            MaterialRippleLayout.this.f23152q.setPressed(false);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes10.dex */
    private class f implements Runnable {
        private f() {
        }

        /* synthetic */ f(MaterialRippleLayout materialRippleLayout, a aVar) {
            this();
        }

        private void a(AdapterView adapterView) {
            int positionForView = adapterView.getPositionForView(MaterialRippleLayout.this);
            long itemId = adapterView.getAdapter() != null ? adapterView.getAdapter().getItemId(positionForView) : 0L;
            if (positionForView != -1) {
                adapterView.performItemClick(MaterialRippleLayout.this, positionForView, itemId);
            }
        }

        @Override // java.lang.Runnable
        public void run() {
            AdapterView u5;
            if (MaterialRippleLayout.this.C) {
                return;
            }
            if (MaterialRippleLayout.this.getParent() instanceof AdapterView) {
                if (MaterialRippleLayout.this.f23152q.performClick()) {
                    return;
                } else {
                    u5 = (AdapterView) MaterialRippleLayout.this.getParent();
                }
            } else {
                if (!MaterialRippleLayout.this.f23148m) {
                    MaterialRippleLayout.this.f23152q.performClick();
                    return;
                }
                u5 = MaterialRippleLayout.this.u();
            }
            a(u5);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes10.dex */
    private final class g implements Runnable {

        /* renamed from: a, reason: collision with root package name */
        private final MotionEvent f23169a;

        public g(MotionEvent motionEvent) {
            this.f23169a = motionEvent;
        }

        @Override // java.lang.Runnable
        public void run() {
            MaterialRippleLayout.this.f23159x = false;
            MaterialRippleLayout.this.f23152q.setLongClickable(false);
            MaterialRippleLayout.this.f23152q.onTouchEvent(this.f23169a);
            MaterialRippleLayout.this.f23152q.setPressed(true);
            if (MaterialRippleLayout.this.f23140e) {
                MaterialRippleLayout.this.A();
            }
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    public static class h {
        

        /* renamed from: a, reason: collision with root package name */
        private final Context f23171a;

        /* renamed from: b, reason: collision with root package name */
        private final View f23172b;

        /* renamed from: c, reason: collision with root package name */
        private int f23173c = -16777216;

        /* renamed from: d, reason: collision with root package name */
        private boolean f23174d = false;

        /* renamed from: e, reason: collision with root package name */
        private boolean f23175e = true;

        /* renamed from: f, reason: collision with root package name */
        private float f23176f = MaterialRippleLayout.I;

        /* renamed from: g, reason: collision with root package name */
        private int f23177g = MaterialRippleLayout.G;

        /* renamed from: h, reason: collision with root package name */
        private float f23178h = 0.2f;

        /* renamed from: i, reason: collision with root package name */
        private boolean f23179i = true;

        /* renamed from: j, reason: collision with root package name */
        private int f23180j = 75;

        /* renamed from: k, reason: collision with root package name */
        private boolean f23181k = false;

        /* renamed from: l, reason: collision with root package name */
        private int f23182l = 0;

        /* renamed from: m, reason: collision with root package name */
        private boolean f23183m = false;

        /* renamed from: n, reason: collision with root package name */
        private float f23184n = 0.0f;

        

        public h(View view) {
            this.f23172b = view;
            this.f23171a = view.getContext();
        }

        public MaterialRippleLayout a() {
            int i5;
            MaterialRippleLayout materialRippleLayout = new MaterialRippleLayout(this.f23171a);
            materialRippleLayout.setRippleColor(this.f23173c);
            materialRippleLayout.setDefaultRippleAlpha(this.f23178h);
            materialRippleLayout.setRippleDelayClick(this.f23179i);
            materialRippleLayout.setRippleDiameter((int) MaterialRippleLayout.r(this.f23171a.getResources(), this.f23176f));
            materialRippleLayout.setRippleDuration(this.f23177g);
            materialRippleLayout.setRippleFadeDuration(this.f23180j);
            materialRippleLayout.setRippleHover(this.f23175e);
            materialRippleLayout.setRipplePersistent(this.f23181k);
            materialRippleLayout.setRippleOverlay(this.f23174d);
            materialRippleLayout.setRippleBackground(this.f23182l);
            materialRippleLayout.setRippleInAdapter(this.f23183m);
            materialRippleLayout.setRippleRoundedCorners((int) MaterialRippleLayout.r(this.f23171a.getResources(), this.f23184n));
            ViewGroup.LayoutParams layoutParams = this.f23172b.getLayoutParams();
            ViewGroup viewGroup = (ViewGroup) this.f23172b.getParent();
            if (viewGroup != null && (viewGroup instanceof MaterialRippleLayout)) {
                throw new IllegalStateException("MaterialRippleLayout could not be created: parent of the view already is a MaterialRippleLayout");
            }
            if (viewGroup != null) {
                i5 = viewGroup.indexOfChild(this.f23172b);
                viewGroup.removeView(this.f23172b);
            } else {
                i5 = 0;
            }
            materialRippleLayout.addView(this.f23172b, new ViewGroup.LayoutParams(-1, -1));
            if (viewGroup != null) {
                viewGroup.addView(materialRippleLayout, i5, layoutParams);
            }
            return materialRippleLayout;
        }

        public h b(float f5) {
            this.f23178h = f5;
            return this;
        }

        public h c(int i5) {
            this.f23182l = i5;
            return this;
        }

        public h d(int i5) {
            this.f23173c = i5;
            return this;
        }

        public h e(boolean z5) {
            this.f23179i = z5;
            return this;
        }

        public h f(int i5) {
            this.f23176f = i5;
            return this;
        }

        public h g(int i5) {
            this.f23177g = i5;
            return this;
        }

        public h h(int i5) {
            this.f23180j = i5;
            return this;
        }

        public h i(boolean z5) {
            this.f23175e = z5;
            return this;
        }

        public h j(boolean z5) {
            this.f23183m = z5;
            return this;
        }

        public h k(boolean z5) {
            this.f23174d = z5;
            return this;
        }

        public h l(boolean z5) {
            this.f23181k = z5;
            return this;
        }

        public h m(int i5) {
            this.f23184n = i5;
            return this;
        }
    }

    

    public MaterialRippleLayout(Context context) {
        this(context, null, 0);
    }

    public MaterialRippleLayout(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public MaterialRippleLayout(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        Paint paint = new Paint(1);
        this.f23136a = paint;
        this.f23137b = new Rect();
        this.f23155t = new Point();
        this.f23156u = new Point();
        this.D = new a(Float.class, "radius");
        this.E = new b(Integer.class, "rippleAlpha");
        this.F = new c();
        setWillNotDraw(false);
        this.f23161z = new GestureDetector(context, this.F);
        TypedArray obtainStyledAttributes = context.obtainStyledAttributes(attributeSet, c.r.Nl);
        this.f23138c = obtainStyledAttributes.getColor(2, -16777216);
        this.f23141f = obtainStyledAttributes.getDimensionPixelSize(4, (int) r(getResources(), I));
        this.f23139d = obtainStyledAttributes.getBoolean(9, false);
        this.f23140e = obtainStyledAttributes.getBoolean(7, true);
        this.f23142g = obtainStyledAttributes.getInt(5, G);
        this.f23143h = (int) (obtainStyledAttributes.getFloat(0, 0.2f) * 255.0f);
        this.f23144i = obtainStyledAttributes.getBoolean(3, true);
        this.f23145j = obtainStyledAttributes.getInteger(6, 75);
        this.f23147l = new ColorDrawable(obtainStyledAttributes.getColor(1, 0));
        this.f23146k = obtainStyledAttributes.getBoolean(10, false);
        this.f23148m = obtainStyledAttributes.getBoolean(8, false);
        this.f23149n = obtainStyledAttributes.getDimensionPixelSize(11, 0);
        obtainStyledAttributes.recycle();
        paint.setColor(this.f23138c);
        paint.setAlpha(this.f23143h);
        s();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void A() {
        if (this.f23158w) {
            return;
        }
        ObjectAnimator objectAnimator = this.f23154s;
        if (objectAnimator != null) {
            objectAnimator.cancel();
        }
        ObjectAnimator duration = ObjectAnimator.ofFloat(this, this.D, this.f23141f, (float) (Math.sqrt(Math.pow(getWidth(), 2.0d) + Math.pow(getHeight(), 2.0d)) * 1.2000000476837158d)).setDuration(T);
        this.f23154s = duration;
        duration.setInterpolator(new LinearInterpolator());
        this.f23154s.start();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void B(Runnable runnable) {
        if (this.f23158w) {
            return;
        }
        float endRadius = getEndRadius();
        p();
        AnimatorSet animatorSet = new AnimatorSet();
        this.f23153r = animatorSet;
        animatorSet.addListener(new e(runnable));
        ObjectAnimator ofFloat = ObjectAnimator.ofFloat(this, this.D, this.f23150o, endRadius);
        ofFloat.setDuration(this.f23142g);
        ofFloat.setInterpolator(new DecelerateInterpolator());
        ObjectAnimator ofInt = ObjectAnimator.ofInt(this, this.E, this.f23143h, 0);
        ofInt.setDuration(this.f23145j);
        ofInt.setInterpolator(new AccelerateInterpolator());
        ofInt.setStartDelay((this.f23142g - this.f23145j) - 50);
        if (this.f23146k) {
            this.f23153r.play(ofFloat);
        } else if (getRadius() > endRadius) {
            ofInt.setStartDelay(0L);
            this.f23153r.play(ofInt);
        } else {
            this.f23153r.playTogether(ofFloat, ofInt);
        }
        this.f23153r.start();
    }

    private float getEndRadius() {
        int width = getWidth();
        int i5 = width / 2;
        int height = getHeight() / 2;
        Point point = this.f23155t;
        int i6 = point.x;
        return ((float) Math.sqrt(Math.pow(i5 > i6 ? width - i6 : i6, 2.0d) + Math.pow(height > point.y ? r1 - r2 : r2, 2.0d))) * 1.2f;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public float getRadius() {
        return this.f23150o;
    }

    private boolean o() {
        if (!this.f23148m) {
            return false;
        }
        int positionForView = u().getPositionForView(this);
        boolean z5 = positionForView != this.f23160y;
        this.f23160y = positionForView;
        if (z5) {
            q();
            p();
            this.f23152q.setPressed(false);
            setRadius(0.0f);
        }
        return z5;
    }

    private void p() {
        AnimatorSet animatorSet = this.f23153r;
        if (animatorSet != null) {
            animatorSet.cancel();
            this.f23153r.removeAllListeners();
        }
        ObjectAnimator objectAnimator = this.f23154s;
        if (objectAnimator != null) {
            objectAnimator.cancel();
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void q() {
        g gVar = this.B;
        if (gVar != null) {
            removeCallbacks(gVar);
            this.f23159x = false;
        }
    }

    static float r(Resources resources, float f5) {
        return TypedValue.applyDimension(1, f5, resources.getDisplayMetrics());
    }

    private void s() {
    }

    private boolean t(View view, int i5, int i6) {
        if (view instanceof ViewGroup) {
            ViewGroup viewGroup = (ViewGroup) view;
            for (int i7 = 0; i7 < viewGroup.getChildCount(); i7++) {
                View childAt = viewGroup.getChildAt(i7);
                Rect rect = new Rect();
                childAt.getHitRect(rect);
                if (rect.contains(i5, i6)) {
                    return t(childAt, i5 - rect.left, i6 - rect.top);
                }
            }
        } else if (view != this.f23152q) {
            if (view.isEnabled()) {
                return view.isClickable() || view.isLongClickable() || view.isFocusableInTouchMode();
            }
            return false;
        }
        return view.isFocusableInTouchMode();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public AdapterView u() {
        AdapterView adapterView = this.f23151p;
        if (adapterView != null) {
            return adapterView;
        }
        ViewParent parent = getParent();
        while (!(parent instanceof AdapterView)) {
            try {
                parent = parent.getParent();
            } catch (NullPointerException unused) {
                throw new RuntimeException("Could not find a parent AdapterView");
            }
        }
        AdapterView adapterView2 = (AdapterView) parent;
        this.f23151p = adapterView2;
        return adapterView2;
    }

    private boolean v() {
        for (ViewParent parent = getParent(); parent != null && (parent instanceof ViewGroup); parent = parent.getParent()) {
            if (((ViewGroup) parent).shouldDelayChildPressedState()) {
                return true;
            }
        }
        return false;
    }

    public static h w(View view) {
        return new h(view);
    }

    private void z() {
        if (this.f23148m) {
            this.f23160y = u().getPositionForView(this);
        }
    }

    @Override // android.view.ViewGroup
    public final void addView(View view, int i5, ViewGroup.LayoutParams layoutParams) {
        if (getChildCount() > 0) {
            throw new IllegalStateException("MaterialRippleLayout can host only one child");
        }
        this.f23152q = view;
        super.addView(view, i5, layoutParams);
    }

    @Override // android.view.View
    public void draw(Canvas canvas) {
        boolean o5 = o();
        if (!this.f23139d) {
            if (!o5) {
                this.f23147l.draw(canvas);
                Point point = this.f23155t;
                canvas.drawCircle(point.x, point.y, this.f23150o, this.f23136a);
            }
            super.draw(canvas);
            return;
        }
        if (!o5) {
            this.f23147l.draw(canvas);
        }
        super.draw(canvas);
        if (o5) {
            return;
        }
        if (this.f23149n != 0.0f) {
            Path path = new Path();
            RectF rectF = new RectF(0.0f, 0.0f, canvas.getWidth(), canvas.getHeight());
            float f5 = this.f23149n;
            path.addRoundRect(rectF, f5, f5, Path.Direction.CW);
            canvas.clipPath(path);
        }
        Point point2 = this.f23155t;
        canvas.drawCircle(point2.x, point2.y, this.f23150o, this.f23136a);
    }

    public <T extends View> T getChildView() {
        return (T) this.f23152q;
    }

    public int getRippleAlpha() {
        return this.f23136a.getAlpha();
    }

    @Override // android.view.View
    public boolean isInEditMode() {
        return true;
    }

    @Override // android.view.ViewGroup
    public boolean onInterceptTouchEvent(MotionEvent motionEvent) {
        return !t(this.f23152q, (int) motionEvent.getX(), (int) motionEvent.getY());
    }

    @Override // android.view.View
    protected void onSizeChanged(int i5, int i6, int i7, int i8) {
        super.onSizeChanged(i5, i6, i7, i8);
        this.f23137b.set(0, 0, i5, i6);
        this.f23147l.setBounds(this.f23137b);
    }

    @Override // android.view.View
    public boolean onTouchEvent(MotionEvent motionEvent) {
        boolean onTouchEvent = super.onTouchEvent(motionEvent);
        if (!isEnabled() || !this.f23152q.isEnabled()) {
            return onTouchEvent;
        }
        boolean contains = this.f23137b.contains((int) motionEvent.getX(), (int) motionEvent.getY());
        if (contains) {
            Point point = this.f23156u;
            Point point2 = this.f23155t;
            point.set(point2.x, point2.y);
            this.f23155t.set((int) motionEvent.getX(), (int) motionEvent.getY());
        }
        if (!this.f23161z.onTouchEvent(motionEvent) && !this.C) {
            int actionMasked = motionEvent.getActionMasked();
            if (actionMasked != 0) {
                a aVar = null;
                if (actionMasked == 1) {
                    this.A = new f(this, aVar);
                    if (this.f23159x) {
                        this.f23152q.setPressed(true);
                        postDelayed(new d(), ViewConfiguration.getPressedStateDuration());
                    }
                    if (contains) {
                        B(this.A);
                    } else if (!this.f23140e) {
                        setRadius(0.0f);
                    }
                    if (!this.f23144i && contains) {
                        this.A.run();
                    }
                } else if (actionMasked == 2) {
                    if (this.f23140e) {
                        if (contains && !this.f23158w) {
                            invalidate();
                        } else if (!contains) {
                            B(null);
                        }
                    }
                    if (!contains) {
                        q();
                        ObjectAnimator objectAnimator = this.f23154s;
                        if (objectAnimator != null) {
                            objectAnimator.cancel();
                        }
                        this.f23152q.onTouchEvent(motionEvent);
                        this.f23158w = true;
                    }
                } else if (actionMasked == 3) {
                    if (this.f23148m) {
                        Point point3 = this.f23155t;
                        Point point4 = this.f23156u;
                        point3.set(point4.x, point4.y);
                        this.f23156u = new Point();
                    }
                    this.f23152q.onTouchEvent(motionEvent);
                    if (!this.f23140e) {
                        this.f23152q.setPressed(false);
                    } else if (!this.f23159x) {
                        B(null);
                    }
                }
                q();
            } else {
                z();
                this.f23158w = false;
                this.B = new g(motionEvent);
                if (v()) {
                    q();
                    this.f23159x = true;
                    postDelayed(this.B, ViewConfiguration.getTapTimeout());
                } else {
                    this.B.run();
                }
            }
        }
        return true;
    }

    public void setDefaultRippleAlpha(float f5) {
        int i5 = (int) (f5 * 255.0f);
        this.f23143h = i5;
        this.f23136a.setAlpha(i5);
        invalidate();
    }

    @Override // android.view.View
    public void setOnClickListener(View.OnClickListener onClickListener) {
        View view = this.f23152q;
        if (view == null) {
            throw new IllegalStateException("MaterialRippleLayout must have a child view to handle clicks");
        }
        view.setOnClickListener(onClickListener);
    }

    @Override // android.view.View
    public void setOnLongClickListener(View.OnLongClickListener onLongClickListener) {
        View view = this.f23152q;
        if (view == null) {
            throw new IllegalStateException("MaterialRippleLayout must have a child view to handle clicks");
        }
        view.setOnLongClickListener(onLongClickListener);
    }

    public void setRadius(float f5) {
        this.f23150o = f5;
        invalidate();
    }

    public void setRippleAlpha(Integer num) {
        this.f23136a.setAlpha(num.intValue());
        invalidate();
    }

    public void setRippleBackground(int i5) {
        ColorDrawable colorDrawable = new ColorDrawable(i5);
        this.f23147l = colorDrawable;
        colorDrawable.setBounds(this.f23137b);
        invalidate();
    }

    public void setRippleColor(int i5) {
        this.f23138c = i5;
        this.f23136a.setColor(i5);
        this.f23136a.setAlpha(this.f23143h);
        invalidate();
    }

    public void setRippleDelayClick(boolean z5) {
        this.f23144i = z5;
    }

    public void setRippleDiameter(int i5) {
        this.f23141f = i5;
    }

    public void setRippleDuration(int i5) {
        this.f23142g = i5;
    }

    public void setRippleFadeDuration(int i5) {
        this.f23145j = i5;
    }

    public void setRippleHover(boolean z5) {
        this.f23140e = z5;
    }

    public void setRippleInAdapter(boolean z5) {
        this.f23148m = z5;
    }

    public void setRippleOverlay(boolean z5) {
        this.f23139d = z5;
    }

    public void setRipplePersistent(boolean z5) {
        this.f23146k = z5;
    }

    public void setRippleRoundedCorners(int i5) {
        this.f23149n = i5;
        s();
    }

    public void x() {
        this.f23155t = new Point(getWidth() / 2, getHeight() / 2);
        B(null);
    }

    public void y(Point point) {
        this.f23155t = new Point(point.x, point.y);
        B(null);
    }
}
