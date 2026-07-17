package com.loc.va.ui.widget;

import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import b.j0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class p extends Drawable {

    /* renamed from: a, reason: collision with root package name */
    private Paint f23391a;

    /* renamed from: c, reason: collision with root package name */
    private int f23393c;

    /* renamed from: d, reason: collision with root package name */
    private int f23394d;

    /* renamed from: e, reason: collision with root package name */
    private o f23395e;

    /* renamed from: f, reason: collision with root package name */
    private int f23396f;

    /* renamed from: g, reason: collision with root package name */
    private RectF f23397g;

    /* renamed from: h, reason: collision with root package name */
    private float f23398h;

    /* renamed from: i, reason: collision with root package name */
    private float f23399i;

    /* renamed from: b, reason: collision with root package name */
    private RectF f23392b = new RectF();

    /* renamed from: j, reason: collision with root package name */
    private PorterDuffXfermode f23400j = new PorterDuffXfermode(PorterDuff.Mode.SRC_OUT);

    public p(o oVar, int i5, float f5, float f6) {
        this.f23395e = oVar;
        this.f23396f = oVar.d();
        this.f23398h = f5;
        this.f23399i = f6;
        Paint paint = new Paint();
        this.f23391a = paint;
        paint.setAntiAlias(true);
        this.f23391a.setFilterBitmap(true);
        this.f23391a.setDither(true);
        this.f23391a.setStyle(Paint.Style.FILL);
        this.f23391a.setColor(i5);
        this.f23391a.setShadowLayer(oVar.f(), oVar.b(), oVar.c(), oVar.a());
        this.f23397g = new RectF();
    }

    public p a(int i5) {
        this.f23391a.setColor(i5);
        return this;
    }

    @Override // android.graphics.drawable.Drawable
    public void draw(@j0 Canvas canvas) {
        this.f23391a.setXfermode(null);
        canvas.drawRoundRect(this.f23397g, this.f23398h, this.f23399i, this.f23391a);
        this.f23391a.setXfermode(this.f23400j);
        canvas.drawRoundRect(this.f23397g, this.f23398h, this.f23399i, this.f23391a);
    }

    @Override // android.graphics.drawable.Drawable
    public int getOpacity() {
        return 0;
    }

    @Override // android.graphics.drawable.Drawable
    protected void onBoundsChange(Rect rect) {
        super.onBoundsChange(rect);
        int i5 = rect.right;
        int i6 = rect.left;
        if (i5 - i6 > 0) {
            int i7 = rect.bottom;
            int i8 = rect.top;
            if (i7 - i8 > 0) {
                RectF rectF = this.f23392b;
                float f5 = i6;
                rectF.left = f5;
                float f6 = i5;
                rectF.right = f6;
                float f7 = i8;
                rectF.top = f7;
                float f8 = i7;
                rectF.bottom = f8;
                this.f23393c = (int) (f6 - f5);
                this.f23394d = (int) (f8 - f7);
                int g5 = this.f23395e.g();
                this.f23397g = new RectF((g5 & 1) == 1 ? this.f23396f : 0, (g5 & 16) == 16 ? this.f23396f : 0, this.f23393c - ((g5 & 256) == 256 ? this.f23396f : 0), this.f23394d - ((g5 & 4096) == 4096 ? this.f23396f : 0));
                invalidateSelf();
            }
        }
    }

    @Override // android.graphics.drawable.Drawable
    public void setAlpha(int i5) {
    }

    @Override // android.graphics.drawable.Drawable
    public void setColorFilter(ColorFilter colorFilter) {
    }
}
