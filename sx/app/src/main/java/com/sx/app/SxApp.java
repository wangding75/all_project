package com.sx.app;

import android.app.Application;
import com.sx.app.sandbox.SandboxProvider;

public class SxApp extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        SandboxProvider.init(this);
    }
}
