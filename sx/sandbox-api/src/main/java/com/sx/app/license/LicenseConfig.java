package com.sx.app.license;

public final class LicenseConfig {
    // Defaults keep library-only tests and emulator development working. The app
    // initializes these values from BuildConfig in SxApp.attachBaseContext().
    public static volatile String BASE_URL = "http://10.0.2.2:8000";
    public static volatile String APP_SECRET = "sx_dev_secret_2026";
    public static volatile String TOKEN_PUBLIC_KEY = "";
    public static volatile String DEV_HMAC_SECRET = "sx-dev-hmac-secret-change-me";
    public static final long TIMEOUT_MS = 10_000L;
    public static final String DEV_KEY_PREFIX = "SX-DEV-";

    private LicenseConfig() {}

    public static void configure(String baseUrl, String appSecret,
                                 String tokenPublicKey, String devHmacSecret) {
        if (baseUrl != null && !baseUrl.trim().isEmpty()) {
            BASE_URL = trimTrailingSlash(baseUrl.trim());
        }
        if (appSecret != null && !appSecret.isEmpty()) {
            APP_SECRET = appSecret;
        }
        if (tokenPublicKey != null && !tokenPublicKey.trim().isEmpty()) {
            TOKEN_PUBLIC_KEY = tokenPublicKey.replaceAll("\\s+", "");
        }
        if (devHmacSecret != null && !devHmacSecret.isEmpty()) {
            DEV_HMAC_SECRET = devHmacSecret;
        }
    }

    private static String trimTrailingSlash(String value) {
        while (value.endsWith("/") && value.length() > 1) {
            value = value.substring(0, value.length() - 1);
        }
        return value;
    }
}
