package com.loc.va.ui.widget;

import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.icu.lang.UCharacter;
import android.os.Handler;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;
import androidx.core.view.f2;
import androidx.recyclerview.widget.RecyclerView;
import b.k0;
import com.loc.va.c;
import java.net.HttpURLConnection;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class DragSelectRecyclerView extends RecyclerView {
    

    /* renamed from: x, reason: collision with root package name */
    private static final boolean f23054x = false;

    /* renamed from: y, reason: collision with root package name */
    private static final int f23055y = 25;

    /* renamed from: a, reason: collision with root package name */
    private int f23056a;

    /* renamed from: b, reason: collision with root package name */
    private k<?> f23057b;

    /* renamed from: c, reason: collision with root package name */
    private int f23058c;

    /* renamed from: d, reason: collision with root package name */
    private boolean f23059d;

    /* renamed from: e, reason: collision with root package name */
    private int f23060e;

    /* renamed from: f, reason: collision with root package name */
    private int f23061f;

    /* renamed from: g, reason: collision with root package name */
    private int f23062g;

    /* renamed from: h, reason: collision with root package name */
    private int f23063h;

    /* renamed from: i, reason: collision with root package name */
    private int f23064i;

    /* renamed from: j, reason: collision with root package name */
    private int f23065j;

    /* renamed from: k, reason: collision with root package name */
    private int f23066k;

    /* renamed from: l, reason: collision with root package name */
    private int f23067l;

    /* renamed from: m, reason: collision with root package name */
    private int f23068m;

    /* renamed from: n, reason: collision with root package name */
    private int f23069n;

    /* renamed from: o, reason: collision with root package name */
    private b f23070o;

    /* renamed from: p, reason: collision with root package name */
    private boolean f23071p;

    /* renamed from: q, reason: collision with root package name */
    private boolean f23072q;

    /* renamed from: r, reason: collision with root package name */
    private Handler f23073r;

    /* renamed from: s, reason: collision with root package name */
    private Runnable f23074s;

    /* renamed from: t, reason: collision with root package name */
    private RectF f23075t;

    /* renamed from: u, reason: collision with root package name */
    private RectF f23076u;

    /* renamed from: v, reason: collision with root package name */
    private Paint f23077v;

    /* renamed from: w, reason: collision with root package name */
    private boolean f23078w;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a implements Runnable {
        a() {
        }

        @Override // java.lang.Runnable
        public void run() {
            DragSelectRecyclerView dragSelectRecyclerView;
            int i5;
            if (DragSelectRecyclerView.this.f23073r == null) {
                return;
            }
            if (DragSelectRecyclerView.this.f23071p) {
                dragSelectRecyclerView = DragSelectRecyclerView.this;
                i5 = -dragSelectRecyclerView.f23069n;
            } else {
                if (!DragSelectRecyclerView.this.f23072q) {
                    return;
                }
                dragSelectRecyclerView = DragSelectRecyclerView.this;
                i5 = dragSelectRecyclerView.f23069n;
            }
            dragSelectRecyclerView.scrollBy(0, i5);
            DragSelectRecyclerView.this.f23073r.postDelayed(this, 25L);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    public interface b {
        void a(boolean z5);
    }

    

    public DragSelectRecyclerView(Context context) {
        super(context);
        this.f23056a = -1;
        this.f23074s = new a();
        this.f23078w = false;
        i(context, null);
    }

    public DragSelectRecyclerView(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        this.f23056a = -1;
        this.f23074s = new a();
        this.f23078w = false;
        i(context, attributeSet);
    }

    public DragSelectRecyclerView(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23056a = -1;
        this.f23074s = new a();
        this.f23078w = false;
        i(context, attributeSet);
    }

    private static void a(String str, Object... objArr) {
    }

    private int h(MotionEvent motionEvent) {
        View findChildViewUnder = findChildViewUnder(motionEvent.getX(), motionEvent.getY());
        if (findChildViewUnder == null) {
            return -1;
        }
        if (findChildViewUnder.getTag() == null || !(findChildViewUnder.getTag() instanceof RecyclerView.e0)) {
            throw new IllegalStateException("Make sure your adapter makes a call to super.onBindViewHolder(), and doesn't override itemView tags.");
        }
        return ((RecyclerView.e0) findChildViewUnder.getTag()).getAdapterPosition();
    }

    private void i(Context context, AttributeSet attributeSet) {
        this.f23073r = new Handler();
        int dimensionPixelSize = context.getResources().getDimensionPixelSize(c.g.Y1);
        String $2 = "Hotspot height = %d";
        if (attributeSet == null) {
            this.f23062g = dimensionPixelSize;
            a($2, Integer.valueOf(dimensionPixelSize));
            return;
        }
        TypedArray obtainStyledAttributes = context.getTheme().obtainStyledAttributes(attributeSet, c.r.me, 0, 0);
        try {
            if (obtainStyledAttributes.getBoolean(0, true)) {
                this.f23062g = obtainStyledAttributes.getDimensionPixelSize(1, dimensionPixelSize);
                this.f23063h = obtainStyledAttributes.getDimensionPixelSize(3, 0);
                this.f23064i = obtainStyledAttributes.getDimensionPixelSize(2, 0);
                a($2, Integer.valueOf(this.f23062g));
            } else {
                this.f23062g = -1;
                this.f23063h = -1;
                this.f23064i = -1;
                a("Auto-scroll disabled", new Object[0]);
            }
        } finally {
            obtainStyledAttributes.recycle();
        }
    }

    @Override // android.view.ViewGroup, android.view.View
    public boolean dispatchTouchEvent(MotionEvent motionEvent) {
        if (this.f23057b.getItemCount() == 0) {
            return super.dispatchTouchEvent(motionEvent);
        }
        if (this.f23059d) {
            if (motionEvent.getAction() == 1) {
                this.f23059d = false;
                this.f23071p = false;
                this.f23072q = false;
                this.f23073r.removeCallbacks(this.f23074s);
                b bVar = this.f23070o;
                if (bVar != null) {
                    bVar.a(false);
                }
                return true;
            }
            if (motionEvent.getAction() == 2) {
                if (this.f23062g > -1) {
                    float y5 = motionEvent.getY();
                    float f5 = this.f23065j;
                    String $2 = "Auto scroll velocity = %d";
                    if (y5 >= f5 && motionEvent.getY() <= this.f23066k) {
                        this.f23072q = false;
                        if (!this.f23071p) {
                            this.f23071p = true;
                            a("Now in TOP hotspot", new Object[0]);
                            this.f23073r.removeCallbacks(this.f23074s);
                            this.f23073r.postDelayed(this.f23074s, 25L);
                        }
                        int y6 = ((int) ((this.f23066k - this.f23065j) - (motionEvent.getY() - this.f23065j))) / 2;
                        this.f23069n = y6;
                        a($2, Integer.valueOf(y6));
                    } else if (motionEvent.getY() >= this.f23067l && motionEvent.getY() <= this.f23068m) {
                        this.f23071p = false;
                        if (!this.f23072q) {
                            this.f23072q = true;
                            a("Now in BOTTOM hotspot", new Object[0]);
                            this.f23073r.removeCallbacks(this.f23074s);
                            this.f23073r.postDelayed(this.f23074s, 25L);
                        }
                        int y7 = ((int) ((motionEvent.getY() + this.f23068m) - (this.f23067l + r0))) / 2;
                        this.f23069n = y7;
                        a($2, Integer.valueOf(y7));
                    } else if (this.f23071p || this.f23072q) {
                        a("Left the hotspot", new Object[0]);
                        this.f23073r.removeCallbacks(this.f23074s);
                        this.f23071p = false;
                        this.f23072q = false;
                    }
                }
                return true;
            }
        }
        return super.dispatchTouchEvent(motionEvent);
    }

    public final void g() {
        this.f23078w = true;
        invalidate();
    }

    public boolean j(boolean z5, int i5) {
        if (z5 && this.f23059d) {
            a("Drag selection is already active.", new Object[0]);
            return false;
        }
        this.f23056a = -1;
        this.f23060e = -1;
        this.f23061f = -1;
        if (!this.f23057b.e(i5)) {
            this.f23059d = false;
            this.f23058c = -1;
            this.f23056a = -1;
            a("Index %d is not selectable.܆ܰܣܥݢܱܧܮܧܡܶܫܭܬݢܫ", Integer.valueOf(i5));
            return false;
        }
        this.f23057b.n(i5, true);
        this.f23059d = z5;
        this.f23058c = i5;
        this.f23056a = i5;
        b bVar = this.f23070o;
        if (bVar != null) {
            bVar.a(true);
        }
        a("nitialized, starting at index %d.", Integer.valueOf(i5));
        return true;
    }

    @Override // androidx.recyclerview.widget.RecyclerView, android.view.View
    public void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (this.f23078w) {
            if (this.f23077v == null) {
                Paint paint = new Paint();
                this.f23077v = paint;
                paint.setColor(f2.f6745t);
                this.f23077v.setAntiAlias(true);
                this.f23077v.setStyle(Paint.Style.FILL);
                this.f23075t = new RectF(0.0f, this.f23065j, getMeasuredWidth(), this.f23066k);
                this.f23076u = new RectF(0.0f, this.f23067l, getMeasuredWidth(), this.f23068m);
            }
            canvas.drawRect(this.f23075t, this.f23077v);
            canvas.drawRect(this.f23076u, this.f23077v);
        }
    }

    @Override // androidx.recyclerview.widget.RecyclerView, android.view.View
    protected void onMeasure(int i5, int i6) {
        super.onMeasure(i5, i6);
        int i7 = this.f23062g;
        if (i7 > -1) {
            int i8 = this.f23063h;
            this.f23065j = i8;
            this.f23066k = i8 + i7;
            this.f23067l = (getMeasuredHeight() - this.f23062g) - this.f23064i;
            this.f23068m = getMeasuredHeight() - this.f23064i;
            a("RecyclerView height = %d", Integer.valueOf(getMeasuredHeight()));
            a("Hotspot top bound = %d to %d", Integer.valueOf(this.f23065j), Integer.valueOf(this.f23065j));
            a("Hotspot bottom bound = %d to %d", Integer.valueOf(this.f23067l), Integer.valueOf(this.f23068m));
        }
    }

    @Override // androidx.recyclerview.widget.RecyclerView
    @Deprecated
    public void setAdapter(RecyclerView.g gVar) {
        if (!(gVar instanceof k)) {
            throw new IllegalArgumentException("Adapter must be a DragSelectRecyclerViewAdapter.");
        }
        setAdapter((k<?>) gVar);
    }

    public void setAdapter(k<?> kVar) {
        super.setAdapter((RecyclerView.g) kVar);
        this.f23057b = kVar;
    }

    public void setFingerListener(@k0 b bVar) {
        this.f23070o = bVar;
    }
}
