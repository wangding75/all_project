package com.loc.va.ui.widget.fittext;

import android.R;
import android.annotation.TargetApi;
import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.text.Layout;
import android.text.TextPaint;
import android.text.TextUtils;
import android.util.AttributeSet;
import android.widget.TextView;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
class a extends TextView {
    

    /* renamed from: i, reason: collision with root package name */
    private static final int[] f23255i = {R.attr.includeFontPadding, R.attr.lineSpacingMultiplier, R.attr.lineSpacingExtra, R.attr.maxLines, R.attr.singleLine};

    /* renamed from: a, reason: collision with root package name */
    protected boolean f23256a;

    /* renamed from: b, reason: collision with root package name */
    protected boolean f23257b;

    /* renamed from: c, reason: collision with root package name */
    protected float f23258c;

    /* renamed from: d, reason: collision with root package name */
    protected float f23259d;

    /* renamed from: e, reason: collision with root package name */
    protected int f23260e;

    /* renamed from: f, reason: collision with root package name */
    protected boolean f23261f;

    /* renamed from: g, reason: collision with root package name */
    protected boolean f23262g;

    /* renamed from: h, reason: collision with root package name */
    protected boolean f23263h;

    

    public a(Context context) {
        this(context, null);
    }

    public a(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        this.f23256a = false;
        this.f23257b = true;
        this.f23258c = 1.0f;
        this.f23259d = 0.0f;
        this.f23260e = Integer.MAX_VALUE;
        this.f23261f = true;
        this.f23262g = false;
        this.f23263h = true;
        if (attributeSet != null) {
            TypedArray obtainStyledAttributes = context.obtainStyledAttributes(attributeSet, f23255i);
            this.f23256a = obtainStyledAttributes.getBoolean(R.attr.singleLine, this.f23256a);
            obtainStyledAttributes.recycle();
        }
    }

