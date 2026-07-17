package com.loc.va.ui.widget.progress;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ObjectAnimator;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.os.Bundle;
import android.widget.TextView;
import b.u0;
import b.v0;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class SpotsDialog extends AlertDialog {
    
    private static final int DELAY = 150;
    private static final int DURATION = 1500;
    private AnimatorPlayer animator;
    private CharSequence message;
    private int size;
    private AnimatedView[] spots;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public static class Builder {
        private DialogInterface.OnCancelListener cancelListener;
        private boolean cancelable = true;
        private Context context;
        private String message;
        private int messageId;
        private int themeId;

        public AlertDialog build() {
            Context context = this.context;
            int i5 = this.messageId;
            String string = i5 != 0 ? context.getString(i5) : this.message;
            int i6 = this.themeId;
            if (i6 == 0) {
                i6 = c.q.M5;
            }
            return new SpotsDialog(context, string, i6, this.cancelable, this.cancelListener);
        }

        public Builder setCancelListener(DialogInterface.OnCancelListener onCancelListener) {
            this.cancelListener = onCancelListener;
            return this;
        }

        public Builder setCancelable(boolean z5) {
            this.cancelable = z5;
            return this;
        }

        public Builder setContext(Context context) {
            this.context = context;
            return this;
        }

        public Builder setMessage(@u0 int i5) {
            this.messageId = i5;
            return this;
        }

        public Builder setMessage(String str) {
            this.message = str;
            return this;
        }

        public Builder setTheme(@v0 int i5) {
            this.themeId = i5;
            return this;
        }
    }

    

    private SpotsDialog(Context context, String str, int i5, boolean z5, DialogInterface.OnCancelListener onCancelListener) {
        super(context, i5);
        this.message = str;
        setCancelable(z5);
        if (onCancelListener != null) {
            setOnCancelListener(onCancelListener);
        }
    }

    private Animator[] createAnimations() {
        Animator[] animatorArr = new Animator[this.size];
        int i5 = 0;
        while (true) {
            AnimatedView[] animatedViewArr = this.spots;
            if (i5 >= animatedViewArr.length) {
                return animatorArr;
            }
            final AnimatedView animatedView = animatedViewArr[i5];
            ObjectAnimator ofFloat = ObjectAnimator.ofFloat(animatedView, "xFactor", 0.0f, 1.0f);
            ofFloat.setDuration(1500L);
            ofFloat.setInterpolator(new HesitateInterpolator());
            ofFloat.setStartDelay(i5 * 150);
            ofFloat.addListener(new AnimatorListenerAdapter() { // from class: com.loc.va.ui.widget.progress.SpotsDialog.1
                @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
                public void onAnimationEnd(Animator animator) {
                    animatedView.setVisibility(4);
                }

                @Override // android.animation.AnimatorListenerAdapter, android.animation.Animator.AnimatorListener
                public void onAnimationStart(Animator animator) {
                    animatedView.setVisibility(0);
                }
            });
            animatorArr[i5] = ofFloat;
            i5++;
        }
    }

    private void initMessage() {
        CharSequence charSequence = this.message;
        if (charSequence == null || charSequence.length() <= 0) {
            return;
        }
        ((TextView) findViewById(c.i.f21734n4)).setText(this.message);
    }

    private void initProgress() {
        ProgressLayout progressLayout = (ProgressLayout) findViewById(c.i.f21728m4);
        int spotsCount = progressLayout.getSpotsCount();
        this.size = spotsCount;
        this.spots = new AnimatedView[spotsCount];
        int dimensionPixelSize = getContext().getResources().getDimensionPixelSize(c.g.n7);
        int dimensionPixelSize2 = getContext().getResources().getDimensionPixelSize(c.g.m7);
        for (int i5 = 0; i5 < this.spots.length; i5++) {
            AnimatedView animatedView = new AnimatedView(getContext());
            animatedView.setBackgroundResource(c.h.f21509a1);
            animatedView.setTarget(dimensionPixelSize2);
            animatedView.setXFactor(-1.0f);
            animatedView.setVisibility(4);
            progressLayout.addView(animatedView, dimensionPixelSize, dimensionPixelSize);
            this.spots[i5] = animatedView;
        }
    }

    @Override // android.app.AlertDialog, android.app.Dialog
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        setContentView(c.l.f21917s0);
        setCanceledOnTouchOutside(false);
        initMessage();
        initProgress();
    }

    @Override // android.app.Dialog
    protected void onStart() {
        super.onStart();
        for (AnimatedView animatedView : this.spots) {
            animatedView.setVisibility(0);
        }
        AnimatorPlayer animatorPlayer = new AnimatorPlayer(createAnimations());
        this.animator = animatorPlayer;
        animatorPlayer.play();
    }

    @Override // android.app.Dialog
    protected void onStop() {
        super.onStop();
        this.animator.stop();
    }

    @Override // android.app.AlertDialog
    public void setMessage(CharSequence charSequence) {
        this.message = charSequence;
        if (isShowing()) {
            initMessage();
        }
    }
}
