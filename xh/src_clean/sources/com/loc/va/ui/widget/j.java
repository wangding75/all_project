package com.loc.va.ui.widget;

import android.R;
import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.view.View;
import android.view.ViewAnimationUtils;
import android.view.ViewGroup;
import android.widget.ImageView;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class j {

    /* renamed from: a, reason: collision with root package name */
    public static final long f23304a = 618;

    /* renamed from: b, reason: collision with root package name */
    public static final int f23305b = 0;

    /* renamed from: c, reason: collision with root package name */
    private static Long f23306c;

    /* renamed from: d, reason: collision with root package name */
    private static Long f23307d;

    /* renamed from: e, reason: collision with root package name */
    private static Integer f23308e;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    @SuppressLint({"NewApi"})
    /* loaded from: D:\github\xh\blackdex_out\classes10.dex */
    public static class a {

        /* renamed from: a, reason: collision with root package name */
        private Activity f23309a;

        /* renamed from: b, reason: collision with root package name */
        private View f23310b;

        /* renamed from: e, reason: collision with root package name */
        private Long f23313e;

        /* renamed from: f, reason: collision with root package name */
        private b f23314f;

        /* renamed from: c, reason: collision with root package name */
        private float f23311c = 0.0f;

        /* renamed from: d, reason: collision with root package name */
        private int f23312d = j.e();

        /* renamed from: g, reason: collision with root package name */
        private int f23315g = R.anim.fade_in;

        /* renamed from: h, reason: collision with root package name */
        private int f23316h = R.anim.fade_out;

        /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
        /* renamed from: com.loc.va.ui.widget.j$a$a, reason: collision with other inner class name */
        class C0215a extends AnimatorListenerAdapter {

            /* renamed from: a, reason: collision with root package name */
            final /* synthetic */ ImageView f23317a;

            /* renamed from: b, reason: collision with root package name */
            final /* synthetic */ int f23318b;

            /* renamed from: c, reason: collision with root package name */
            final /* synthetic */ int f23319c;

            /* renamed from: d, reason: collision with root package name */
            final /* synthetic */ int f23320d;

            /* renamed from: e, reason: collision with root package name */
            final /* synthetic */ long f23321e;

            /* renamed from: f, reason: collision with root package name */
            final /* synthetic */ ViewGroup f23322f;

            /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
            /* renamed from: com.loc.va.ui.widget.j$a$a$a, reason: collision with other inner class name */
            class RunnableC0216a implements Runnable {

                /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
                /* renamed from: com.loc.va.ui.widget.j$a$a$a$a, reason: collision with other inner class name */
                class C0217a extends AnimatorListenerAdapter {
                    C0217a() {
                    }

                    @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
                    public void onAnimationEnd(Animator animator) {
                        super.onAnimationEnd(animator);
                        try {
                            C0215a c0215a = C0215a.this;
                            c0215a.f23322f.removeView(c0215a.f23317a);
                        } catch (Exception e6) {
                            e6.printStackTrace();
                        }
                    }
                }

                RunnableC0216a() {
                }

                @Override // java.lang.Runnable
                public void run() {
                    if (a.this.f23309a.isFinishing()) {
                        return;
                    }
                    try {
                        C0215a c0215a = C0215a.this;
                        Animator createCircularReveal = ViewAnimationUtils.createCircularReveal(c0215a.f23317a, c0215a.f23318b, c0215a.f23319c, c0215a.f23320d, a.this.f23311c);
                        createCircularReveal.setDuration(C0215a.this.f23321e);
                        createCircularReveal.addListener(new C0217a());
                        createCircularReveal.start();
                    } catch (Exception e6) {
                        e6.printStackTrace();
                        try {
                            C0215a c0215a2 = C0215a.this;
                            c0215a2.f23322f.removeView(c0215a2.f23317a);
                        } catch (Exception e7) {
                            e7.printStackTrace();
                        }
                    }
                }
            }

            C0215a(ImageView imageView, int i5, int i6, int i7, long j5, ViewGroup viewGroup) {
                this.f23317a = imageView;
                this.f23318b = i5;
                this.f23319c = i6;
                this.f23320d = i7;
                this.f23321e = j5;
                this.f23322f = viewGroup;
            }

            @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
            public void onAnimationEnd(Animator animator) {
                super.onAnimationEnd(animator);
                a.this.h();
                a.this.f23309a.overridePendingTransition(a.this.f23315g, a.this.f23316h);
                a.this.f23310b.postDelayed(new RunnableC0216a(), 1000L);
            }
        }

        public a(Activity activity, View view) {
            this.f23309a = activity;
            this.f23310b = view;
        }

        /* JADX INFO: Access modifiers changed from: private */
        public void h() {
            this.f23314f.onAnimationEnd();
        }

        public a g(int i5) {
            this.f23312d = i5;
            return this;
        }

        public a i(long j5) {
            this.f23313e = Long.valueOf(j5);
            return this;
        }

        public void j(b bVar) {
            this.f23314f = bVar;
            int[] iArr = new int[2];
            this.f23310b.getLocationInWindow(iArr);
            int width = iArr[0] + (this.f23310b.getWidth() / 2);
            int height = iArr[1] + (this.f23310b.getHeight() / 2);
            ImageView imageView = new ImageView(this.f23309a);
            imageView.setScaleType(ImageView.ScaleType.CENTER_CROP);
            imageView.setImageResource(this.f23312d);
            ViewGroup viewGroup = (ViewGroup) this.f23309a.getWindow().getDecorView();
            int width2 = viewGroup.getWidth();
            int height2 = viewGroup.getHeight();
            viewGroup.addView(imageView, width2, height2);
            int max = Math.max(width, width2 - width);
            int max2 = Math.max(height, height2 - height);
            int sqrt = ((int) Math.sqrt((max * max) + (max2 * max2))) + 1;
            try {
                Animator createCircularReveal = ViewAnimationUtils.createCircularReveal(imageView, width, height, this.f23311c, sqrt);
                int sqrt2 = ((int) Math.sqrt((width2 * width2) + (height2 * height2))) + 1;
                if (this.f23313e == null) {
                    this.f23313e = Long.valueOf((long) (j.f() * Math.sqrt((sqrt * 1.0d) / sqrt2)));
                }
                long longValue = this.f23313e.longValue();
                createCircularReveal.setDuration((long) (longValue * 0.9d));
                createCircularReveal.addListener(new C0215a(imageView, width, height, sqrt, longValue, viewGroup));
                createCircularReveal.start();
            } catch (Exception e6) {
                e6.printStackTrace();
                h();
            }
        }

        public a k(int i5, int i6) {
            this.f23315g = i5;
            this.f23316h = i6;
            return this;
        }

        public a l(float f5) {
            this.f23311c = f5;
            return this;
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    public interface b {
        void onAnimationEnd();
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    @SuppressLint({"NewApi"})
    public static class c {

        /* renamed from: a, reason: collision with root package name */
        private View f23326a;

        /* renamed from: b, reason: collision with root package name */
        private View f23327b;

        /* renamed from: c, reason: collision with root package name */
        private Float f23328c;

        /* renamed from: d, reason: collision with root package name */
        private Float f23329d;

        /* renamed from: e, reason: collision with root package name */
        private long f23330e = j.g();

        /* renamed from: f, reason: collision with root package name */
        private boolean f23331f;

        /* renamed from: g, reason: collision with root package name */
        private b f23332g;

        /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
        class a extends AnimatorListenerAdapter {
            a() {
            }

            @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
            public void onAnimationEnd(Animator animator) {
                super.onAnimationEnd(animator);
                c.this.b();
            }
        }

        public c(View view, boolean z5) {
            this.f23326a = view;
            this.f23331f = z5;
            Float valueOf = Float.valueOf(0.0f);
            if (z5) {
                this.f23328c = valueOf;
            } else {
                this.f23329d = valueOf;
            }
        }

        /* JADX INFO: Access modifiers changed from: private */
        public void b() {
            View view;
            int i5;
            if (this.f23331f) {
                view = this.f23326a;
                i5 = 0;
            } else {
                view = this.f23326a;
                i5 = 4;
            }
            view.setVisibility(i5);
            b bVar = this.f23332g;
            if (bVar != null) {
                bVar.onAnimationEnd();
            }
        }

        public c c(long j5) {
            this.f23330e = j5;
            return this;
        }

        public c d(float f5) {
            this.f23329d = Float.valueOf(f5);
            return this;
        }

        public void e() {
            f(null);
        }

        public void f(b bVar) {
            int left;
            int top2;
            int width;
            int height;
            this.f23332g = bVar;
            View view = this.f23327b;
            if (view != null) {
                int[] iArr = new int[2];
                view.getLocationInWindow(iArr);
                int width2 = iArr[0] + (this.f23327b.getWidth() / 2);
                int height2 = iArr[1] + (this.f23327b.getHeight() / 2);
                int[] iArr2 = new int[2];
                this.f23326a.getLocationInWindow(iArr2);
                int i5 = iArr2[0];
                int i6 = iArr2[1];
                int min = Math.min(Math.max(i5, width2), this.f23326a.getWidth() + i5);
                int min2 = Math.min(Math.max(i6, height2), this.f23326a.getHeight() + i6);
                int width3 = this.f23326a.getWidth();
                int height3 = this.f23326a.getHeight();
                left = min - i5;
                top2 = min2 - i6;
                width = Math.max(left, width3 - left);
                height = Math.max(top2, height3 - top2);
            } else {
                left = (this.f23326a.getLeft() + this.f23326a.getRight()) / 2;
                top2 = (this.f23326a.getTop() + this.f23326a.getBottom()) / 2;
                width = this.f23326a.getWidth();
                height = this.f23326a.getHeight();
            }
            int sqrt = ((int) Math.sqrt((width * width) + (height * height))) + 1;
            boolean z5 = this.f23331f;
            if (z5 && this.f23329d == null) {
                this.f23329d = Float.valueOf(sqrt + 0.0f);
            } else if (!z5 && this.f23328c == null) {
                this.f23328c = Float.valueOf(sqrt + 0.0f);
            }
            try {
                Animator createCircularReveal = ViewAnimationUtils.createCircularReveal(this.f23326a, left, top2, this.f23328c.floatValue(), this.f23329d.floatValue());
                this.f23326a.setVisibility(0);
                createCircularReveal.setDuration(this.f23330e);
                createCircularReveal.addListener(new a());
                createCircularReveal.start();
            } catch (Exception e6) {
                e6.printStackTrace();
                b();
            }
        }

        @Deprecated
        public c g(b bVar) {
            this.f23332g = bVar;
            return this;
        }

        public c h(float f5) {
            this.f23328c = Float.valueOf(f5);
            return this;
        }

        public c i(View view) {
            this.f23327b = view;
            return this;
        }
    }

    public static a d(Activity activity, View view) {
        return new a(activity, view);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static int e() {
        Integer num = f23308e;
        return num != null ? num.intValue() : R.color.white;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static long f() {
        Long l5 = f23307d;
        if (l5 != null) {
            return l5.longValue();
        }
        return 618L;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static long g() {
        Long l5 = f23306c;
        if (l5 != null) {
            return l5.longValue();
        }
        return 618L;
    }

    public static c h(View view) {
        return new c(view, false);
    }

    public static void i(long j5, long j6, int i5) {
        f23306c = Long.valueOf(j5);
        f23307d = Long.valueOf(j6);
        f23308e = Integer.valueOf(i5);
    }

    public static c j(View view) {
        return new c(view, true);
    }
}
