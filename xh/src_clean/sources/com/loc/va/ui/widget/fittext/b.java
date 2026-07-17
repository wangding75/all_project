package com.loc.va.ui.widget.fittext;

import android.annotation.TargetApi;
import android.text.Layout;
import android.text.SpannableStringBuilder;
import android.text.StaticLayout;
import android.text.TextPaint;
import android.text.TextUtils;
import android.widget.TextView;
import androidx.core.view.q;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
class b {
    

    /* renamed from: c, reason: collision with root package name */
    protected static final float f23264c = 0.001f;

    /* renamed from: d, reason: collision with root package name */
    private static final boolean f23265d = false;

    /* renamed from: e, reason: collision with root package name */
    public static final List<CharSequence> f23266e;

    /* renamed from: a, reason: collision with root package name */
    protected a f23267a;

    /* renamed from: b, reason: collision with root package name */
    protected volatile boolean f23268b = false;

    

    static {
        ArrayList arrayList = new ArrayList();
        f23266e = arrayList;
        arrayList.add(",");
        arrayList.add(".");
        arrayList.add(";");
        arrayList.add("'");
        arrayList.add("\"");
        arrayList.add(":");
        arrayList.add("?");
        arrayList.add("~");
        arrayList.add("!");
        arrayList.add("‘");
        arrayList.add("’");
        arrayList.add("”");
        arrayList.add("“");
        arrayList.add("；");
        arrayList.add("：");
        arrayList.add("，");
        arrayList.add("。");
        arrayList.add("？");
        arrayList.add("！");
        arrayList.add("(");
        arrayList.add(")");
        arrayList.add("[");
        arrayList.add("]");
        arrayList.add("@");
        arrayList.add("/");
        arrayList.add("#");
        arrayList.add("$");
        arrayList.add("%");
        arrayList.add("^");
        arrayList.add("&");
        arrayList.add("*");
        arrayList.add("<");
        arrayList.add(">");
        arrayList.add("+");
        arrayList.add("-");
        arrayList.add("·");
    }

    public b(a aVar) {
        this.f23267a = aVar;
    }

    @TargetApi(17)
    public static Layout.Alignment b(TextView textView) {
        switch (textView.getTextAlignment()) {
            case 1:
                int gravity = textView.getGravity() & q.f6928d;
                if (gravity != 1) {
                    return gravity == 3 ? Layout.Alignment.ALIGN_NORMAL : Layout.Alignment.ALIGN_NORMAL;
                }
                return Layout.Alignment.ALIGN_CENTER;
            case 2:
            case 5:
            default:
            case 3:
            case 6:
                return Layout.Alignment.ALIGN_OPPOSITE;
            case 4:
                return Layout.Alignment.ALIGN_CENTER;
        }
    }

    public static StaticLayout e(TextView textView, CharSequence charSequence, TextPaint textPaint) {
        StaticLayout staticLayout;
        if (textView instanceof FitTextView) {
            FitTextView fitTextView = (FitTextView) textView;
            staticLayout = new StaticLayout(charSequence, textPaint, g(textView), b(fitTextView), fitTextView.getLineSpacingMultiplierCompat(), fitTextView.getLineSpacingExtraCompat(), fitTextView.getIncludeFontPaddingCompat());
        } else {
            staticLayout = new StaticLayout(charSequence, textPaint, g(textView), b(textView), textView.getLineSpacingMultiplier(), textView.getLineSpacingExtra(), textView.getIncludeFontPadding());
        }
        if (i(textView)) {
            try {
                Field declaredField = StaticLayout.class.getDeclaredField("mMaximumVisibleLineCount");
                if (declaredField != null) {
                    declaredField.setAccessible(true);
                    declaredField.set(staticLayout, 1);
                }
            } catch (Exception e6) {
                e6.printStackTrace();
            }
        }
        return staticLayout;
    }

    public static int g(TextView textView) {
        return (textView.getMeasuredWidth() - textView.getCompoundPaddingLeft()) - textView.getCompoundPaddingRight();
    }

    public static boolean i(TextView textView) {
        if (textView == null) {
            return false;
        }
        return textView instanceof a ? ((a) textView).isSingleLine() : (textView.getInputType() & 131072) == 131072;
    }

    public float a(TextPaint textPaint, CharSequence charSequence, float f5, float f6) {
        float f7 = f5;
        float f8 = f6;
        if (TextUtils.isEmpty(charSequence)) {
            if (textPaint != null) {
                return textPaint.getTextSize();
            }
            a aVar = this.f23267a;
            if (aVar != null) {
                return aVar.getTextSize();
            }
        }
        TextPaint textPaint2 = new TextPaint(textPaint);
        while (Math.abs(f7 - f8) > f23264c) {
            textPaint2.setTextSize((f8 + f7) / 2.0f);
            if (h(c(charSequence, textPaint2), textPaint2)) {
                f8 = textPaint2.getTextSize();
            } else {
                f7 = textPaint2.getTextSize();
            }
        }
        return f8;
    }

    public CharSequence c(CharSequence charSequence, TextPaint textPaint) {
        int textWidth = this.f23267a.getTextWidth();
        boolean e6 = this.f23267a.e();
        if (textWidth <= 0 || e6) {
            return charSequence;
        }
        int length = charSequence.length();
        SpannableStringBuilder spannableStringBuilder = new SpannableStringBuilder();
        int i5 = 0;
        for (int i6 = 1; i6 <= length; i6++) {
            int i7 = i6 - 1;
            CharSequence subSequence = charSequence.subSequence(i7, i6);
            String $2 = "\n";
            if (!TextUtils.equals(subSequence, $2)) {
                float measureText = textPaint.measureText(charSequence, i5, i6);
                float f5 = textWidth;
                if (measureText > f5) {
                    spannableStringBuilder.append(charSequence, i5, i7);
                    if (i6 < length && !TextUtils.equals(charSequence.subSequence(i7, i6), $2)) {
                        spannableStringBuilder.append('\n');
                    }
                    i5 = i7;
                } else if (measureText == f5) {
                    spannableStringBuilder.append(charSequence, i5, i6);
                    if (i6 < length && !TextUtils.equals(charSequence.subSequence(i6, i6 + 1), $2)) {
                        spannableStringBuilder.append('\n');
                    }
                    i5 = i6;
                } else if (i6 != length) {
                }
            }
            spannableStringBuilder.append(charSequence, i5, i6);
            i5 = i6;
        }
        return spannableStringBuilder;
    }

    protected int d() {
        return (int) (this.f23267a.getTextHeight() / this.f23267a.getTextLineHeight());
    }

    public StaticLayout f(CharSequence charSequence, TextPaint textPaint) {
        return e(this.f23267a.getTextView(), charSequence, textPaint);
    }

    protected boolean h(CharSequence charSequence, TextPaint textPaint) {
        boolean isSingleLine = this.f23267a.isSingleLine();
        int maxLinesCompat = this.f23267a.getMaxLinesCompat();
        float lineSpacingExtraCompat = this.f23267a.getLineSpacingExtraCompat() * this.f23267a.getLineSpacingMultiplierCompat();
        int textHeight = this.f23267a.getTextHeight();
        if (!isSingleLine) {
            textHeight += Math.round(lineSpacingExtraCompat);
        }
        int max = isSingleLine ? 1 : Math.max(1, maxLinesCompat);
        StaticLayout f5 = f(charSequence, textPaint);
        return f5.getLineCount() <= max && f5.getHeight() <= textHeight;
    }
}
