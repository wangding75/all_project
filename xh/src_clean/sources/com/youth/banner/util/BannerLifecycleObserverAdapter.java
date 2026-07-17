package com.youth.banner.util;

import androidx.lifecycle.l;
import androidx.lifecycle.o;
import androidx.lifecycle.p;
import androidx.lifecycle.w;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class BannerLifecycleObserverAdapter implements o {
    
    private final p mLifecycleOwner;
    private final BannerLifecycleObserver mObserver;

    

    public BannerLifecycleObserverAdapter(p pVar, BannerLifecycleObserver bannerLifecycleObserver) {
        this.mLifecycleOwner = pVar;
        this.mObserver = bannerLifecycleObserver;
    }

    @w(l.b.ON_DESTROY)
    public void onDestroy() {
        LogUtils.i("onDestroy");
        this.mObserver.onDestroy(this.mLifecycleOwner);
    }

    @w(l.b.ON_START)
    public void onStart() {
        LogUtils.i("onStart");
        this.mObserver.onStart(this.mLifecycleOwner);
    }

    @w(l.b.ON_STOP)
    public void onStop() {
        LogUtils.i("onStop");
        this.mObserver.onStop(this.mLifecycleOwner);
    }
}
