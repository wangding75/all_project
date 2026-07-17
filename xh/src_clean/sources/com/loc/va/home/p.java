package com.loc.va.home;

import android.app.Activity;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.os.Build;
import android.os.Environment;
import android.provider.Settings;
import android.widget.Toast;
import androidx.appcompat.app.d;
import b.o0;
import com.loc.va.c;
import com.loc.va.home.b;
import com.loc.va.home.p;
import com.loc.va.model.AppData;
import com.loc.va.model.AppInfoLite;
import com.lody.virtual.client.ipc.VActivityManager;
import com.lody.virtual.client.ipc.VPackageManager;
import com.lody.virtual.client.stub.RequestExternalStorageManagerActivity;
import com.lody.virtual.remote.InstalledAppInfo;
import com.lody.virtual.remote.VAppInstallerResult;
import java.util.List;
import java.util.Objects;
import jonathanfinerty.once.Once;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
class p implements b.a {
    

    /* renamed from: a, reason: collision with root package name */
    private b.InterfaceC0211b f22605a;

    /* renamed from: b, reason: collision with root package name */
    private Activity f22606b;

    /* renamed from: c, reason: collision with root package name */
    private com.loc.va.model.h f22607c;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class a {

        /* renamed from: a, reason: collision with root package name */
        private com.loc.va.model.r f22608a;

        /* renamed from: b, reason: collision with root package name */
        private int f22609b;

        a() {
        }
    }

    

    p(b.InterfaceC0211b interfaceC0211b) {
        this.f22605a = interfaceC0211b;
        this.f22606b = interfaceC0211b.d();
        this.f22607c = new com.loc.va.model.h(this.f22606b);
        this.f22605a.k(this);
    }

    public static boolean k(Context context) {
        boolean isExternalStorageManager;
        if (Build.VERSION.SDK_INT >= 30) {
            isExternalStorageManager = Environment.isExternalStorageManager();
            if (!isExternalStorageManager) {
                Intent intent = new Intent("android.settings.MANAGE_ALL_FILES_ACCESS_PERMISSION");
                intent.addFlags(268435456);
                context.startActivity(intent);
                return false;
            }
        }
        return true;
    }

