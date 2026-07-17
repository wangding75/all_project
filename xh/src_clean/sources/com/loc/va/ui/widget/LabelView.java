package com.loc.va.ui.widget;

import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.util.AttributeSet;
import android.view.View;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class LabelView extends View {
    

    /* renamed from: n, reason: collision with root package name */
    private static final int f23092n = 45;

    /* renamed from: a, reason: collision with root package name */
    private String f23093a;

    /* renamed from: b, reason: collision with root package name */
    private int f23094b;

    /* renamed from: c, reason: collision with root package name */
    private float f23095c;

    /* renamed from: d, reason: collision with root package name */
    private boolean f23096d;

    /* renamed from: e, reason: collision with root package name */
    private boolean f23097e;

    /* renamed from: f, reason: collision with root package name */
    private boolean f23098f;

    /* renamed from: g, reason: collision with root package name */
    private int f23099g;

    /* renamed from: h, reason: collision with root package name */
    private float f23100h;

    /* renamed from: i, reason: collision with root package name */
    private float f23101i;

    /* renamed from: j, reason: collision with root package name */
    private int f23102j;

    /* renamed from: k, reason: collision with root package name */
    private Paint f23103k;

    /* renamed from: l, reason: collision with root package name */
    private Paint f23104l;

    /* renamed from: m, reason: collision with root package name */
    private Path f23105m;

    

    public LabelView(Context context) {
        this(context, null);
    }

    public LabelView(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        this.f23103k = new Paint(1);
        this.f23104l = new Paint(1);
        this.f23105m = new Path();
        h(context, attributeSet);
        this.f23103k.setTextAlign(Paint.Align.CENTER);
    }

    private void b(int i5, float f5, Canvas canvas, float f6, boolean z5) {
        canvas.save();
        float f7 = i5 / 2.0f;
        canvas.rotate(f5, f7, f7);
        float f8 = f6 + (this.f23101i * 2.0f);
        canvas.drawText(this.f23098f ? this.f23093a.toUpperCase() : this.f23093a, getPaddingLeft() + (((i5 - getPaddingLeft()) - getPaddingRight()) / 2), ((i5 / 2) - ((this.f23103k.descent() + this.f23103k.ascent()) / 2.0f)) + (z5 ? (-f8) / 2.0f : f8 / 2.0f), this.f23103k);
        canvas.restore();
    }

    private void c(int i5, float f5, Canvas canvas, boolean z5) {
        canvas.save();
        float f6 = i5 / 2.0f;
        canvas.rotate(f5, f6, f6);
        canvas.drawText(this.f23098f ? this.f23093a.toUpperCase() : this.f23093a, getPaddingLeft() + (((i5 - getPaddingLeft()) - getPaddingRight()) / 2), ((i5 / 2) - ((this.f23103k.descent() + this.f23103k.ascent()) / 2.0f)) + (z5 ? (-i5) / 4 : i5 / 4), this.f23103k);
        canvas.restore();
    }

    private int g(int i5) {
        int mode = View.MeasureSpec.getMode(i5);
        int size = View.MeasureSpec.getSize(i5);
        if (mode == 1073741824) {
            return size;
        }
        int paddingLeft = getPaddingLeft() + getPaddingRight();
        this.f23103k.setColor(this.f23094b);
        this.f23103k.setTextSize(this.f23095c);
        Paint paint = this.f23103k;
        int measureText = (int) ((paddingLeft + ((int) paint.measureText(this.f23093a + ""))) * Math.sqrt(2.0d));
        if (mode == Integer.MIN_VALUE) {
            measureText = Math.min(measureText, size);
        }
        return Math.max((int) this.f23100h, measureText);
    }

    private void h(Context context, AttributeSet attributeSet) {
        TypedArray obtainStyledAttributes = context.obtainStyledAttributes(attributeSet, c.r.hi);
        this.f23093a = obtainStyledAttributes.getString(5);
        this.f23094b = obtainStyledAttributes.getColor(8, Color.parseColor("#ffffff"));
        this.f23095c = obtainStyledAttributes.getDimension(9, i(11.0f));
        this.f23096d = obtainStyledAttributes.getBoolean(7, true);
        this.f23098f = obtainStyledAttributes.getBoolean(6, true);
        this.f23097e = obtainStyledAttributes.getBoolean(1, false);
        this.f23099g = obtainStyledAttributes.getColor(0, Color.parseColor("#FF4081"));
        this.f23100h = obtainStyledAttributes.getDimension(3, a(this.f23097e ? 35.0f : 50.0f));
        this.f23101i = obtainStyledAttributes.getDimension(4, a(3.5f));
        this.f23102j = obtainStyledAttributes.getInt(2, 51);
        obtainStyledAttributes.recycle();
    }

    protected int a(float f5) {
        return (int) ((f5 * getResources().getDisplayMetrics().density) + 0.5f);
    }

    public boolean d() {
        return this.f23097e;
    }

    public boolean e() {
        return this.f23098f;
    }

    public boolean f() {
        return this.f23096d;
    }

    public int getBgColor() {
        return this.f23099g;
    }

    public int getGravity() {
        return this.f23102j;
    }

    public float getMinSize() {
        return this.f23100h;
    }

    public float getPadding() {
        return this.f23101i;
    }

    public String getText() {
        return this.f23093a;
    }

    public int getTextColor() {
        return this.f23094b;
    }

    public float getTextSize() {
        return this.f23095c;
    }

    protected int i(float f5) {
        return (int) ((f5 * getResources().getDisplayMetrics().scaledDensity) + 0.5f);
    }

    @Override // android.view.View
    protected void onDraw(Canvas canvas) {
        float f5;
        boolean z5;
        float f6;
        Path path;
        float f7;
        int height = getHeight();
        this.f23103k.setColor(this.f23094b);
        this.f23103k.setTextSize(this.f23095c);
        this.f23103k.setFakeBoldText(this.f23096d);
        this.f23104l.setColor(this.f23099g);
        float descent = this.f23103k.descent() - this.f23103k.ascent();
        if (this.f23097e) {
            int i5 = this.f23102j;
            boolean z6 = true;
            if (i5 != 51) {
                if (i5 == 53) {
                    this.f23105m.reset();
                    f7 = height;
                    this.f23105m.moveTo(f7, 0.0f);
                } else {
                    z6 = false;
                    if (i5 == 83) {
                        this.f23105m.reset();
                        f7 = height;
                        this.f23105m.moveTo(0.0f, f7);
                    } else {
                        if (i5 != 85) {
                            return;
                        }
                        this.f23105m.reset();
                        f6 = height;
                        this.f23105m.moveTo(f6, f6);
                        path = this.f23105m;
                    }
                }
                this.f23105m.lineTo(0.0f, 0.0f);
                this.f23105m.lineTo(f7, f7);
                this.f23105m.close();
                canvas.drawPath(this.f23105m, this.f23104l);
                c(height, 45.0f, canvas, z6);
                return;
            }
            this.f23105m.reset();
            this.f23105m.moveTo(0.0f, 0.0f);
            path = this.f23105m;
            f6 = height;
            path.lineTo(0.0f, f6);
            this.f23105m.lineTo(f6, 0.0f);
            this.f23105m.close();
            canvas.drawPath(this.f23105m, this.f23104l);
            c(height, -45.0f, canvas, z6);
            return;
        }
        double sqrt = ((this.f23101i * 2.0f) + descent) * Math.sqrt(2.0d);
        int i6 = this.f23102j;
        if (i6 == 51) {
            this.f23105m.reset();
            float f8 = (float) (height - sqrt);
            this.f23105m.moveTo(0.0f, f8);
            float f9 = height;
            this.f23105m.lineTo(0.0f, f9);
            this.f23105m.lineTo(f9, 0.0f);
            this.f23105m.lineTo(f8, 0.0f);
            this.f23105m.close();
            canvas.drawPath(this.f23105m, this.f23104l);
            f5 = -45.0f;
        } else {
            if (i6 != 53) {
                if (i6 == 83) {
                    this.f23105m.reset();
                    this.f23105m.moveTo(0.0f, 0.0f);
                    this.f23105m.lineTo(0.0f, (float) sqrt);
                    float f10 = height;
                    this.f23105m.lineTo((float) (height - sqrt), f10);
                    this.f23105m.lineTo(f10, f10);
                    this.f23105m.close();
                    canvas.drawPath(this.f23105m, this.f23104l);
                    f5 = 45.0f;
                } else {
                    if (i6 != 85) {
                        return;
                    }
                    this.f23105m.reset();
                    float f11 = height;
                    this.f23105m.moveTo(0.0f, f11);
                    float f12 = (float) sqrt;
                    this.f23105m.lineTo(f12, f11);
                    this.f23105m.lineTo(f11, f12);
                    this.f23105m.lineTo(f11, 0.0f);
                    this.f23105m.close();
                    canvas.drawPath(this.f23105m, this.f23104l);
                    f5 = -45.0f;
                }
                z5 = false;
                b(height, f5, canvas, descent, z5);
            }
            this.f23105m.reset();
            this.f23105m.moveTo(0.0f, 0.0f);
            this.f23105m.lineTo((float) sqrt, 0.0f);
            float f13 = height;
            this.f23105m.lineTo(f13, (float) (height - sqrt));
            this.f23105m.lineTo(f13, f13);
            this.f23105m.close();
            canvas.drawPath(this.f23105m, this.f23104l);
            f5 = 45.0f;
        }
        z5 = true;
        b(height, f5, canvas, descent, z5);
    }

    @Override // android.view.View
    protected void onMeasure(int i5, int i6) {
        int g5 = g(i5);
        setMeasuredDimension(g5, g5);
    }

    public void setBgColor(int i5) {
        this.f23099g = i5;
        invalidate();
    }

    public void setFillTriangle(boolean z5) {
        this.f23097e = z5;
        invalidate();
    }

    public void setGravity(int i5) {
        this.f23102j = i5;
    }

    public void setMinSize(float f5) {
        this.f23100h = a(f5);
        invalidate();
    }

    public void setPadding(float f5) {
        this.f23101i = a(f5);
        invalidate();
    }

    public void setText(String str) {
        this.f23093a = str;
        invalidate();
    }

    public void setTextAllCaps(boolean z5) {
        this.f23098f = z5;
        invalidate();
    }

    public void setTextBold(boolean z5) {
        this.f23096d = z5;
        invalidate();
    }

    public void setTextColor(int i5) {
        this.f23094b = i5;
        invalidate();
    }

    public void setTextSize(float f5) {
        this.f23095c = i(f5);
        invalidate();
    }
}
