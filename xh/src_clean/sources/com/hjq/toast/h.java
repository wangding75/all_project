package com.hjq.toast;

import android.R;
import android.app.Application;
import android.app.StatsManager;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.view.WindowManager;
import android.widget.Toast;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
final class h extends Handler {
    

    /* renamed from: e, reason: collision with root package name */
    private static String f20863e = "Toast";

    /* renamed from: a, reason: collision with root package name */
    private final Toast f20864a;

    /* renamed from: b, reason: collision with root package name */
    private final i f20865b;

    /* renamed from: c, reason: collision with root package name */
    private final String f20866c;

    /* renamed from: d, reason: collision with root package name */
    private boolean f20867d;

    

    h(Toast toast, Application application) {
        super(Looper.getMainLooper());
        this.f20864a = toast;
        this.f20866c = application.getPackageName();
        this.f20865b = new i(this, application);
    }

    void a() {
        removeMessages(0);
        if (this.f20867d) {
            try {
                this.f20865b.b().removeView(this.f20864a.getView());
            } catch (IllegalArgumentException | NullPointerException unused) {
            }
            this.f20867d = false;
        }
    }

    void b() {
        if (this.f20867d) {
            return;
        }
        WindowManager.LayoutParams layoutParams = new WindowManager.LayoutParams();
        layoutParams.height = -2;
        layoutParams.width = -2;
        layoutParams.format = -3;
        layoutParams.windowAnimations = R.style.Animation.Toast;
        layoutParams.setTitle("Toast");
        layoutParams.flags = 152;
        layoutParams.packageName = this.f20866c;
        layoutParams.gravity = this.f20864a.getGravity();
        layoutParams.x = this.f20864a.getXOffset();
        layoutParams.y = this.f20864a.getYOffset();
        try {
            this.f20865b.b().addView(this.f20864a.getView(), layoutParams);
            this.f20867d = true;
            sendEmptyMessageDelayed(0, this.f20864a.getDuration() == 1 ? 3500L : StatsManager.DEFAULT_TIMEOUT_MILLIS);
        } catch (WindowManager.BadTokenException | IllegalStateException | NullPointerException unused) {
        }
    }

    @Override // android.os.Handler
    public void handleMessage(Message message) {
        a();
    }
}
