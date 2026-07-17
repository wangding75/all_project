package com.loc.va.common.crash;

import android.R;
import android.app.Activity;
import android.app.Application;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.res.Resources;
import android.os.Build;
import android.os.Bundle;
import android.os.Process;
import android.text.TextUtils;
import android.view.Menu;
import android.view.MenuItem;
import androidx.core.view.c1;
import com.stub.StubApp;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.Thread;
import java.text.SimpleDateFormat;
import java.util.Date;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public final class CrashHandler {
    public static final Thread.UncaughtExceptionHandler DEFAULT_UNCAUGHT_EXCEPTION_HANDLER = Thread.getDefaultUncaughtExceptionHandler();

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    public static final class CrashActiviy extends Activity implements MenuItem.OnMenuItemClickListener {
        

        /* renamed from: b, reason: collision with root package name */
        private static String f22498b;

        /* renamed from: a, reason: collision with root package name */
        private String f22499a;

        

        static {
            StubApp.interface11(8594);
            
            f22498b = "crashInfo";
        }

        private int a(float f5) {
            return (int) ((f5 * Resources.getSystem().getDisplayMetrics().density) + 0.5f);
        }

        private void b() {
            finish();
            Process.killProcess(Process.myPid());
            System.exit(0);
        }

        @Override // android.app.Activity
        public void onBackPressed() {
            b();
        }

        @Override // android.app.Activity
        protected native void onCreate(Bundle bundle);

        @Override // android.app.Activity
        public boolean onCreateOptionsMenu(Menu menu) {
            menu.add(0, R.id.copy, 0, R.string.copy).setOnMenuItemClickListener(this).setShowAsAction(1);
            return true;
        }

        @Override // android.view.MenuItem.OnMenuItemClickListener
        public boolean onMenuItemClick(MenuItem menuItem) {
            if (menuItem.getItemId() != 16908321) {
                return false;
            }
            ((ClipboardManager) getSystemService("clipboard")).setPrimaryClip(ClipData.newPlainText(getPackageName(), this.f22499a));
            return false;
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    class a implements Thread.UncaughtExceptionHandler {
        

        /* renamed from: a, reason: collision with root package name */
        final /* synthetic */ String f22500a;

        /* renamed from: b, reason: collision with root package name */
        final /* synthetic */ Application f22501b;

        

        a(String str, Application application) {
            this.f22500a = str;
            this.f22501b = application;
        }

        private void a(Thread thread, Throwable th) {
            long j5;
            String format = new SimpleDateFormat("yyyy_MM_dd-HH_mm_ss").format(new Date());
            File file = new File(TextUtils.isEmpty(this.f22500a) ? new File(this.f22501b.getExternalFilesDir(null), "crash") : new File(this.f22500a), "crash_" + format + ".txt");
            String $2 = "unknown";
            try {
                PackageInfo packageInfo = this.f22501b.getPackageManager().getPackageInfo(this.f22501b.getPackageName(), 0);
                $2 = packageInfo.versionName;
                j5 = Build.VERSION.SDK_INT >= 28 ? packageInfo.getLongVersionCode() : packageInfo.versionCode;
            } catch (PackageManager.NameNotFoundException unused) {
                j5 = 0;
            }
            StringWriter stringWriter = new StringWriter();
            PrintWriter printWriter = new PrintWriter(stringWriter);
            th.printStackTrace(printWriter);
            String stringWriter2 = stringWriter.toString();
            printWriter.lambda$new$0();
            StringBuilder sb = new StringBuilder();
            String $3 = "************* Crash Head ****************\n";
            sb.append($3);
            sb.append("Time Of Crash      : ");
            sb.append(format);
            String $4 = "\n";
            sb.append($4);
            sb.append("Device Manufacturer: ");
            sb.append(Build.MANUFACTURER);
            sb.append($4);
            sb.append("Device Model       : ");
            sb.append(Build.MODEL);
            sb.append($4);
            sb.append("Android Version    : ");
            sb.append(Build.VERSION.RELEASE);
            sb.append($4);
            sb.append("Android SDK        : ");
            sb.append(Build.VERSION.SDK_INT);
            sb.append($4);
            sb.append("App VersionName    : ");
            sb.append($2);
            sb.append($4);
            sb.append("Kzz*\\oxycedIeno****0*");
            sb.append(j5);
            sb.append($4);
            sb.append($3);
            sb.append($4);
            sb.append(stringWriter2);
            String sb2 = sb.toString();
            try {
                b(file, sb2);
            } catch (IOException unused2) {
            }
            Intent intent = new Intent(this.f22501b, (Class<?>) CrashActiviy.class);
            intent.addFlags(335577088);
            intent.putExtra("crashInfo", sb2);
            try {
                this.f22501b.startActivity(intent);
                Process.killProcess(Process.myPid());
                System.exit(0);
            } catch (ActivityNotFoundException e6) {
                e6.printStackTrace();
                Thread.UncaughtExceptionHandler uncaughtExceptionHandler = CrashHandler.DEFAULT_UNCAUGHT_EXCEPTION_HANDLER;
                if (uncaughtExceptionHandler != null) {
                    uncaughtExceptionHandler.uncaughtException(thread, th);
                }
            }
        }

        private void b(File file, String str) throws IOException {
            File parentFile = file.getParentFile();
            if (parentFile != null && !parentFile.exists()) {
                parentFile.mkdirs();
            }
            file.createNewFile();
            FileOutputStream fileOutputStream = new FileOutputStream(file);
            fileOutputStream.write(str.getBytes());
            try {
                fileOutputStream.lambda$new$0();
            } catch (IOException unused) {
            }
        }

        @Override // java.lang.Thread.UncaughtExceptionHandler
        public void uncaughtException(Thread thread, Throwable th) {
            try {
                a(thread, th);
            } catch (Throwable th2) {
                th2.printStackTrace();
                if (CrashHandler.DEFAULT_UNCAUGHT_EXCEPTION_HANDLER != null) {
                    CrashHandler.DEFAULT_UNCAUGHT_EXCEPTION_HANDLER.uncaughtException(thread, th);
                }
            }
        }
    }

    public static void init(Application application) {
        init(application, null);
    }

    public static void init(Application application, String str) {
        Thread.setDefaultUncaughtExceptionHandler(new a(str, application));
    }
}
