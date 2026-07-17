package com.loc.va.model;

import android.content.Context;
import com.lody.virtual.remote.VAppInstallerResult;
import java.io.File;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public interface b {
    boolean a(String str, int i5);

    org.jdeferred.p<List<c>, Throwable, Void> b(Context context);

    VAppInstallerResult c(AppInfoLite appInfoLite);

    org.jdeferred.p<List<AppData>, Throwable, Void> d();

    org.jdeferred.p<List<c>, Throwable, Void> e(Context context, File file);

    String getLabel(String str);
}
