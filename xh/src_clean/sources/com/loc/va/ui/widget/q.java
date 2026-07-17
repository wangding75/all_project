package com.loc.va.ui.widget;

import android.animation.Animator;
import android.animation.ObjectAnimator;
import android.view.View;
import com.loc.va.ui.widget.s;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class q {
    

    /* renamed from: g, reason: collision with root package name */
    public static final int f23401g = 0;

    /* renamed from: h, reason: collision with root package name */
    public static final int f23402h = 1;

    /* renamed from: i, reason: collision with root package name */
    private static final int f23403i = -1;

    /* renamed from: j, reason: collision with root package name */
    private static final long f23404j = 1000;

    /* renamed from: k, reason: collision with root package name */
    private static final long f23405k = 0;

    /* renamed from: l, reason: collision with root package name */
    private static final int f23406l = 0;

    /* renamed from: a, reason: collision with root package name */
    private int f23407a = -1;

    /* renamed from: b, reason: collision with root package name */
    private long f23408b = 1000;

    /* renamed from: c, reason: collision with root package name */
    private long f23409c = 0;

    /* renamed from: d, reason: collision with root package name */
    private int f23410d = 0;

    /* renamed from: e, reason: collision with root package name */
    private Animator.AnimatorListener f23411e;

    /* renamed from: f, reason: collision with root package name */
    private ObjectAnimator f23412f;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a implements Runnable {
        

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ View f23413a;

        /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
        /* renamed from: com.loc.va.ui.widget.q$a$a, reason: collision with other inner class name */
        class C0218a implements Animator.AnimatorListener {
            C0218a() {
            }

            @Override // android.animation.Animator.AnimatorListener
            public void onAnimationCancel(Animator animator) {
            }

            @Override // android.animation.Animator.AnimatorListener
            public void onAnimationEnd(Animator animator) {
                ((r) a.this.f23413a).setShimmering(false);
                a.this.f23413a.postInvalidateOnAnimation();
                q.this.f23412f = null;
            }

            @Override // android.animation.Animator.AnimatorListener
            public void onAnimationRepeat(Animator animator) {
            }

            @Override // android.animation.Animator.AnimatorListener
            public void onAnimationStart(Animator animator) {
            }
        }

        

        a(View view) {
            this.f23413a = view;
        }

        @Override // java.lang.Runnable
        public void run() {
            ((r) this.f23413a).setShimmering(true);
            float width = this.f23413a.getWidth();
            float f5 = 0.0f;
            if (q.this.f23410d == 1) {
                f5 = this.f23413a.getWidth();
                width = 0.0f;
            }
            q.this.f23412f = ObjectAnimator.ofFloat(this.f23413a, "gradientX", f5, width);
            q.this.f23412f.setRepeatCount(q.this.f23407a);
            q.this.f23412f.setDuration(q.this.f23408b);
            q.this.f23412f.setStartDelay(q.this.f23409c);
            q.this.f23412f.addListener(new C0218a());
            if (q.this.f23411e != null) {
                q.this.f23412f.addListener(q.this.f23411e);
            }
            q.this.f23412f.start();
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class b implements s.a {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ Runnable f23416a;

        b(Runnable runnable) {
            this.f23416a = runnable;
        }

        @Override // com.loc.va.ui.widget.s.a
        public void a(View view) {
            this.f23416a.run();
        }
    }

    

    public void h() {
        ObjectAnimator objectAnimator = this.f23412f;
        if (objectAnimator != null) {
            objectAnimator.cancel();
        }
    }

    public Animator.AnimatorListener i() {
        return this.f23411e;
    }

    public int j() {
        return this.f23410d;
    }

    public long k() {
        return this.f23408b;
    }

    public int l() {
        return this.f23407a;
    }

    public long m() {
        return this.f23409c;
    }

    public boolean n() {
        ObjectAnimator objectAnimator = this.f23412f;
        return objectAnimator != null && objectAnimator.isRunning();
    }

    public q o(Animator.AnimatorListener animatorListener) {
        this.f23411e = animatorListener;
        return this;
    }

    public q p(int i5) {
        if (i5 != 0 && i5 != 1) {
            throw new IllegalArgumentException("The animation direction must be either ANIMATION_DIRECTION_LTR or ANIMATION_DIRECTION_RTL");
        }
        this.f23410d = i5;
        return this;
    }

    public q q(long j5) {
        this.f23408b = j5;
        return this;
    }

    public q r(int i5) {
        this.f23407a = i5;
        return this;
    }

    public q s(long j5) {
        this.f23409c = j5;
        return this;
    }

    public <V extends View & r> void t(V v5) {
        if (n()) {
            return;
        }
        a aVar = new a(v5);
        V v6 = v5;
        if (v6.c()) {
            aVar.run();
        } else {
            v6.setAnimationSetupCallback(new b(aVar));
        }
    }
}
