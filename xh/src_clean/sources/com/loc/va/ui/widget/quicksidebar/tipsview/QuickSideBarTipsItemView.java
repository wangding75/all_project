package com.loc.va.ui.widget.quicksidebar.tipsview;

import android.R;
import android.annotation.TargetApi;
import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.text.TextUtils;
import android.util.AttributeSet;
import android.view.View;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class QuickSideBarTipsItemView extends View {

    /* renamed from: a, reason: collision with root package name */
    private int f23431a;

    /* renamed from: b, reason: collision with root package name */
    private Path f23432b;

    /* renamed from: c, reason: collision with root package name */
    private RectF f23433c;

    /* renamed from: d, reason: collision with root package name */
    private Paint f23434d;

    /* renamed from: e, reason: collision with root package name */
    private String f23435e;

    /* renamed from: f, reason: collision with root package name */
    private Paint f23436f;

    /* renamed from: g, reason: collision with root package name */
    private int f23437g;

    /* renamed from: h, reason: collision with root package name */
    private int f23438h;

    /* renamed from: i, reason: collision with root package name */
    private float f23439i;

    /* renamed from: j, reason: collision with root package name */
    private int f23440j;

    /* renamed from: k, reason: collision with root package name */
    private int f23441k;

    /* renamed from: l, reason: collision with root package name */
    private int f23442l;

    /* renamed from: m, reason: collision with root package name */
    private int f23443m;

    public QuickSideBarTipsItemView(Context context) {
        this(context, null);
    }

    public QuickSideBarTipsItemView(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public QuickSideBarTipsItemView(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23432b = new Path();
        this.f23433c = new RectF();
        this.f23435e = "";
        a(context, attributeSet);
    }

    private void a(Context context, AttributeSet attributeSet) {
        this.f23440j = context.getResources().getColor(R.color.black);
        this.f23441k = context.getResources().getColor(R.color.darker_gray);
        this.f23439i = context.getResources().getDimension(c.g.D7);
        if (attributeSet != null) {
            TypedArray obtainStyledAttributes = getContext().obtainStyledAttributes(attributeSet, c.r.Xp);
            this.f23440j = obtainStyledAttributes.getColor(2, this.f23440j);
            this.f23441k = obtainStyledAttributes.getColor(0, this.f23441k);
            this.f23439i = obtainStyledAttributes.getDimension(4, this.f23439i);
            obtainStyledAttributes.recycle();
        }
        this.f23434d = new Paint(1);
        this.f23436f = new Paint(1);
        this.f23434d.setColor(this.f23441k);
        this.f23436f.setColor(this.f23440j);
        this.f23436f.setTextSize(this.f23439i);
    }

    @TargetApi(17)
    public boolean b() {
        return getContext().getResources().getConfiguration().getLayoutDirection() == 1;
    }

    @Override // android.view.View
    protected void onDraw(Canvas canvas) {
        float[] fArr;
        super.onDraw(canvas);
        if (TextUtils.isEmpty(this.f23435e)) {
            return;
        }
        canvas.drawColor(getResources().getColor(R.color.transparent));
        this.f23433c.set(0.0f, 0.0f, this.f23437g, this.f23438h);
        if (b()) {
            int i5 = this.f23431a;
            fArr = new float[]{i5, i5, i5, i5, i5, i5, 0.0f, 0.0f};
        } else {
            int i6 = this.f23431a;
            fArr = new float[]{i6, i6, i6, i6, 0.0f, 0.0f, i6, i6};
        }
        this.f23432b.addRoundRect(this.f23433c, fArr, Path.Direction.CW);
        canvas.drawPath(this.f23432b, this.f23434d);
        canvas.drawText(this.f23435e, this.f23442l, this.f23443m, this.f23436f);
    }

    @Override // android.view.View
    protected void onMeasure(int i5, int i6) {
        super.onMeasure(i5, i6);
        int width = getWidth();
        this.f23437g = width;
        this.f23438h = width;
        this.f23431a = (int) (width * 0.5d);
    }

    public void setText(String str) {
        this.f23435e = str;
        Rect rect = new Rect();
        Paint paint = this.f23436f;
        String str2 = this.f23435e;
        paint.getTextBounds(str2, 0, str2.length(), rect);
        this.f23442l = (int) ((this.f23437g - rect.width()) * 0.5d);
        this.f23443m = this.f23438h - rect.height();
        invalidate();
    }
}
