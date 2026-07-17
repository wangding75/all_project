package com.loc.va.ui.widget;

import android.content.res.TypedArray;
import android.graphics.LinearGradient;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Shader;
import android.util.AttributeSet;
import android.util.Log;
import android.view.View;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class s {
    

    /* renamed from: k, reason: collision with root package name */
    private static final int f23444k = -1;

    /* renamed from: a, reason: collision with root package name */
    private View f23445a;

    /* renamed from: b, reason: collision with root package name */
    private Paint f23446b;

    /* renamed from: c, reason: collision with root package name */
    private float f23447c;

    /* renamed from: d, reason: collision with root package name */
    private LinearGradient f23448d;

    /* renamed from: e, reason: collision with root package name */
    private Matrix f23449e;

    /* renamed from: f, reason: collision with root package name */
    private int f23450f;

    /* renamed from: g, reason: collision with root package name */
    private int f23451g;

    /* renamed from: h, reason: collision with root package name */
    private boolean f23452h;

    /* renamed from: i, reason: collision with root package name */
    private boolean f23453i;

    /* renamed from: j, reason: collision with root package name */
    private a f23454j;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    public interface a {
        void a(View view);
    }

    

    public s(View view, Paint paint, AttributeSet attributeSet) {
        this.f23445a = view;
        this.f23446b = paint;
        d(attributeSet);
    }

    private void d(AttributeSet attributeSet) {
        this.f23451g = -1;
        if (attributeSet != null) {
            TypedArray obtainStyledAttributes = this.f23445a.getContext().obtainStyledAttributes(attributeSet, c.r.wr, 0, 0);
            try {
                if (obtainStyledAttributes != null) {
                    try {
                        this.f23451g = obtainStyledAttributes.getColor(0, -1);
                    } catch (Exception e6) {
                        Log.e("ShimmerTextView", "Error while creating the view:", e6);
                    }
                }
            } finally {
                obtainStyledAttributes.recycle();
            }
        }
        this.f23449e = new Matrix();
    }

    private void i() {
        float f5 = -this.f23445a.getWidth();
        int i5 = this.f23450f;
        LinearGradient linearGradient = new LinearGradient(f5, 0.0f, 0.0f, 0.0f, new int[]{i5, this.f23451g, i5}, new float[]{0.0f, 0.5f, 1.0f}, Shader.TileMode.CLAMP);
        this.f23448d = linearGradient;
        this.f23446b.setShader(linearGradient);
    }

    public float a() {
        return this.f23447c;
    }

    public int b() {
        return this.f23450f;
    }

    public int c() {
        return this.f23451g;
    }

    public boolean e() {
        return this.f23453i;
    }

    public boolean f() {
        return this.f23452h;
    }

    public void g() {
        if (!this.f23452h) {
            this.f23446b.setShader(null);
            return;
        }
        if (this.f23446b.getShader() == null) {
            this.f23446b.setShader(this.f23448d);
        }
        this.f23449e.setTranslate(this.f23447c * 2.0f, 0.0f);
        this.f23448d.setLocalMatrix(this.f23449e);
    }

    protected void h() {
        i();
        if (this.f23453i) {
            return;
        }
        this.f23453i = true;
        a aVar = this.f23454j;
        if (aVar != null) {
            aVar.a(this.f23445a);
        }
    }

    public void j(a aVar) {
        this.f23454j = aVar;
    }

    public void k(float f5) {
        this.f23447c = f5;
        this.f23445a.invalidate();
    }

    public void l(int i5) {
        this.f23450f = i5;
        if (this.f23453i) {
            i();
        }
    }

    public void m(int i5) {
        this.f23451g = i5;
        if (this.f23453i) {
            i();
        }
    }

    public void n(boolean z5) {
        this.f23452h = z5;
    }
}
