package com.loc.va.utils;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class b {
    

    /* renamed from: a, reason: collision with root package name */
    public static String f23476a = "bd09ll";

    /* renamed from: b, reason: collision with root package name */
    public static String f23477b = "bd09";

    /* renamed from: c, reason: collision with root package name */
    public static String f23478c = "gcj02";

    /* renamed from: d, reason: collision with root package name */
    public static float[] f23479d = {0.1f, 0.2f, 0.4f, 0.6f, 0.8f};

    /* renamed from: e, reason: collision with root package name */
    static double f23480e = 6378245.0d;

    /* renamed from: f, reason: collision with root package name */
    static double f23481f = 0.006693421622965943d;

    /* renamed from: g, reason: collision with root package name */
    static double f23482g = 3.141592653589793d;

    /* renamed from: h, reason: collision with root package name */
    public static final double f23483h = 52.35987755982988d;

    

    public static double[] a(double d6, double d7) {
        double d8 = d6 - 0.0065d;
        double d9 = d7 - 0.006d;
        double sqrt = Math.sqrt((d8 * d8) + (d9 * d9)) - (Math.sin(d9 * 52.35987755982988d) * 2.0E-5d);
        double atan2 = Math.atan2(d9, d8) - (Math.cos(d8 * 52.35987755982988d) * 3.0E-6d);
        return new double[]{Math.cos(atan2) * sqrt, sqrt * Math.sin(atan2)};
    }

    public static double[] b(double d6, double d7) {
        double[] a6 = a(d6, d7);
        return d(a6[0], a6[1]);
    }

    public static double[] c(double d6, double d7) {
        double sqrt = Math.sqrt((d6 * d6) + (d7 * d7)) + (Math.sin(d7 * 52.35987755982988d) * 2.0E-5d);
        double atan2 = Math.atan2(d7, d6) + (Math.cos(d6 * 52.35987755982988d) * 3.0E-6d);
        return new double[]{(Math.cos(atan2) * sqrt) + 0.0065d, (sqrt * Math.sin(atan2)) + 0.006d};
    }

    public static double[] d(double d6, double d7) {
        double d8 = d6 - 105.0d;
        double d9 = d7 - 35.0d;
        double f5 = f(d8, d9);
        double g5 = g(d8, d9);
        double d10 = (d7 / 180.0d) * f23482g;
        double sin = Math.sin(d10);
        double d11 = 1.0d - ((f23481f * sin) * sin);
        double sqrt = Math.sqrt(d11);
        double cos = (f23480e / sqrt) * Math.cos(d10);
        double d12 = f23482g;
        return new double[]{(d6 * 2.0d) - (d6 + ((g5 * 180.0d) / (cos * d12))), (d7 * 2.0d) - (d7 + ((f5 * 180.0d) / (((f23480e * (1.0d - f23481f)) / (d11 * sqrt)) * d12)))};
    }

    private static boolean e(double d6, double d7) {
        return d6 < 72.004d || d6 > 137.8347d || d7 < 0.8293d || d7 > 55.8271d;
    }

    private static double f(double d6, double d7) {
        double d8 = d6 * 2.0d;
        return (-100.0d) + d8 + (d7 * 3.0d) + (d7 * 0.2d * d7) + (0.1d * d6 * d7) + (Math.sqrt(Math.abs(d6)) * 0.2d) + ((((Math.sin((d6 * 6.0d) * f23482g) * 20.0d) + (Math.sin(d8 * f23482g) * 20.0d)) * 2.0d) / 3.0d) + ((((Math.sin(f23482g * d7) * 20.0d) + (Math.sin((d7 / 3.0d) * f23482g) * 40.0d)) * 2.0d) / 3.0d) + ((((Math.sin((d7 / 12.0d) * f23482g) * 160.0d) + (Math.sin((d7 * f23482g) / 30.0d) * 320.0d)) * 2.0d) / 3.0d);
    }

    private static double g(double d6, double d7) {
        double d8 = d6 * 0.1d;
        return d6 + 300.0d + (d7 * 2.0d) + (d8 * d6) + (d8 * d7) + (Math.sqrt(Math.abs(d6)) * 0.1d) + ((((Math.sin((6.0d * d6) * f23482g) * 20.0d) + (Math.sin((d6 * 2.0d) * f23482g) * 20.0d)) * 2.0d) / 3.0d) + ((((Math.sin(f23482g * d6) * 20.0d) + (Math.sin((d6 / 3.0d) * f23482g) * 40.0d)) * 2.0d) / 3.0d) + ((((Math.sin((d6 / 12.0d) * f23482g) * 150.0d) + (Math.sin((d6 / 30.0d) * f23482g) * 300.0d)) * 2.0d) / 3.0d);
    }

    public static double[] h(double d6, double d7) {
        double[] i5 = i(d6, d7);
        return c(i5[0], i5[1]);
    }

    public static double[] i(double d6, double d7) {
        if (e(d6, d7)) {
            return new double[]{d6, d7};
        }
        double d8 = d6 - 105.0d;
        double d9 = d7 - 35.0d;
        double f5 = f(d8, d9);
        double g5 = g(d8, d9);
        double d10 = (d7 / 180.0d) * f23482g;
        double sin = Math.sin(d10);
        double d11 = 1.0d - ((f23481f * sin) * sin);
        double sqrt = Math.sqrt(d11);
        double d12 = f23480e;
        return new double[]{d6 + ((g5 * 180.0d) / (((d12 / sqrt) * Math.cos(d10)) * f23482g)), d7 + ((f5 * 180.0d) / ((((1.0d - f23481f) * d12) / (d11 * sqrt)) * f23482g))};
    }
}
