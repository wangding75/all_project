package com.loc.va.model;

import android.content.Context;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.icu.impl.Normalizer2Impl;
import com.lody.virtual.remote.InstalledAppInfo;
import com.lody.virtual.remote.VAppInstallerParams;
import com.lody.virtual.remote.VAppInstallerResult;
import dalvik.bytecode.Opcodes;
import java.io.File;
import java.text.Collator;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.Callable;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class h implements b {
    

    /* renamed from: c, reason: collision with root package name */
    private static final Collator f22650c = Collator.getInstance(Locale.CHINA);

    /* renamed from: d, reason: collision with root package name */
    private static final List<String> f22651d = Arrays.asList("《", "backups/apps", "(>1;0*56>p>//", "tencent/tassistant/apk", "BaiduAsa9103056", "360Download", "pp/downloader", "pp/downloader/apk", "pp/downloader/silent/apk");

    /* renamed from: a, reason: collision with root package name */
    private final Map<String, String> f22652a = new HashMap();

    /* renamed from: b, reason: collision with root package name */
    private Context f22653b;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    private static class a implements Comparator<c> {
        

        

        private a() {
        }

        @Override // java.util.Comparator
        /* renamed from: a, reason: merged with bridge method [inline-methods] */
        public int compare(c cVar, c cVar2) {
            String str = cVar.f22643i;
            String $2 = "#";
            if (str.equals($2)) {
                return 1;
            }
            if (cVar2.f22643i.equals($2)) {
                return -1;
            }
            return cVar.f22643i.compareTo(cVar2.f22643i);
        }
    }

    

    public h(Context context) {
        this.f22653b = context;
    }

    private List<c> j(Context context, List<PackageInfo> list, boolean z5, boolean z6) {
        PackageManager packageManager = context.getPackageManager();
        ArrayList arrayList = new ArrayList(list.size());
        for (PackageInfo packageInfo : list) {
            if (!com.lody.virtual.client.stub.d.i(packageInfo.packageName) && (!z6 || !com.lody.virtual.c.d(packageInfo.packageName))) {
                if (!z5 || !l(packageInfo)) {
                    ApplicationInfo applicationInfo = packageInfo.applicationInfo;
                    if ((applicationInfo.flags & 4) != 0) {
                        String str = applicationInfo.publicSourceDir;
                        if (str == null) {
                            str = applicationInfo.sourceDir;
                        }
                        if (str != null) {
                            InstalledAppInfo v5 = com.lody.virtual.client.core.j.h().v(packageInfo.packageName, 0);
                            c cVar = new c();
                            cVar.f22635a = packageInfo.packageName;
                            cVar.f22637c = z5;
                            cVar.f22636b = str;
                            cVar.f22638d = applicationInfo.loadIcon(packageManager);
                            cVar.f22639e = applicationInfo.loadLabel(packageManager);
                            cVar.f22641g = packageInfo.applicationInfo.targetSdkVersion;
                            cVar.f22642h = packageInfo.requestedPermissions;
                            if (v5 != null) {
                                cVar.f22636b = v5.c();
                                cVar.f22640f = v5.i().length;
                            }
                            cVar.f22643i = (com.github.promeg.pinyinhelper.c.e(cVar.f22639e.charAt(0)) ? com.github.promeg.pinyinhelper.c.g(cVar.f22639e.charAt(0)) : cVar.f22639e.toString()).substring(0, 1).toUpperCase();
                            if (cVar.f22643i.compareTo("A") < 0) {
                                cVar.f22643i = "#";
                            }
                            arrayList.add(cVar);
                        }
                    }
                }
            }
        }
        Collections.sort(arrayList, new Comparator() { // from class: com.loc.va.model.f
            @Override // java.util.Comparator
            public final int compare(Object obj, Object obj2) {
                int m5;
                m5 = h.m((c) obj, (c) obj2);
                return m5;
            }
        });
        return arrayList;
    }

    private List<PackageInfo> k(Context context, File file, List<String> list) {
        ArrayList arrayList = new ArrayList();
        if (list == null) {
            return arrayList;
        }
        Iterator<String> iterator2 = list.iterator2();
        while (iterator2.hasNext()) {
            File[] listFiles = new File(file, iterator2.next()).listFiles();
            if (listFiles != null) {
                for (File file2 : listFiles) {
                    if (file2.getName().toLowerCase().endsWith(".apk")) {
                        PackageInfo packageInfo = null;
                        try {
                            packageInfo = context.getPackageManager().getPackageArchiveInfo(file2.getAbsolutePath(), 4096);
                            packageInfo.applicationInfo.sourceDir = file2.getAbsolutePath();
                            packageInfo.applicationInfo.publicSourceDir = file2.getAbsolutePath();
                        } catch (Exception unused) {
                        }
                        if (packageInfo != null) {
                            arrayList.add(packageInfo);
                        }
                    }
                }
            }
        }
        return arrayList;
    }

    private static boolean l(PackageInfo packageInfo) {
        ApplicationInfo applicationInfo = packageInfo.applicationInfo;
        if (applicationInfo.uid >= 10000) {
            int i5 = applicationInfo.flags;
            if ((i5 & 1) == 0 && (i5 & 128) == 0) {
                return false;
            }
        }
        return true;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static /* synthetic */ int m(c cVar, c cVar2) {
        int compare = Integer.compare(cVar.f22640f, cVar2.f22640f);
        return compare != 0 ? -compare : f22650c.compare(cVar.f22639e, cVar2.f22639e);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ List n(Context context) throws Exception {
        return j(context, context.getPackageManager().getInstalledPackages(4096), true, true);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ List o(Context context, File file) throws Exception {
        return j(context, k(context, file, f22651d), false, false);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ List p() throws Exception {
        ArrayList arrayList = new ArrayList();
        for (InstalledAppInfo installedAppInfo : com.lody.virtual.client.core.j.h().w(0)) {
            if (com.lody.virtual.client.core.j.h().f0(installedAppInfo.f24691a)) {
                r rVar = new r(this.f22653b, installedAppInfo);
                if (com.lody.virtual.client.core.j.h().V(0, installedAppInfo.f24691a)) {
                    arrayList.add(rVar);
                }
                this.f22652a.put(installedAppInfo.f24691a, rVar.f22679d);
                for (int i5 : installedAppInfo.i()) {
                    if (i5 != 0) {
                        arrayList.add(new q(rVar, i5));
                    }
                }
            }
        }
        return arrayList;
    }

    @Override // com.loc.va.model.b
    public boolean a(String str, int i5) {
        return com.lody.virtual.client.core.j.h().H0(str, i5);
    }

    @Override // com.loc.va.model.b
    public org.jdeferred.p<List<c>, Throwable, Void> b(final Context context) {
        return com.loc.va.abs.ui.c.a().l(new Callable() { // from class: com.loc.va.model.e
            @Override // java.util.concurrent.Callable
            public final Object call() {
                List n5;
                n5 = h.this.n(context);
                return n5;
            }
        });
    }

    @Override // com.loc.va.model.b
    public VAppInstallerResult c(AppInfoLite appInfoLite) {
        return com.lody.virtual.client.core.j.h().S(appInfoLite.c(), new VAppInstallerParams());
    }

    @Override // com.loc.va.model.b
    public org.jdeferred.p<List<AppData>, Throwable, Void> d() {
        return com.loc.va.abs.ui.c.a().l(new Callable() { // from class: com.loc.va.model.d
            @Override // java.util.concurrent.Callable
            public final Object call() {
                List p5;
                p5 = h.this.p();
                return p5;
            }
        });
    }

    @Override // com.loc.va.model.b
    public org.jdeferred.p<List<c>, Throwable, Void> e(final Context context, final File file) {
        return com.loc.va.abs.ui.c.a().l(new Callable() { // from class: com.loc.va.model.g
            @Override // java.util.concurrent.Callable
            public final Object call() {
                List o5;
                o5 = h.this.o(context, file);
                return o5;
            }
        });
    }

    @Override // com.loc.va.model.b
    public String getLabel(String str) {
        String str2 = this.f22652a.get(str);
        return str2 == null ? str : str2;
    }
}
