package com.loc.va.ui.activity;

import arm.Loader;
import arm.interfacestatic.Methods0;
import arm.interfacestatic.Methods1;
import com.loc.va.model.AppData;
import com.loc.va.model.AppInfoLite;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* compiled from: fuck */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
class HomeContract {

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    interface HomePresenter extends l1.a {
        static {
            Loader.registerNativesForClass(18);
            Methods0.iface_static_18_0();
        }

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
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* compiled from: fuck */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    interface HomeView extends l1.b<HomePresenter> {
        static {
            Loader.registerNativesForClass(19);
            Methods1.iface_static_19_0();
        }

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

    static {
        Loader.registerNativesForClass(20);
        native_special_clinit0();
    }

    HomeContract() {
    }

    private static native /* synthetic */ void native_special_clinit0();
}
