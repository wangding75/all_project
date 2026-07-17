package com.loc.va.ui.widget;

import android.annotation.TargetApi;
import android.content.Context;
import android.content.res.TypedArray;
import android.util.AttributeSet;
import android.view.View;
import android.widget.FrameLayout;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class i extends FrameLayout {

    /* renamed from: h, reason: collision with root package name */
    public static final boolean f23295h = false;

    /* renamed from: i, reason: collision with root package name */
    public static final boolean f23296i = true;

    /* renamed from: a, reason: collision with root package name */
    private float f23297a;

    /* renamed from: b, reason: collision with root package name */
    private float f23298b;

    /* renamed from: c, reason: collision with root package name */
    private boolean f23299c;

    /* renamed from: d, reason: collision with root package name */
    private boolean f23300d;

    /* renamed from: e, reason: collision with root package name */
    private int f23301e;

    /* renamed from: f, reason: collision with root package name */
    private a f23302f;

    /* renamed from: g, reason: collision with root package name */
    private g f23303g;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    public interface a {
        void a(View view, int i5);
    }

    public i(Context context) {
        super(context);
        this.f23302f = null;
        this.f23303g = null;
        f();
    }

    public i(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public i(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23302f = null;
        this.f23303g = null;
        a(context, attributeSet, i5, 0);
    }

    @TargetApi(21)
    public i(Context context, AttributeSet attributeSet, int i5, int i6) {
        super(context, attributeSet, i5, i6);
        this.f23302f = null;
        this.f23303g = null;
        a(context, attributeSet, i5, i6);
    }

    private void a(Context context, AttributeSet attributeSet, int i5, int i6) {
        f();
        TypedArray obtainStyledAttributes = context.getTheme().obtainStyledAttributes(attributeSet, c.r.s5, i5, i6);
        this.f23300d = obtainStyledAttributes.getBoolean(2, false);
        this.f23299c = obtainStyledAttributes.getBoolean(4, true);
        this.f23301e = obtainStyledAttributes.getInteger(3, getResources().getInteger(c.j.C));
        this.f23298b = obtainStyledAttributes.getDimension(0, getResources().getDimension(c.g.E0));
        this.f23297a = obtainStyledAttributes.getDimension(1, getResources().getDimension(c.g.F0));
        obtainStyledAttributes.recycle();
    }

    private void f() {
        this.f23302f = null;
    }

    public boolean b() {
        return this.f23303g.m();
    }

    public boolean c() {
        return this.f23300d;
    }

    public boolean d() {
        return this.f23299c;
    }

    public void e() {
        if (getChildCount() > 0) {
            removeAllViews();
        }
        this.f23303g = null;
        this.f23302f = null;
    }

    public void g() {
        this.f23303g.q();
    }

    public g getAdapter() {
        return this.f23303g;
    }

    public float getCardGap() {
        return this.f23298b;
    }

    public float getCardGapBottom() {
        return this.f23297a;
    }

    a getOnCardSelectedListener() {
        return this.f23302f;
    }

    public int getParallaxScale() {
        return this.f23301e;
    }

    public void setAdapter(g gVar) {
        this.f23303g = gVar;
        gVar.s(this);
        for (int i5 = 0; i5 < this.f23303g.k(); i5++) {
            this.f23303g.d(i5);
        }
        if (this.f23299c) {
            postDelayed(new Runnable() { // from class: com.loc.va.ui.widget.h
                @Override // java.lang.Runnable
                public final void run() {
                    i.this.g();
                }
            }, 500L);
        }
    }

    public void setCardGap(float f5) {
        this.f23298b = f5;
    }

    public void setCardGapBottom(float f5) {
        this.f23297a = f5;
    }

    public void setOnCardSelectedListener(a aVar) {
        this.f23302f = aVar;
    }

    public void setParallaxEnabled(boolean z5) {
        this.f23300d = z5;
    }

    public void setParallaxScale(int i5) {
        this.f23301e = i5;
    }

    public void setShowInitAnimation(boolean z5) {
        this.f23299c = z5;
    }
}
