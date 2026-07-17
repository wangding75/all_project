package com.loc.va.home;

import android.app.Activity;
import com.loc.va.home.q;
import java.io.File;
import java.util.List;
import java.util.Objects;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
class v implements q.a {

    /* renamed from: a, reason: collision with root package name */
    private Activity f22620a;

    /* renamed from: b, reason: collision with root package name */
    private q.b f22621b;

    /* renamed from: c, reason: collision with root package name */
    private com.loc.va.model.b f22622c;

    /* renamed from: d, reason: collision with root package name */
    private File f22623d;

    v(Activity activity, q.b bVar, File file) {
        this.f22620a = activity;
        this.f22621b = bVar;
        this.f22622c = new com.loc.va.model.h(activity);
        this.f22621b.e(this);
        this.f22623d = file;
    }

    @Override // l1.a
    public void start() {
        org.jdeferred.p<List<com.loc.va.model.c>, Throwable, Void> e6;
        org.jdeferred.g<List<com.loc.va.model.c>> gVar;
        this.f22621b.e(this);
        this.f22621b.b();
        File file = this.f22623d;
        if (file == null) {
            e6 = this.f22622c.b(this.f22620a);
            final q.b bVar = this.f22621b;
            Objects.requireNonNull(bVar);
            gVar = new org.jdeferred.g() { // from class: com.loc.va.home.u
                @Override // org.jdeferred.g
                public final void b(Object obj) {
                    q.b.this.loadFinish((List) obj);
                }
            };
        } else {
            e6 = this.f22622c.e(this.f22620a, file);
            final q.b bVar2 = this.f22621b;
            Objects.requireNonNull(bVar2);
            gVar = new org.jdeferred.g() { // from class: com.loc.va.home.u
                @Override // org.jdeferred.g
                public final void b(Object obj) {
                    q.b.this.loadFinish((List) obj);
                }
            };
        }
        e6.h(gVar);
    }
}
