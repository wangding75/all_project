package com.loc.va.model;

import com.loc.va.App;
import com.lody.virtual.remote.InstalledAppInfo;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.Callable;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class u {

    /* renamed from: b, reason: collision with root package name */
    private static final u f22685b = new u();

    /* renamed from: a, reason: collision with root package name */
    private final Map<String, r> f22686a = new HashMap();

    public static u d() {
        return f22685b;
    }

    private r f(String str) {
        InstalledAppInfo v5 = com.lody.virtual.client.core.j.h().v(str, 0);
        if (v5 == null) {
            return null;
        }
        r rVar = new r(App.a(), v5);
        synchronized (this.f22686a) {
            this.f22686a.put(str, rVar);
        }
        return rVar;
    }

    /* renamed from: b, reason: merged with bridge method [inline-methods] */
    public r e(String str) {
        r rVar;
        synchronized (this.f22686a) {
            rVar = this.f22686a.get(str);
            if (rVar == null) {
                rVar = f(str);
            }
        }
        return rVar;
    }

    public void c(final String str, final l1.c<r> cVar) {
        org.jdeferred.p l5 = com.loc.va.abs.ui.c.a().l(new Callable() { // from class: com.loc.va.model.s
            @Override // java.util.concurrent.Callable
            public final Object call() {
                r e6;
                e6 = u.this.e(str);
                return e6;
            }
        });
        Objects.requireNonNull(cVar);
        l5.h(new org.jdeferred.g() { // from class: com.loc.va.model.t
            @Override // org.jdeferred.g
            public final void b(Object obj) {
                l1.c.this.a((r) obj);
            }
        });
    }
}