    public a(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet);
        this.f23256a = false;
        this.f23257b = true;
        this.f23258c = 1.0f;
        this.f23259d = 0.0f;
        this.f23260e = Integer.MAX_VALUE;
        this.f23261f = true;
        this.f23262g = false;
        this.f23263h = true;
    }

    protected int a(CharSequence charSequence) {
        int length = charSequence.length();
        int i5 = 0;
        int i6 = 0;
        while (i5 < length) {
            int i7 = i5 + 1;
            if (b(charSequence, i5, i7)) {
                i6++;
            }
            i5 = i7;
        }
        return i6;
    }

    protected boolean b(CharSequence charSequence, int i5, int i6) {
        if (i6 >= charSequence.length()) {
            return false;
        }
        CharSequence subSequence = charSequence.subSequence(i5, i6);
        return TextUtils.equals(subSequence, "\t") || TextUtils.equals(subSequence, " ") || b.f23266e.contains(subSequence);
    }

    public boolean c() {
        return getPaint().getTextSkewX() != 0.0f;
    }

    public boolean d() {
        return this.f23262g;
    }

    public boolean e() {
        return this.f23263h;
    }

    public boolean f() {
        return this.f23261f;
    }

    protected boolean g(CharSequence charSequence) {
        return TextUtils.equals(charSequence, " ");
    }

    @TargetApi(16)
    public boolean getIncludeFontPaddingCompat() {
        return getIncludeFontPadding();
    }

    @TargetApi(16)
    public float getLineSpacingExtraCompat() {
        return getLineSpacingExtra();
    }

    @TargetApi(16)
    public float getLineSpacingMultiplierCompat() {
        return getLineSpacingMultiplier();
    }

    @TargetApi(16)
    public int getMaxLinesCompat() {
        return getMaxLines();
    }

    public int getTextHeight() {
        return (getMeasuredHeight() - getCompoundPaddingTop()) - getCompoundPaddingBottom();
    }

    public float getTextLineHeight() {
        return getLineHeight();
    }

    public TextView getTextView() {
        return this;
    }

    public int getTextWidth() {
        return b.g(this);
    }

    @Override // android.widget.TextView
    public boolean isSingleLine() {
        return this.f23256a;
    }

    @Override // android.widget.TextView, android.view.View
    protected void onDraw(Canvas canvas) {
        Layout layout;
        int i5;
        int i6;
        if (!this.f23262g || this.f23256a) {
            super.onDraw(canvas);
            return;
        }
        TextPaint paint = getPaint();
        float textWidth = getTextWidth();
        if (c()) {
            textWidth -= getPaint().measureText("a");
        }
        float f5 = textWidth;
        CharSequence text = getText();
        Layout layout2 = getLayout();
        if (layout2 == null) {
            layout2 = b.e(this, getText(), getPaint());
        }
        Layout layout3 = layout2;
        int lineCount = layout3.getLineCount();
        int i7 = 0;
        while (i7 < lineCount) {
            int lineStart = layout3.getLineStart(i7);
            int lineEnd = layout3.getLineEnd(i7);
            float lineLeft = layout3.getLineLeft(i7);
            int i8 = i7 + 1;
            int topPadding = layout3.getTopPadding() + (getLineHeight() * i8);
            CharSequence subSequence = text.subSequence(lineStart, lineEnd);
            if (subSequence.length() == 0) {
                layout = layout3;
            } else {
                if (this.f23261f) {
                    CharSequence subSequence2 = subSequence.subSequence(subSequence.length() - 1, subSequence.length());
                    String $2 = " ";
                    if (TextUtils.equals(subSequence2, $2)) {
                        i6 = 0;
                        subSequence = subSequence.subSequence(0, subSequence.length() - 1);
                    } else {
                        i6 = 0;
                    }
                    layout = layout3;
                    i5 = 1;
                    if (TextUtils.equals(subSequence.subSequence(i6, 1), $2)) {
                        subSequence = subSequence.subSequence(1, subSequence.length() - 1);
                    }
                } else {
                    layout = layout3;
                    i5 = 1;
                    i6 = 0;
                }
                float measureText = getPaint().measureText(text, lineStart, lineEnd);
                if (i7 >= lineCount - 1 || !g(text.subSequence(lineEnd - 1, lineEnd))) {
                    i5 = i6;
                }
                if (i5 == 0 || f5 <= measureText) {
                    canvas.drawText(subSequence, 0, subSequence.length(), lineLeft, topPadding, paint);
                } else {
                    float a6 = (f5 - measureText) / a(subSequence);
                    int i9 = i6;
                    while (i9 < subSequence.length()) {
                        int i10 = i9 + 1;
                        float measureText2 = getPaint().measureText(subSequence, i9, i10);
                        canvas.drawText(subSequence, i9, i10, lineLeft, topPadding, getPaint());
                        lineLeft += measureText2;
                        if (b(subSequence, i10, i9 + 2)) {
                            lineLeft += a6 / 2.0f;
                        }
                        if (b(subSequence, i9, i10)) {
                            lineLeft += a6 / 2.0f;
                        }
                        i9 = i10;
                    }
                }
            }
            i7 = i8;
            layout3 = layout;
        }
    }

    public void setBoldText(boolean z5) {
        getPaint().setFakeBoldText(z5);
    }

    @Override // android.widget.TextView
    public void setIncludeFontPadding(boolean z5) {
        super.setIncludeFontPadding(z5);
        this.f23257b = z5;
    }

    public void setItalicText(boolean z5) {
        getPaint().setTextSkewX(z5 ? -0.25f : 0.0f);
    }

    public void setJustify(boolean z5) {
        this.f23262g = z5;
    }

    public void setKeepWord(boolean z5) {
        this.f23263h = z5;
    }

    public void setLineEndNoSpace(boolean z5) {
        this.f23261f = z5;
    }

    @Override // android.widget.TextView
    public void setLineSpacing(float f5, float f6) {
        super.setLineSpacing(f5, f6);
        this.f23259d = f5;
        this.f23258c = f6;
    }

    @Override // android.widget.TextView
    public void setMaxLines(int i5) {
        super.setMaxLines(i5);
        this.f23260e = i5;
    }

    @Override // android.widget.TextView
    public void setSingleLine(boolean z5) {
        super.setSingleLine(z5);
        this.f23256a = z5;
    }
}
