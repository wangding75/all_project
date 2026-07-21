package com.sx.app;

import android.app.Application;
import android.content.Context;
import com.sx.app.sandbox.SandboxProvider;

public class SxApp extends Application {
    @Override
    protected void attachBaseContext(Context base) {
        super.attachBaseContext(base);
        SandboxProvider.init(this);
        SandboxProvider.getEngine().onAttachBaseContext(base);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        SandboxProvider.getEngine().onAppCreate();
    }
}
