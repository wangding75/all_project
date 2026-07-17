package com.loc.va.effects;

import android.animation.ValueAnimator;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.view.View;
import android.view.animation.AccelerateInterpolator;
import android.view.animation.Interpolator;
import com.loc.va.App;
import com.loc.va.abs.ui.c;
import java.util.Random;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class a extends ValueAnimator {

    /* renamed from: f, reason: collision with root package name */
    private static final float f22525f = 1.4f;

    /* renamed from: a, reason: collision with root package name */
    private Paint f22531a = new Paint();

    /* renamed from: b, reason: collision with root package name */
    private b[] f22532b = new b[225];

    /* renamed from: c, reason: collision with root package name */
    private Rect f22533c;

    /* renamed from: d, reason: collision with root package name */
    private View f22534d;

    /* renamed from: e, reason: collision with root package name */
    private static final Interpolator f22524e = new AccelerateInterpolator(0.6f);

    /* renamed from: g, reason: collision with root package name */
    private static final float f22526g = c.b(App.a(), 5);

    /* renamed from: h, reason: collision with root package name */
    private static final float f22527h = c.b(App.a(), 20);

    /* renamed from: i, reason: collision with root package name */
    private static final float f22528i = c.b(App.a(), 2);

    /* renamed from: j, reason: collision with root package name */
    private static final float f22529j = c.b(App.a(), 1);

    /* renamed from: k, reason: collision with root package name */
    static long f22530k = 1104;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* renamed from: com.loc.va.effects.a$a, reason: collision with other inner class name */
    static /* synthetic */ class C0209a {
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    private class b {

        /* renamed from: a, reason: collision with root package name */
        float f22535a;

        /* renamed from: b, reason: collision with root package name */
        int f22536b;

        /* renamed from: c, reason: collision with root package name */
        float f22537c;

        /* renamed from: d, reason: collision with root package name */
        float f22538d;

        /* renamed from: e, reason: collision with root package name */
        float f22539e;

        /* renamed from: f, reason: collision with root package name */
        float f22540f;

        /* renamed from: g, reason: collision with root package name */
        float f22541g;

        /* renamed from: h, reason: collision with root package name */
        float f22542h;

        /* renamed from: i, reason: collision with root package name */
        float f22543i;

        /* renamed from: j, reason: collision with root package name */
        float f22544j;

        /* renamed from: k, reason: collision with root package name */
        float f22545k;

        /* renamed from: l, reason: collision with root package name */
        float f22546l;

        /* renamed from: m, reason: collision with root package name */
        float f22547m;

        /* renamed from: n, reason: collision with root package name */
        float f22548n;

        private b() {
        }

        /* synthetic */ b(a aVar, C0209a c0209a) {
            this();
        }

        public void a(float f5) {
            float f6 = f5 / a.f22525f;
            float f7 = this.f22547m;
            if (f6 >= f7) {
                float f8 = this.f22548n;
                if (f6 <= 1.0f - f8) {
                    float f9 = (f6 - f7) / ((1.0f - f7) - f8);
                    float f10 = a.f22525f * f9;
                    this.f22535a = 1.0f - (f9 >= 0.7f ? (f9 - 0.7f) / 0.3f : 0.0f);
                    float f11 = this.f22544j * f10;
                    this.f22537c = this.f22540f + f11;
                    this.f22538d = ((float) (this.f22541g - (this.f22546l * Math.pow(f11, 2.0d)))) - (f11 * this.f22545k);
                    this.f22539e = a.f22528i + ((this.f22542h - a.f22528i) * f10);
                    return;
                }
            }
            this.f22535a = 0.0f;
        }
    }

    public a(View view, Bitmap bitmap, Rect rect) {
        this.f22533c = new Rect(rect);
        Random random = new Random(System.currentTimeMillis());
        int width = bitmap.getWidth() / 17;
        int height = bitmap.getHeight() / 17;
        for (int i5 = 0; i5 < 15; i5++) {
            int i6 = 0;
            while (i6 < 15) {
                int i7 = (i5 * 15) + i6;
                i6++;
                this.f22532b[i7] = c(bitmap.getPixel(i6 * width, (i5 + 1) * height), random);
            }
        }
        this.f22534d = view;
        setFloatValues(0.0f, f22525f);
        setInterpolator(f22524e);
        setDuration(f22530k);
    }

    private b c(int i5, Random random) {
        b bVar = new b(this, null);
        bVar.f22536b = i5;
        float f5 = f22528i;
        bVar.f22539e = f5;
        if (random.nextFloat() < 0.2f) {
            bVar.f22542h = f5 + ((f22526g - f5) * random.nextFloat());
        } else {
            float f6 = f22529j;
            bVar.f22542h = f6 + ((f5 - f6) * random.nextFloat());
        }
        float nextFloat = random.nextFloat();
        float height = this.f22533c.height() * ((random.nextFloat() * 0.18f) + 0.2f);
        bVar.f22543i = height;
        if (nextFloat >= 0.2f) {
            height += 0.2f * height * random.nextFloat();
        }
        bVar.f22543i = height;
        float height2 = this.f22533c.height() * (random.nextFloat() - 0.5f) * 1.8f;
        bVar.f22544j = height2;
        if (nextFloat >= 0.2f) {
            height2 *= nextFloat < 0.8f ? 0.6f : 0.3f;
        }
        bVar.f22544j = height2;
        float f7 = (bVar.f22543i * 4.0f) / height2;
        bVar.f22545k = f7;
        bVar.f22546l = (-f7) / height2;
        float centerX = this.f22533c.centerX();
        float f8 = f22527h;
        float nextFloat2 = centerX + ((random.nextFloat() - 0.5f) * f8);
        bVar.f22540f = nextFloat2;
        bVar.f22537c = nextFloat2;
        float centerY = this.f22533c.centerY() + (f8 * (random.nextFloat() - 0.5f));
        bVar.f22541g = centerY;
        bVar.f22538d = centerY;
        bVar.f22547m = random.nextFloat() * 0.14f;
        bVar.f22548n = random.nextFloat() * 0.4f;
        bVar.f22535a = 1.0f;
        return bVar;
    }

    public boolean b(Canvas canvas) {
        if (!isStarted()) {
            return false;
        }
        for (b bVar : this.f22532b) {
            bVar.a(((Float) getAnimatedValue()).floatValue());
            if (bVar.f22535a > 0.0f) {
                this.f22531a.setColor(bVar.f22536b);
                this.f22531a.setAlpha((int) (Color.alpha(bVar.f22536b) * bVar.f22535a));
                canvas.drawCircle(bVar.f22537c, bVar.f22538d, bVar.f22539e, this.f22531a);
            }
        }
        this.f22534d.invalidate();
        return true;
    }

    @Override // android.animation.ValueAnimator, android.animation.Animator
    public void start() {
        super.start();
        this.f22534d.invalidate(this.f22533c);
    }
}
