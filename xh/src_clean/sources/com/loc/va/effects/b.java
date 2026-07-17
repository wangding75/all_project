package com.loc.va.effects;

import android.R;
import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Rect;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.util.AttributeSet;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import com.loc.va.App;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.Random;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class b extends View {

    /* renamed from: c, reason: collision with root package name */
    private static final Canvas f22550c = new Canvas();

    /* renamed from: a, reason: collision with root package name */
    private List<com.loc.va.effects.a> f22551a;

    /* renamed from: b, reason: collision with root package name */
    private int[] f22552b;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class a extends AnimatorListenerAdapter {
        a() {
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            b.this.f22551a.remove(animator);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* renamed from: com.loc.va.effects.b$b, reason: collision with other inner class name */
    class C0210b implements ValueAnimator.AnimatorUpdateListener {

        /* renamed from: a, reason: collision with root package name */
        Random f22554a = new Random();

        /* renamed from: b, reason: collision with root package name */
        final /* synthetic */ View f22555b;

        C0210b(View view) {
            this.f22555b = view;
        }

        @Override // android.animation.ValueAnimator.AnimatorUpdateListener
        public void onAnimationUpdate(ValueAnimator valueAnimator) {
            this.f22555b.setTranslationX((this.f22554a.nextFloat() - 0.5f) * this.f22555b.getWidth() * 0.05f);
            this.f22555b.setTranslationY((this.f22554a.nextFloat() - 0.5f) * this.f22555b.getHeight() * 0.05f);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class c extends AnimatorListenerAdapter {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ d f22557a;

        /* renamed from: b, reason: collision with root package name */
        final /* synthetic */ View f22558b;

        c(d dVar, View view) {
            this.f22557a = dVar;
            this.f22558b = view;
        }

        @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            d dVar = this.f22557a;
            if (dVar != null) {
                dVar.a(this.f22558b);
            }
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    public interface d {
        void a(View view);
    }

    public b(Context context) {
        super(context);
        this.f22551a = new ArrayList();
        this.f22552b = new int[2];
        k();
    }

    public b(Context context, AttributeSet attributeSet) {
        super(context, attributeSet);
        this.f22551a = new ArrayList();
        this.f22552b = new int[2];
        k();
    }

    public b(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.f22551a = new ArrayList();
        this.f22552b = new int[2];
        k();
    }

    public static b b(Activity activity) {
        ViewGroup viewGroup = (ViewGroup) activity.findViewById(R.id.content);
        b bVar = new b(activity);
        viewGroup.addView(bVar, new ViewGroup.LayoutParams(-1, -1));
        return bVar;
    }

    public static b c(ViewGroup viewGroup, Activity activity) {
        b bVar = new b(activity);
        viewGroup.addView(bVar, new ViewGroup.LayoutParams(-1, -1));
        return bVar;
    }

    public static Bitmap e(View view) {
        Drawable drawable;
        if ((view instanceof ImageView) && (drawable = ((ImageView) view).getDrawable()) != null && (drawable instanceof BitmapDrawable)) {
            return ((BitmapDrawable) drawable).getBitmap();
        }
        view.clearFocus();
        Bitmap f5 = f(view.getWidth(), view.getHeight(), Bitmap.Config.ARGB_8888, 1);
        if (f5 != null) {
            Canvas canvas = f22550c;
            synchronized (canvas) {
                canvas.setBitmap(f5);
                view.draw(canvas);
                canvas.setBitmap(null);
            }
        }
        return f5;
    }

    public static Bitmap f(int i5, int i6, Bitmap.Config config, int i7) {
        try {
            return Bitmap.createBitmap(i5, i6, config);
        } catch (OutOfMemoryError e6) {
            e6.printStackTrace();
            if (i7 <= 0) {
                return null;
            }
            System.gc();
            return f(i5, i6, config, i7 - 1);
        }
    }

    private void k() {
        Arrays.fill(this.f22552b, com.loc.va.abs.ui.c.b(App.a(), 32));
    }

    public void d() {
        this.f22551a.clear();
        invalidate();
    }

    public void g(int i5, int i6) {
        int[] iArr = this.f22552b;
        iArr[0] = i5;
        iArr[1] = i6;
    }

    public void h(Bitmap bitmap, Rect rect, long j5, long j6) {
        com.loc.va.effects.a aVar = new com.loc.va.effects.a(this, bitmap, rect);
        aVar.addListener(new a());
        aVar.setStartDelay(j5);
        aVar.setDuration(j6);
        this.f22551a.add(aVar);
        aVar.start();
    }

    public void i(View view) {
        j(view, null);
    }

    public void j(View view, d dVar) {
        Rect rect = new Rect();
        view.getGlobalVisibleRect(rect);
        int[] iArr = new int[2];
        getLocationOnScreen(iArr);
        rect.offset(-iArr[0], -iArr[1]);
        int[] iArr2 = this.f22552b;
        rect.inset(-iArr2[0], -iArr2[1]);
        ValueAnimator duration = ValueAnimator.ofFloat(0.0f, 1.0f).setDuration(150L);
        duration.addUpdateListener(new C0210b(view));
        duration.addListener(new c(dVar, view));
        duration.start();
        long j5 = 100;
        view.animate().setDuration(150L).setStartDelay(j5).scaleX(0.0f).scaleY(0.0f).alpha(0.0f).start();
        h(e(view), rect, j5, com.loc.va.effects.a.f22530k);
    }

    @Override // android.view.View
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        Iterator<com.loc.va.effects.a> iterator2 = this.f22551a.iterator2();
        while (iterator2.hasNext()) {
            iterator2.next().b(canvas);
        }
    }
}
