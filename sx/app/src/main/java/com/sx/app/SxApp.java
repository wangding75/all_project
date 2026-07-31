package com.sx.app;

import android.app.Application;
import android.content.Context;
import com.sx.app.license.LicenseConfig;
import com.sx.app.sandbox.SandboxProvider;

public class SxApp extends Application {
    @Override
    protected void attachBaseContext(Context base) {
        super.attachBaseContext(base);
        // Use direct BuildConfig references so R8 cannot remove or rename fields
        // that were previously reached only through reflection.
        LicenseConfig.configure(
                BuildConfig.LICENSE_SERVER_URL,
                BuildConfig.LICENSE_APP_SECRET,
                BuildConfig.LICENSE_TOKEN_PUBLIC_KEY,
                BuildConfig.LICENSE_HMAC_SECRET);
        SandboxProvider.init(this);
        SandboxProvider.getEngine().onAttachBaseContext(base);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        SandboxProvider.getEngine().onAppCreate();
        com.sx.app.util.TimeGuard.refreshNetworkTimeAsync(this);
    }
}
