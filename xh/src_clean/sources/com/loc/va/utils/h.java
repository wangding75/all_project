package com.loc.va.utils;

import android.content.Context;
import com.loc.va.c;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Locale;
import java.util.TimeZone;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class h {
    

    /* renamed from: a, reason: collision with root package name */
    private static boolean f23508a = true;

    

    public static double a(double d6) {
        return f23508a ? d6 : Double.parseDouble(b(d6));
    }

    public static String b(double d6) {
        if (f23508a) {
            return String.valueOf(d6);
        }
        DecimalFormat decimalFormat = new DecimalFormat();
        decimalFormat.setMaximumFractionDigits(6);
        return decimalFormat.format(d6);
    }

    public static double c(double d6) {
        return f23508a ? d6 : Double.parseDouble(d(d6));
    }

    public static String d(double d6) {
        if (f23508a) {
            return String.valueOf(d6);
        }
        DecimalFormat decimalFormat = new DecimalFormat();
        decimalFormat.setMaximumFractionDigits(8);
        return decimalFormat.format(d6);
    }

    public static String e(long j5) {
        Calendar calendar = Calendar.getInstance(TimeZone.getTimeZone("GMT+0"));
        calendar.setTimeInMillis(j5);
        return String.format("%02d:%02d:%02d", Integer.valueOf(calendar.get(11)), Integer.valueOf(calendar.get(12)), Integer.valueOf(calendar.get(13)));
    }

    public static String f(long j5) {
        Calendar calendar = Calendar.getInstance(TimeZone.getTimeZone("GMT+0"));
        calendar.setTimeInMillis(j5);
        return String.format("%02d:%02d", Integer.valueOf((calendar.get(11) * 60) + calendar.get(12)), Integer.valueOf(calendar.get(13)));
    }

    public static boolean g(String str) {
        return (str == null || "".equals(str)) ? false : true;
    }

    public static String h(Context context, long j5) {
        Calendar.getInstance(Locale.getDefault()).setTimeInMillis(j5);
        return new SimpleDateFormat("yyyy-MM-dd [" + context.getResources().getStringArray(c.C0208c.f21022c)[r0.get(7) - 1] + "] hh:mm").format(Long.valueOf(j5));
    }
}
