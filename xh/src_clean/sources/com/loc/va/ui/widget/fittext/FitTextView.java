package com.loc.va.ui.widget.fittext;

import android.annotation.TargetApi;
import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.text.TextUtils;
import android.util.AttributeSet;
import android.view.View;
import android.widget.TextView;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class FitTextView extends a {

    /* renamed from: j, reason: collision with root package name */
    private boolean f23247j;

    /* renamed from: k, reason: collision with root package name */
    private boolean f23248k;

    /* renamed from: l, reason: collision with root package name */
    protected float f23249l;

    /* renamed from: m, reason: collision with root package name */
    private float f23250m;

    /* renamed from: n, reason: collision with root package name */
    private float f23251n;

    /* renamed from: o, reason: collision with root package name */
    protected CharSequence f23252o;

    /* renamed from: p, reason: collision with root package name */
    protected volatile boolean f23253p;

    /* renamed from: q, reason: collision with root package name */
    protected b f23254q;

    public FitTextView(Context context) {
        this(context, null);
    }

    public FitTextView(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public FitTextView(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f23247j = false;
        this.f23248k = true;
        this.f23249l = 0.0f;
        this.f23253p = false;
        float textSize = getTextSize();
        this.f23249l = textSize;
        if (attributeSet == null) {
            this.f23250m = textSize;
            this.f23251n = textSize;
        } else {
            TypedArray obtainStyledAttributes = context.obtainStyledAttributes(attributeSet, new int[]{c.d.Z6, c.d.a7});
            this.f23251n = obtainStyledAttributes.getDimension(0, this.f23249l * 2.0f);
            this.f23250m = obtainStyledAttributes.getDimension(1, this.f23249l / 2.0f);
            obtainStyledAttributes.recycle();
        }
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ boolean c() {
        return super.c();
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ boolean d() {
        return super.d();
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ boolean e() {
        return super.e();
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ boolean f() {
        return super.f();
    }

    protected b getFitTextHelper() {
        if (this.f23254q == null) {
            this.f23254q = new b(this);
        }
        return this.f23254q;
    }

    @Override // com.loc.va.ui.widget.fittext.a
    @TargetApi(16)
    public /* bridge */ /* synthetic */ boolean getIncludeFontPaddingCompat() {
        return super.getIncludeFontPaddingCompat();
    }

    @Override // com.loc.va.ui.widget.fittext.a
    @TargetApi(16)
    public /* bridge */ /* synthetic */ float getLineSpacingExtraCompat() {
        return super.getLineSpacingExtraCompat();
    }

    @Override // com.loc.va.ui.widget.fittext.a
    @TargetApi(16)
    public /* bridge */ /* synthetic */ float getLineSpacingMultiplierCompat() {
        return super.getLineSpacingMultiplierCompat();
    }

    @Override // com.loc.va.ui.widget.fittext.a
    @TargetApi(16)
    public /* bridge */ /* synthetic */ int getMaxLinesCompat() {
        return super.getMaxLinesCompat();
    }

    public float getMaxTextSize() {
        return this.f23251n;
    }

    public float getMinTextSize() {
        return this.f23250m;
    }

    public CharSequence getOriginalText() {
        return this.f23252o;
    }

    public float getOriginalTextSize() {
        return this.f23249l;
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ int getTextHeight() {
        return super.getTextHeight();
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ float getTextLineHeight() {
        return super.getTextLineHeight();
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ TextView getTextView() {
        return super.getTextView();
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ int getTextWidth() {
        return super.getTextWidth();
    }

    protected void h(CharSequence charSequence) {
        if (!this.f23248k || !this.f23247j || this.f23253p || this.f23256a || TextUtils.isEmpty(charSequence)) {
            return;
        }
        this.f23253p = true;
        super.setTextSize(0, getFitTextHelper().a(getPaint(), charSequence, this.f23251n, this.f23250m));
        super.setText(getFitTextHelper().c(charSequence, getPaint()));
        this.f23253p = false;
    }

    public boolean i() {
        return this.f23248k;
    }

    @Override // com.loc.va.ui.widget.fittext.a, android.widget.TextView
    public /* bridge */ /* synthetic */ boolean isSingleLine() {
        return super.isSingleLine();
    }

    @Override // com.loc.va.ui.widget.fittext.a, android.widget.TextView, android.view.View
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
    }

    @Override // android.widget.TextView, android.view.View
    protected void onMeasure(int i5, int i6) {
        super.onMeasure(i5, i6);
        int mode = View.MeasureSpec.getMode(i5);
        int mode2 = View.MeasureSpec.getMode(i6);
        if (mode == 0 && mode2 == 0) {
            super.setTextSize(0, this.f23249l);
            this.f23247j = false;
        } else {
            this.f23247j = true;
            h(getOriginalText());
        }
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ void setBoldText(boolean z5) {
        super.setBoldText(z5);
    }

    @Override // com.loc.va.ui.widget.fittext.a, android.widget.TextView
    public /* bridge */ /* synthetic */ void setIncludeFontPadding(boolean z5) {
        super.setIncludeFontPadding(z5);
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ void setItalicText(boolean z5) {
        super.setItalicText(z5);
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ void setJustify(boolean z5) {
        super.setJustify(z5);
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ void setKeepWord(boolean z5) {
        super.setKeepWord(z5);
    }

    @Override // com.loc.va.ui.widget.fittext.a
    public /* bridge */ /* synthetic */ void setLineEndNoSpace(boolean z5) {
        super.setLineEndNoSpace(z5);
    }

    @Override // com.loc.va.ui.widget.fittext.a, android.widget.TextView
    public /* bridge */ /* synthetic */ void setLineSpacing(float f5, float f6) {
        super.setLineSpacing(f5, f6);
    }

    @Override // com.loc.va.ui.widget.fittext.a, android.widget.TextView
    public /* bridge */ /* synthetic */ void setMaxLines(int i5) {
        super.setMaxLines(i5);
    }

    public void setMaxTextSize(float f5) {
        this.f23251n = f5;
    }

    public void setMinTextSize(float f5) {
        this.f23250m = f5;
    }

    public void setNeedFit(boolean z5) {
        this.f23248k = z5;
    }

    @Override // com.loc.va.ui.widget.fittext.a, android.widget.TextView
    public /* bridge */ /* synthetic */ void setSingleLine(boolean z5) {
        super.setSingleLine(z5);
    }

    @Override // android.widget.TextView
    public void setText(CharSequence charSequence, TextView.BufferType bufferType) {
        this.f23252o = charSequence;
        super.setText(charSequence, bufferType);
        h(charSequence);
    }

    @Override // android.widget.TextView
    public void setTextSize(int i5, float f5) {
        super.setTextSize(i5, f5);
        this.f23249l = getTextSize();
    }
}
