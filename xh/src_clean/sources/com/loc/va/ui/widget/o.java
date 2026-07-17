package com.loc.va.ui.widget;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class o {

    /* renamed from: f, reason: collision with root package name */
    public static final int f23381f = 4369;

    /* renamed from: g, reason: collision with root package name */
    public static final int f23382g = 1;

    /* renamed from: h, reason: collision with root package name */
    public static final int f23383h = 16;

    /* renamed from: i, reason: collision with root package name */
    public static final int f23384i = 256;

    /* renamed from: j, reason: collision with root package name */
    public static final int f23385j = 4096;

    /* renamed from: a, reason: collision with root package name */
    private int f23386a;

    /* renamed from: b, reason: collision with root package name */
    private int f23387b;

    /* renamed from: c, reason: collision with root package name */
    private int f23388c;

    /* renamed from: d, reason: collision with root package name */
    private int f23389d;

    /* renamed from: e, reason: collision with root package name */
    private int f23390e = f23381f;

    public int a() {
        return this.f23386a;
    }

    public int b() {
        return this.f23388c;
    }

    public int c() {
        return this.f23389d;
    }

    public int d() {
        return e() * 2;
    }

    public int e() {
        if (this.f23387b <= 0) {
            return 0;
        }
        return Math.max(this.f23388c, this.f23389d) + this.f23387b;
    }

    public int f() {
        return this.f23387b;
    }

    public int g() {
        return this.f23390e;
    }

    public o h(int i5) {
        this.f23386a = i5;
        return this;
    }

    public o i(int i5) {
        this.f23388c = i5;
        return this;
    }

    public o j(int i5) {
        this.f23389d = i5;
        return this;
    }

    public o k(int i5) {
        this.f23387b = i5;
        return this;
    }

    public o l(int i5) {
        this.f23390e = i5;
        return this;
    }
}
