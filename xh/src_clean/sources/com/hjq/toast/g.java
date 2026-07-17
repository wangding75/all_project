package com.hjq.toast;

import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.widget.Toast;
import java.util.Queue;
import java.util.concurrent.ArrayBlockingQueue;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
final class g extends Handler {

    /* renamed from: d, reason: collision with root package name */
    static final int f20854d = 2000;

    /* renamed from: e, reason: collision with root package name */
    static final int f20855e = 3500;

    /* renamed from: f, reason: collision with root package name */
    private static final int f20856f = 1;

    /* renamed from: g, reason: collision with root package name */
    private static final int f20857g = 2;

    /* renamed from: h, reason: collision with root package name */
    private static final int f20858h = 3;

    /* renamed from: i, reason: collision with root package name */
    private static final int f20859i = 3;

    /* renamed from: a, reason: collision with root package name */
    private volatile Queue<CharSequence> f20860a;

    /* renamed from: b, reason: collision with root package name */
    private volatile boolean f20861b;

    /* renamed from: c, reason: collision with root package name */
    private final Toast f20862c;

    g(Toast toast) {
        super(Looper.getMainLooper());
        this.f20862c = toast;
        this.f20860a = new ArrayBlockingQueue(3);
    }

    private static int c(CharSequence charSequence) {
        if (charSequence.length() > 20) {
            return f20855e;
        }
        return 2000;
    }

    void a(CharSequence charSequence) {
        if ((this.f20860a.isEmpty() || !this.f20860a.contains(charSequence)) && !this.f20860a.offer(charSequence)) {
            this.f20860a.poll();
            this.f20860a.offer(charSequence);
        }
    }

    void b() {
        if (this.f20861b) {
            this.f20861b = false;
            sendEmptyMessage(3);
        }
    }

    void d() {
        if (this.f20861b) {
            return;
        }
        this.f20861b = true;
        sendEmptyMessage(1);
    }

    @Override // android.os.Handler
    public void handleMessage(Message message) {
        int i5 = message.what;
        if (i5 == 1) {
            CharSequence peek = this.f20860a.peek();
            if (peek != null) {
                this.f20862c.setText(peek);
                this.f20862c.show();
                sendEmptyMessageDelayed(2, c(peek) + 300);
                return;
            }
        } else {
            if (i5 != 2) {
                if (i5 != 3) {
                    return;
                }
                this.f20861b = false;
                this.f20860a.clear();
                this.f20862c.cancel();
                return;
            }
            this.f20860a.poll();
            if (!this.f20860a.isEmpty()) {
                sendEmptyMessage(1);
                return;
            }
        }
        this.f20861b = false;
    }
}
