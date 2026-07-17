package com.loc.va.ui.widget.quicksidebar;

import android.R;
import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.Typeface;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;
import com.loc.va.c;
import java.util.Arrays;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class QuickSideBarView extends View {

    /* renamed from: a, reason: collision with root package name */
    private r1.a f23418a;

    /* renamed from: b, reason: collision with root package name */
    private List<String> f23419b;

    /* renamed from: c, reason: collision with root package name */
    private int f23420c;

    /* renamed from: d, reason: collision with root package name */
    private Paint f23421d;

    /* renamed from: e, reason: collision with root package name */
    private float f23422e;

    /* renamed from: f, reason: collision with root package name */
    private float f23423f;

    /* renamed from: g, reason: collision with root package name */
    private int f23424g;

    /* renamed from: h, reason: collision with root package name */
    private int f23425h;

    /* renamed from: i, reason: collision with root package name */
    private int f23426i;

    /* renamed from: j, reason: collision with root package name */
    private int f23427j;

    /* renamed from: k, reason: collision with root package name */
    private float f23428k;

    /* renamed from: l, reason: collision with root package name */
    private float f23429l;

    public QuickSideBarView(Context context) {
        this(context, null);
    }

    public QuickSideBarView(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public QuickSideBarView(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23420c = -1;
        this.f23421d = new Paint();
        a(context, attributeSet);
    }

    private void a(Context context, AttributeSet attributeSet) {
        this.f23419b = Arrays.asList(context.getResources().getStringArray(c.C0208c.f21021b));
        this.f23424g = context.getResources().getColor(R.color.black);
        this.f23425h = context.getResources().getColor(2131099779);
        this.f23422e = context.getResources().getDimensionPixelSize(c.g.B7);
        this.f23423f = context.getResources().getDimensionPixelSize(c.g.C7);
        this.f23428k = context.getResources().getDimension(c.g.f21370d2);
        if (attributeSet != null) {
            TypedArray obtainStyledAttributes = getContext().obtainStyledAttributes(attributeSet, c.r.Xp);
            this.f23424g = obtainStyledAttributes.getColor(2, this.f23424g);
            this.f23425h = obtainStyledAttributes.getColor(3, this.f23425h);
            this.f23422e = obtainStyledAttributes.getDimension(4, this.f23422e);
            this.f23423f = obtainStyledAttributes.getDimension(5, this.f23423f);
            this.f23428k = obtainStyledAttributes.getDimension(1, this.f23428k);
            obtainStyledAttributes.recycle();
        }
    }

    @Override // android.view.View
    public boolean dispatchTouchEvent(MotionEvent motionEvent) {
        r1.a aVar;
        int action = motionEvent.getAction();
        float y5 = motionEvent.getY();
        int i5 = this.f23420c;
        int i6 = (int) ((y5 - this.f23429l) / this.f23428k);
        if (action != 1) {
            if (i5 != i6) {
                if (i6 >= 0 && i6 < this.f23419b.size()) {
                    this.f23420c = i6;
                    if (this.f23418a != null) {
                        this.f23421d.getTextBounds(this.f23419b.get(this.f23420c), 0, this.f23419b.get(this.f23420c).length(), new Rect());
                        this.f23418a.b(this.f23419b.get(i6), this.f23420c, (this.f23420c * this.f23428k) + ((int) ((r2 - r0.height()) * 0.5d)) + this.f23429l);
                    }
                }
                invalidate();
            }
            if (motionEvent.getAction() == 3) {
                r1.a aVar2 = this.f23418a;
                if (aVar2 != null) {
                    aVar2.a(false);
                }
            } else if (motionEvent.getAction() == 0 && (aVar = this.f23418a) != null) {
                aVar.a(true);
            }
        } else {
            r1.a aVar3 = this.f23418a;
            if (aVar3 != null) {
                aVar3.a(false);
            }
            invalidate();
        }
        return true;
    }

    public List<String> getLetters() {
        return this.f23419b;
    }

    public r1.a getListener() {
        return this.f23418a;
    }

    @Override // android.view.View
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        for (int i5 = 0; i5 < this.f23419b.size(); i5++) {
            this.f23421d.setColor(this.f23424g);
            this.f23421d.setAntiAlias(true);
            this.f23421d.setTextSize(this.f23422e);
            this.f23421d.setTypeface(Typeface.DEFAULT);
            this.f23421d.setFakeBoldText(false);
            if (i5 == this.f23420c) {
                this.f23421d.setColor(this.f23425h);
                this.f23421d.setFakeBoldText(true);
                this.f23421d.setTypeface(Typeface.DEFAULT_BOLD);
                this.f23421d.setTextSize(this.f23423f);
            }
            this.f23421d.getTextBounds(this.f23419b.get(i5), 0, this.f23419b.get(i5).length(), new Rect());
            canvas.drawText(this.f23419b.get(i5), (int) ((this.f23426i - r2.width()) * 0.5d), (i5 * this.f23428k) + ((int) ((r4 - r2.height()) * 0.5d)) + this.f23429l, this.f23421d);
            this.f23421d.reset();
        }
    }

    @Override // android.view.View
    protected void onMeasure(int i5, int i6) {
        super.onMeasure(i5, i6);
        this.f23427j = getMeasuredHeight();
        this.f23426i = getMeasuredWidth();
        this.f23429l = (this.f23427j - (this.f23419b.size() * this.f23428k)) / 2.0f;
    }

    public void setChooseLetter(int i5) {
        if (this.f23420c != i5) {
            if (i5 >= 0 && i5 < this.f23419b.size()) {
                this.f23420c = i5;
            }
            invalidate();
        }
    }

    public void setLetters(List<String> list) {
        this.f23419b = list;
        invalidate();
    }

    public void setOnQuickSideBarTouchListener(r1.a aVar) {
        this.f23418a = aVar;
    }
}
