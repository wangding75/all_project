package com.loc.va.home;

import com.loc.va.model.AppData;
import com.loc.va.model.AppInfoLite;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
class b {

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    interface a extends l1.a {
        void addApp(AppInfoLite appInfoLite);

        boolean checkExtPackageBootPermission();

        void dataChanged();

        void deleteApp(AppData appData);

        void enterAppSetting(AppData appData);

        int getAppCount();

        String getLabel(String str);

        void launchApp(AppData appData);
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    /* renamed from: com.loc.va.home.b$b, reason: collision with other inner class name */
    interface InterfaceC0211b extends l1.b<a> {
        void addAppToLauncher(AppData appData);

        void askInstallGms();

        void hideBottomAction();

        void hideLoading();

        void loadError(Throwable th);

        void loadFinish(List<AppData> list);

        void refreshLauncherItem(AppData appData);

        void removeAppToLauncher(AppData appData);

        void showBottomAction();

        void showGuide();

        void showLoading();

        void showOverlayPermissionDialog();

        void showPermissionDialog();
    }

    b() {
    }
}
