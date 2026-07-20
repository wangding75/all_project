package com.sx.app.sandbox;

import android.app.Application;

public final class SandboxProvider {
    private static SandboxEngine sEngine;

    public static void init(Application app) {
        if (sEngine == null) {
            sEngine = new FakeSandboxEngine();
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
