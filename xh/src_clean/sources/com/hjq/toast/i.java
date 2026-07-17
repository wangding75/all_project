package com.hjq.toast;

import android.annotation.TargetApi;
import android.app.Activity;
import android.app.Application;
import android.os.Bundle;
import android.util.ArrayMap;
import android.view.WindowManager;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
@TargetApi(19)
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
final class i implements Application.ActivityLifecycleCallbacks {
    

    /* renamed from: a, reason: collision with root package name */
    private final ArrayMap<String, Activity> f20868a = new ArrayMap<>();

    /* renamed from: b, reason: collision with root package name */
    private final h f20869b;

    /* renamed from: c, reason: collision with root package name */
    private String f20870c;

    

    i(h hVar, Application application) {
        this.f20869b = hVar;
        application.registerActivityLifecycleCallbacks(this);
    }

    private static String a(Object obj) {
        return obj.getClass().getName() + Integer.toHexString(obj.hashCode());
    }

    private static WindowManager c(Activity activity) {
        return (WindowManager) activity.getSystemService("window");
    }

    WindowManager b() throws NullPointerException {
        Activity activity;
        String str = this.f20870c;
        if (str == null || (activity = this.f20868a.get(str)) == null) {
            throw null;
        }
        return c(activity);
    }

    @Override // android.app.Application.ActivityLifecycleCallbacks
    public void onActivityCreated(Activity activity, Bundle bundle) {
        String a6 = a(activity);
        this.f20870c = a6;
        this.f20868a.put(a6, activity);
    }

    @Override // android.app.Application.ActivityLifecycleCallbacks
    public void onActivityDestroyed(Activity activity) {
        this.f20868a.remove(a(activity));
        if (a(activity).equals(this.f20870c)) {
            this.f20870c = null;
        }
    }

    @Override // android.app.Application.ActivityLifecycleCallbacks
    public void onActivityPaused(Activity activity) {
        this.f20869b.a();
    }

    @Override // android.app.Application.ActivityLifecycleCallbacks
    public void onActivityResumed(Activity activity) {
        this.f20870c = a(activity);
    }

    @Override // android.app.Application.ActivityLifecycleCallbacks
    public void onActivitySaveInstanceState(Activity activity, Bundle bundle) {
    }

    @Override // android.app.Application.ActivityLifecycleCallbacks
    public void onActivityStarted(Activity activity) {
        this.f20870c = a(activity);
    }

    @Override // android.app.Application.ActivityLifecycleCallbacks
    public void onActivityStopped(Activity activity) {
    }
}
