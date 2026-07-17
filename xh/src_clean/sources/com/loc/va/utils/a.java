package com.loc.va.utils;

import android.animation.Animator;
import android.view.View;
import android.view.animation.AlphaAnimation;
import android.view.animation.Animation;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class a {

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* renamed from: com.loc.va.utils.a$a, reason: collision with other inner class name */
    class AnimationAnimationListenerC0219a implements Animation.AnimationListener {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ View f23470a;

        AnimationAnimationListenerC0219a(View view) {
            this.f23470a = view;
        }

        @Override // android.view.animation.Animation.AnimationListener
        public void onAnimationEnd(Animation animation) {
            this.f23470a.setVisibility(8);
        }

        @Override // android.view.animation.Animation.AnimationListener
        public void onAnimationRepeat(Animation animation) {
        }

        @Override // android.view.animation.Animation.AnimationListener
        public void onAnimationStart(Animation animation) {
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class b implements Animation.AnimationListener {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ View f23471a;

        b(View view) {
            this.f23471a = view;
        }

        @Override // android.view.animation.Animation.AnimationListener
        public void onAnimationEnd(Animation animation) {
            this.f23471a.setVisibility(0);
        }

        @Override // android.view.animation.Animation.AnimationListener
        public void onAnimationRepeat(Animation animation) {
        }

        @Override // android.view.animation.Animation.AnimationListener
        public void onAnimationStart(Animation animation) {
            this.f23471a.setVisibility(0);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class c implements Animator.AnimatorListener {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ int f23472a;

        /* renamed from: b, reason: collision with root package name */
        final /* synthetic */ View f23473b;

        c(int i5, View view) {
            this.f23472a = i5;
            this.f23473b = view;
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationCancel(Animator animator) {
            int i5 = this.f23472a;
            if (i5 != 0) {
                this.f23473b.setVisibility(i5);
            }
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            int i5 = this.f23472a;
            if (i5 != 0) {
                this.f23473b.setVisibility(i5);
            }
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationRepeat(Animator animator) {
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationStart(Animator animator) {
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class d implements Animator.AnimatorListener {

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ int f23474a;

        /* renamed from: b, reason: collision with root package name */
        final /* synthetic */ View f23475b;

        d(int i5, View view) {
            this.f23474a = i5;
            this.f23475b = view;
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationCancel(Animator animator) {
            int i5 = this.f23474a;
            if (i5 != 0) {
                this.f23475b.setVisibility(i5);
            }
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationEnd(Animator animator) {
            int i5 = this.f23474a;
            if (i5 != 0) {
                this.f23475b.setVisibility(i5);
            }
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationRepeat(Animator animator) {
        }

        @Override // android.animation.Animator.AnimatorListener
        public void onAnimationStart(Animator animator) {
        }
    }

    public static void a(View view, int i5) {
        c(view, i5, view.getHeight());
    }

    public static void b(View view, int i5) {
        h(view, i5, view.getHeight());
    }

    private static void c(View view, int i5, int i6) {
        if (view.getVisibility() == i5) {
            return;
        }
        view.setTranslationY(0.0f);
        if (i5 == 0) {
            view.setVisibility(0);
        }
        view.animate().translationY(i6).setListener(new d(i5, view)).setDuration(500L).start();
    }

    public static void d(View view) {
        view.clearAnimation();
        AlphaAnimation alphaAnimation = new AlphaAnimation(1.0f, 0.0f);
        alphaAnimation.setDuration(500L);
        alphaAnimation.setFillAfter(true);
        alphaAnimation.setAnimationListener(new AnimationAnimationListenerC0219a(view));
        view.startAnimation(alphaAnimation);
    }

    public static void e(View view) {
        if (view.getVisibility() == 0) {
            return;
        }
        view.clearAnimation();
        AlphaAnimation alphaAnimation = new AlphaAnimation(0.0f, 1.0f);
        alphaAnimation.setDuration(500L);
        alphaAnimation.setFillAfter(true);
        alphaAnimation.setAnimationListener(new b(view));
        view.startAnimation(alphaAnimation);
    }

    public static void f(View view, int i5) {
        h(view, i5, -view.getHeight());
    }

    public static void g(View view, int i5) {
        c(view, i5, -view.getHeight());
    }

    private static void h(View view, int i5, int i6) {
        if (i5 == 0) {
            view.setTranslationY(i6);
            view.setVisibility(0);
        }
        view.animate().translationY(0.0f).setListener(new c(i5, view)).setDuration(500L).start();
    }
}
