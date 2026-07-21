package com.sx.app.sandbox;

import android.app.Application;
import com.sx.app.BuildConfig;

public final class SandboxProvider {
    private static SandboxEngine sEngine;

    public static void init(Application app) {
        if (sEngine == null) {
            if ("blackbox".equals(BuildConfig.SANDBOX_ENGINE)) {
                sEngine = new BlackBoxSandboxEngine();
            } else {
                sEngine = new FakeSandboxEngine();
            }
            sEngine.initialize(app);
        }
    }

    public static SandboxEngine getEngine() {
        if (sEngine == null) {
            throw new IllegalStateException("SandboxEngine not initialized");
        }
        return sEngine;
    }
}
