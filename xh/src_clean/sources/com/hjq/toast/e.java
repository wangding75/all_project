package com.hjq.toast;

import android.app.Application;
import android.os.Handler;
import android.os.Message;
import android.view.WindowManager;
import android.widget.Toast;
import java.lang.reflect.Field;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
final class e extends com.hjq.toast.a {
    

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    static final class a extends Handler {

        /* renamed from: a, reason: collision with root package name */
        private Handler f20852a;

        a(Handler handler) {
            this.f20852a = handler;
        }

        @Override // android.os.Handler
        public void dispatchMessage(Message message) {
            this.f20852a.dispatchMessage(message);
        }

        @Override // android.os.Handler
        public void handleMessage(Message message) {
            try {
                this.f20852a.handleMessage(message);
            } catch (WindowManager.BadTokenException unused) {
            }
        }
    }

    

    e(Application application) {
        super(application);
        try {
            Field declaredField = Toast.class.getDeclaredField("mTN");
            declaredField.setAccessible(true);
            Object obj = declaredField.get(this);
            Field declaredField2 = declaredField.getType().getDeclaredField("mHandler");
            declaredField2.setAccessible(true);
            declaredField2.set(obj, new a((Handler) declaredField2.get(obj)));
        } catch (Exception unused) {
        }
    }
}
