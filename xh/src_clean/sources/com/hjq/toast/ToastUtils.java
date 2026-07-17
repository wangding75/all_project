package com.hjq.toast;

import android.R;
import android.app.AppOpsManager;
import android.app.Application;
import android.app.NotificationManager;
import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.res.Resources;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import android.widget.Toast;
import com.stub.StubApp;
import java.lang.reflect.InvocationTargetException;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public final class ToastUtils {
    
    private static c sDefaultStyle;
    private static Toast sToast;
    private static g sToastHandler;

    

    private ToastUtils() {
    }

    public static void cancel() {
        checkToastState();
        sToastHandler.b();
    }

    private static void checkToastState() {
        if (sToast == null) {
            throw new IllegalStateException("ToastUtils has not been initialized");
        }
    }

    private static TextView createTextView(Context context) {
        GradientDrawable gradientDrawable = new GradientDrawable();
        gradientDrawable.setColor(sDefaultStyle.m());
        gradientDrawable.setCornerRadius(TypedValue.applyDimension(1, sDefaultStyle.h(), context.getResources().getDisplayMetrics()));
        TextView textView = new TextView(context);
        textView.setId(R.id.message);
        textView.setTextColor(sDefaultStyle.g());
        textView.setTextSize(0, TypedValue.applyDimension(2, sDefaultStyle.f(), context.getResources().getDisplayMetrics()));
        textView.setPadding((int) TypedValue.applyDimension(1, sDefaultStyle.k(), context.getResources().getDisplayMetrics()), (int) TypedValue.applyDimension(1, sDefaultStyle.j(), context.getResources().getDisplayMetrics()), (int) TypedValue.applyDimension(1, sDefaultStyle.b(), context.getResources().getDisplayMetrics()), (int) TypedValue.applyDimension(1, sDefaultStyle.d(), context.getResources().getDisplayMetrics()));
        textView.setLayoutParams(new ViewGroup.LayoutParams(-2, -2));
        textView.setBackground(gradientDrawable);
        textView.setZ(sDefaultStyle.c());
        if (sDefaultStyle.a() > 0) {
            textView.setMaxLines(sDefaultStyle.a());
        }
        return textView;
    }

    public static Toast getToast() {
        return sToast;
    }

    public static void init(Application application) {
        if (sDefaultStyle == null) {
            sDefaultStyle = new k1.b();
        }
        sToast = isNotificationEnabled(application) ? Build.VERSION.SDK_INT == 25 ? new e(application) : new a(application) : new f(application);
        sToastHandler = new g(sToast);
        setView(createTextView(StubApp.getOrigApplicationContext(application.getApplicationContext())));
        setGravity(sDefaultStyle.e(), sDefaultStyle.i(), sDefaultStyle.l());
    }

    public static void init(Application application, c cVar) {
        initStyle(cVar);
        init(application);
    }

    public static void initStyle(c cVar) {
        sDefaultStyle = cVar;
        Toast toast = sToast;
        if (toast != null) {
            toast.cancel();
            Toast toast2 = sToast;
            toast2.setView(createTextView(StubApp.getOrigApplicationContext(toast2.getView().getContext().getApplicationContext())));
            sToast.setGravity(sDefaultStyle.e(), sDefaultStyle.i(), sDefaultStyle.l());
        }
    }

    private static boolean isNotificationEnabled(Context context) {
        boolean areNotificationsEnabled;
        if (Build.VERSION.SDK_INT >= 24) {
            areNotificationsEnabled = ((NotificationManager) context.getSystemService("notification")).areNotificationsEnabled();
            return areNotificationsEnabled;
        }
        AppOpsManager appOpsManager = (AppOpsManager) context.getSystemService("appops");
        ApplicationInfo applicationInfo = context.getApplicationInfo();
        String packageName = StubApp.getOrigApplicationContext(context.getApplicationContext()).getPackageName();
        int i5 = applicationInfo.uid;
        try {
            Class<?> cls = Class.forName(AppOpsManager.class.getName());
            String $2 = "checkOpNoThrow";
            Class<Integer> cls2 = Integer.TYPE;
            return ((Integer) cls.getMethod($2, cls2, cls2, String.class).invoke(appOpsManager, Integer.valueOf(((Integer) cls.getDeclaredField("OP_POST_NOTIFICATION").get(Integer.class)).intValue()), Integer.valueOf(i5), packageName)).intValue() == 0;
        } catch (ClassNotFoundException | IllegalAccessException | NoSuchFieldException | NoSuchMethodException | RuntimeException | InvocationTargetException unused) {
            return true;
        }
    }

    public static void setGravity(int i5, int i6, int i7) {
        checkToastState();
        sToast.setGravity(Gravity.getAbsoluteGravity(i5, sToast.getView().getResources().getConfiguration().getLayoutDirection()), i6, i7);
    }

    public static void setView(int i5) {
        checkToastState();
        setView(View.inflate(StubApp.getOrigApplicationContext(sToast.getView().getContext().getApplicationContext()), i5, null));
    }

    public static void setView(View view) {
        checkToastState();
        if (view == null) {
            throw new IllegalArgumentException("Views cannot be empty");
        }
        if (view.getContext() != StubApp.getOrigApplicationContext(view.getContext().getApplicationContext())) {
            throw new IllegalArgumentException("The view must be initialized using the context of the application");
        }
        Toast toast = sToast;
        if (toast != null) {
            toast.cancel();
            sToast.setView(view);
        }
    }

    public static void show(int i5) {
        checkToastState();
        try {
            show(sToast.getView().getContext().getResources().getText(i5));
        } catch (Resources.NotFoundException unused) {
            show((CharSequence) String.valueOf(i5));
        }
    }

    public static void show(CharSequence charSequence) {
        checkToastState();
        if (charSequence == null || "".equals(charSequence.toString())) {
            return;
        }
        sToastHandler.a(charSequence);
        sToastHandler.d();
    }

    public static void show(Object obj) {
        show((CharSequence) (obj != null ? obj.toString() : "null"));
    }
}