    private void l(final AppData appData) {
        com.loc.va.abs.ui.c.a().j(new Runnable() { // from class: com.loc.va.home.d
            @Override // java.lang.Runnable
            public final void run() {
                p.t();
            }
        }).h(new org.jdeferred.g() { // from class: com.loc.va.home.e
            @Override // org.jdeferred.g
            public final void b(Object obj) {
                p.this.u(appData, (Void) obj);
            }
        });
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void m(AppInfoLite appInfoLite, a aVar) {
        InstalledAppInfo v5 = com.lody.virtual.client.core.j.h().v(appInfoLite.f22627a, 0);
        if (v5 != null) {
            aVar.f22609b = a2.a.a(v5);
            return;
        }
        VAppInstallerResult c6 = this.f22607c.c(appInfoLite);
        if (c6.f24750b == 0) {
            return;
        }
        throw new IllegalStateException("error code: " + c6.f24750b);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static /* synthetic */ void n(a aVar, AppInfoLite appInfoLite, Void r6) {
        aVar.f22608a = com.loc.va.model.u.d().e(appInfoLite.f22627a);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void o(ProgressDialog progressDialog, Throwable th) {
        th.printStackTrace();
        progressDialog.dismiss();
        Toast.makeText(this.f22606b, th.getMessage(), 0).show();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void p(a aVar, ProgressDialog progressDialog, Void r9) {
        if (aVar.f22609b == 0) {
            com.loc.va.model.r rVar = aVar.f22608a;
            rVar.f22626b = true;
            this.f22605a.addAppToLauncher(rVar);
            l(rVar);
        } else {
            com.loc.va.model.q qVar = new com.loc.va.model.q(aVar.f22608a, aVar.f22609b);
            qVar.f22626b = true;
            this.f22605a.addAppToLauncher(qVar);
            l(qVar);
        }
        progressDialog.dismiss();
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void q(AppData appData) {
        this.f22607c.a(appData.g(), appData.h());
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static /* synthetic */ void t() {
        long currentTimeMillis = System.currentTimeMillis() - System.currentTimeMillis();
        if (currentTimeMillis < 1500) {
            try {
                Thread.sleep(1500 - currentTimeMillis);
            } catch (InterruptedException e6) {
                e6.printStackTrace();
            }
        }
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void u(AppData appData, Void r8) {
        AppData appData2;
        if (!(appData instanceof com.loc.va.model.r)) {
            if (appData instanceof com.loc.va.model.q) {
                appData2 = (com.loc.va.model.q) appData;
            }
            this.f22605a.refreshLauncherItem(appData);
        }
        appData2 = (com.loc.va.model.r) appData;
        appData2.f22626b = false;
        appData2.f22625a = true;
        this.f22605a.refreshLauncherItem(appData);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static /* synthetic */ void v(boolean z5, DialogInterface dialogInterface, int i5) {
        RequestExternalStorageManagerActivity.a(com.lody.virtual.client.core.j.h().m(), z5);
    }

    private void w(int i5, String str) {
        if (com.lody.virtual.client.core.j.h().h0(str)) {
            if (!com.lody.virtual.client.core.j.h().b0()) {
                Toast.makeText(this.f22606b, "Please install Extension Package.", 0).show();
                return;
            } else if (!com.lody.virtual.server.extension.a.k()) {
                Toast.makeText(this.f22606b, c.p.f22040g4, 0).show();
                return;
            }
        }
        VActivityManager.get().launchApp(i5, str);
    }

    @Override // com.loc.va.home.b.a
    public void addApp(final AppInfoLite appInfoLite) {
        final a aVar = new a();
        Activity activity = this.f22606b;
        final ProgressDialog show = ProgressDialog.show(activity, null, activity.getString(c.p.n5));
        com.loc.va.abs.ui.c.a().j(new Runnable() { // from class: com.loc.va.home.l
            @Override // java.lang.Runnable
            public final void run() {
                p.this.m(appInfoLite, aVar);
            }
        }).m(new org.jdeferred.g() { // from class: com.loc.va.home.m
            @Override // org.jdeferred.g
            public final void b(Object obj) {
                p.n(p.a.this, appInfoLite, (Void) obj);
            }
        }).r(new org.jdeferred.j() { // from class: com.loc.va.home.n
            @Override // org.jdeferred.j
            public final void b(Object obj) {
                p.this.o(show, (Throwable) obj);
            }
        }).h(new org.jdeferred.g() { // from class: com.loc.va.home.o
            @Override // org.jdeferred.g
            public final void b(Object obj) {
                p.this.p(aVar, show, (Void) obj);
            }
        });
    }

    @Override // com.loc.va.home.b.a
    @o0(api = 23)
    public boolean checkExtPackageBootPermission() {
        if (!com.lody.virtual.client.core.j.h().b0()) {
            return false;
        }
        if (!com.lody.virtual.server.extension.a.k()) {
            this.f22605a.showPermissionDialog();
            return true;
        }
        if (!com.lody.virtual.helper.compat.d.k() || Settings.canDrawOverlays(this.f22606b)) {
            return false;
        }
        this.f22605a.showOverlayPermissionDialog();
        return true;
    }

    @Override // com.loc.va.home.b.a
    public void dataChanged() {
        this.f22605a.showLoading();
        org.jdeferred.p<List<AppData>, Throwable, Void> d6 = this.f22607c.d();
        final b.InterfaceC0211b interfaceC0211b = this.f22605a;
        Objects.requireNonNull(interfaceC0211b);
        org.jdeferred.p<List<AppData>, Throwable, Void> h5 = d6.h(new org.jdeferred.g() { // from class: com.loc.va.home.j
            @Override // org.jdeferred.g
            public final void b(Object obj) {
                b.InterfaceC0211b.this.loadFinish((List) obj);
            }
        });
        final b.InterfaceC0211b interfaceC0211b2 = this.f22605a;
        Objects.requireNonNull(interfaceC0211b2);
        h5.r(new org.jdeferred.j() { // from class: com.loc.va.home.k
            @Override // org.jdeferred.j
            public final void b(Object obj) {
                b.InterfaceC0211b.this.loadError((Throwable) obj);
            }
        });
    }

    @Override // com.loc.va.home.b.a
    public void deleteApp(final AppData appData) {
        this.f22605a.removeAppToLauncher(appData);
        Activity activity = this.f22606b;
        final ProgressDialog show = ProgressDialog.show(activity, activity.getString(c.p.o5), appData.f());
        com.loc.va.abs.ui.c.a().j(new Runnable() { // from class: com.loc.va.home.g
            @Override // java.lang.Runnable
            public final void run() {
                p.this.q(appData);
            }
        }).r(new org.jdeferred.j() { // from class: com.loc.va.home.h
            @Override // org.jdeferred.j
            public final void b(Object obj) {
                show.dismiss();
            }
        }).h(new org.jdeferred.g() { // from class: com.loc.va.home.i
            @Override // org.jdeferred.g
            public final void b(Object obj) {
                show.dismiss();
            }
        });
    }

    @Override // com.loc.va.home.b.a
    public void enterAppSetting(AppData appData) {
        AppSettingActivity.m0(this.f22606b, appData.g(), appData.h());
    }

    @Override // com.loc.va.home.b.a
    public int getAppCount() {
        return com.lody.virtual.client.core.j.h().w(0).size();
    }

    @Override // com.loc.va.home.b.a
    public String getLabel(String str) {
        return this.f22607c.getLabel(str);
    }

    /* JADX WARN: Code restructure failed: missing block: B:23:0x006f, code lost:
    
        if (r3 == false) goto L25;
     */
    /* JADX WARN: Removed duplicated region for block: B:30:0x00cb A[Catch: all -> 0x00d1, TRY_LEAVE, TryCatch #0 {all -> 0x00d1, blocks: (B:3:0x0004, B:6:0x0011, B:35:0x0034, B:9:0x004f, B:13:0x0059, B:16:0x0063, B:18:0x0071, B:22:0x006b, B:24:0x00a4, B:26:0x00aa, B:28:0x00ba, B:30:0x00cb, B:36:0x0048), top: B:2:0x0004 }] */
    /* JADX WARN: Removed duplicated region for block: B:32:? A[RETURN, SYNTHETIC] */
    @Override // com.loc.va.home.b.a
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public void launchApp(AppData appData) {
        boolean z5;
        boolean isExternalStorageManager;
        try {
            int h5 = appData.h();
            String g5 = appData.g();
            if (h5 == -1 || g5 == null) {
                return;
            }
            InstalledAppInfo v5 = com.lody.virtual.client.core.j.h().v(g5, h5);
            ApplicationInfo h6 = v5.h(h5);
            final boolean h02 = com.lody.virtual.client.core.j.h().h0(v5.f24691a);
            int i5 = com.lody.virtual.client.core.j.h().q().targetSdkVersion;
            if (h02) {
                try {
                    i5 = this.f22606b.getPackageManager().getApplicationInfo(com.lody.virtual.client.core.j.l().d(), 0).targetSdkVersion;
                } catch (Exception unused) {
                }
                if (checkExtPackageBootPermission()) {
                    return;
                }
            }
            if (com.lody.virtual.helper.compat.d.l() && i5 >= 30 && v5.h(0).targetSdkVersion < 30) {
                if (!h02 || com.lody.virtual.server.extension.a.l()) {
                    if (!h02) {
                        isExternalStorageManager = Environment.isExternalStorageManager();
                    }
                }
                new d.a(this.f22606b).J(c.p.f22046h4).m(c.p.D4).d(false).s("GO", new DialogInterface.OnClickListener() { // from class: com.loc.va.home.f
                    @Override // android.content.DialogInterface.OnClickListener
                    public final void onClick(DialogInterface dialogInterface, int i6) {
                        p.v(h02, dialogInterface, i6);
                    }
                }).O();
                return;
            }
            if (com.lody.virtual.helper.compat.s.d(h6)) {
                String[] dangerousPermissions = VPackageManager.get().getDangerousPermissions(v5.f24691a);
                if (!com.lody.virtual.helper.compat.s.a(dangerousPermissions, h02)) {
                    PermissionRequestActivity.c(this.f22606b, dangerousPermissions, appData.f(), h5, g5, 6);
                    z5 = false;
                    if (z5) {
                        return;
                    }
                    appData.f22625a = false;
                    w(h5, g5);
                    return;
                }
            }
            z5 = true;
            if (z5) {
            }
        } catch (Throwable th) {
            th.printStackTrace();
        }
    }

    @Override // l1.a
    public void start() {
        dataChanged();
        String $2 = "Should show add app guide";
        if (Once.beenDone($2)) {
            return;
        }
        this.f22605a.showGuide();
        Once.markDone($2);
    }
}
