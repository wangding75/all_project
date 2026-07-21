package com.sx.app.license;

public final class LicenseConfig {
    // 服务端根地址，通过 BuildConfig 注入，不硬编码
    public static final String BASE_URL = getBuildConfigValue("LICENSE_SERVER_URL", "http://10.0.2.2:8000");
    // 与服务端 SERVER_SECRET 一致（用于签名计算）
    public static final String APP_SECRET = getBuildConfigValue("LICENSE_APP_SECRET", "sx_dev_secret_2026");
    public static final long TIMEOUT_MS = 10_000L;
    public static final String DEV_KEY_PREFIX = "SX-DEV-";

    private LicenseConfig() {}

    private static String getBuildConfigValue(String fieldName, String defaultValue) {
        try {
            Class<?> clazz = Class.forName("com.sx.app.BuildConfig");
            java.lang.reflect.Field field = clazz.getField(fieldName);
            return (String) field.get(null);
        } catch (Exception e) {
            return defaultValue;
        }
    }
}
