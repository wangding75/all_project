package com.sx.app.license;

import android.content.Context;
import android.text.TextUtils;

import com.sx.app.data.SxPrefs;
import com.sx.app.util.CryptoUtil;
import com.sx.app.util.TimeGuard;

import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Locale;

/**
 * Card-key license manager.
 * <ul>
 *   <li>Debug + SX-DEV-YYYYMMDD: local HMAC token, stored in {@link SxPrefs#KEY_LICENSE}</li>
 *   <li>Otherwise: server activate/verify, same JSON schema in {@link SxPrefs#KEY_LICENSE}</li>
 * </ul>
 * Device id is always {@link DeviceFingerprint#get(Context)} (host process only).
 */
public final class LicenseManager {

    private static final String SOURCE_DEV = "dev";
    private static final String SOURCE_SERVER = "server";
    /** expireAt == -1 means permanent server license */
    public static final long EXPIRE_PERMANENT = -1L;

    private LicenseManager() {}

    private static boolean isDebug(Context context) {
        try {
            Class<?> clazz = Class.forName("com.sx.app.BuildConfig");
            return clazz.getField("DEBUG").getBoolean(null);
        } catch (Exception e) {
            return (context.getApplicationInfo().flags
                    & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        }
    }

    /** HMAC secret from app BuildConfig when available (debug-only local tokens). */
    private static String hmacSecret() {
        return LicenseConfig.DEV_HMAC_SECRET;
    }

    public static String getDeviceId(Context context) {
        return DeviceFingerprint.get(context);
    }

    public static boolean isActivated(Context context) {
        if (isDebug(context)) {
            return true;
        }
        LicenseInfo info = load(context);
        if ((info == null || TextUtils.isEmpty(info.token)) && isDebug(context)) {
            try {
                activate(context, "SX-DEV-20291231");
                info = load(context);
            } catch (Throwable ignored) {
            }
        }
        if (info == null || TextUtils.isEmpty(info.token)) {
            return false;
        }
        if (!getDeviceId(context).equals(info.deviceId)) {
            return false;
        }
        if (SOURCE_DEV.equals(info.source)) {
            long now = TimeGuard.getTrustedNow(context);
            if (info.expireAt <= 0 || now >= info.expireAt) {
                return false;
            }
            return verifyToken(context, info.token);
        }
        return SOURCE_SERVER.equals(info.source) && verifyServerToken(context, info);
    }

    /**
     * Resolve activation without blocking the UI. Current RSA tokens are
     * accepted immediately. A legacy server token gets one online verification
     * attempt so the server can replace it with an RSA-signed token.
     */
    public static void checkActivationAsync(
            Context context, java.util.function.Consumer<Boolean> callback) {
        final Context appCtx = context.getApplicationContext();
        if (isActivated(appCtx)) {
            postActivationResult(callback, true);
            refreshTokenAsync(appCtx);
            return;
        }

        final LicenseInfo info = load(appCtx);
        boolean canMigrate = info != null
                && SOURCE_SERVER.equals(info.source)
                && !TextUtils.isEmpty(info.token)
                && getDeviceId(appCtx).equals(info.deviceId)
                && (info.expireAt == EXPIRE_PERMANENT
                    || (info.expireAt > 0
                        && TimeGuard.getTrustedNow(appCtx) < info.expireAt));
        if (!canMigrate) {
            postActivationResult(callback, false);
            return;
        }

        new Thread(() -> {
            boolean activated = false;
            try {
                LicenseResult result = SxServerLicenseClient.verify(
                        info.token, getDeviceId(appCtx));
                if (result != null && result.success
                        && !TextUtils.isEmpty(result.token)) {
                    persistLicense(appCtx, SOURCE_SERVER, info.card, result.token,
                            result.expireAt, getDeviceId(appCtx));
                    activated = isActivated(appCtx);
                } else if (result != null) {
                    clearLicense(appCtx);
                }
            } catch (Exception ignored) {
            }
            postActivationResult(callback, activated);
        }, "sx-license-migrate").start();
    }

    private static void postActivationResult(
            java.util.function.Consumer<Boolean> callback, boolean activated) {
        if (callback == null) {
            return;
        }
        new android.os.Handler(android.os.Looper.getMainLooper())
                .post(() -> callback.accept(activated));
    }

    public static LicenseInfo load(Context context) {
        LicenseInfo info = new LicenseInfo();
        info.deviceId = getDeviceId(context);
        try {
            JSONObject o = SxPrefs.getJson(context, SxPrefs.KEY_LICENSE);
            if (o == null || o.length() == 0) {
                // Migrate legacy sx_license SharedPreferences (server path before unify)
                migrateLegacyServerPrefs(context);
                o = SxPrefs.getJson(context, SxPrefs.KEY_LICENSE);
            }
            if (o == null || o.length() == 0) {
                return info;
            }
            info.card = o.optString("card", "");
            info.token = o.optString("token", "");
            info.expireAt = o.optLong("expireAt", 0L);
            info.deviceId = o.optString("deviceId", info.deviceId);
            info.source = o.optString("source",
                    TextUtils.isEmpty(info.token) ? "" :
                            (info.token.contains(".") && !info.token.startsWith("ey")
                                    ? SOURCE_DEV : SOURCE_SERVER));
        } catch (Exception ignored) {
        }
        return info;
    }

    private static void migrateLegacyServerPrefs(Context context) {
        try {
            android.content.SharedPreferences legacy =
                    context.getSharedPreferences("sx_license", Context.MODE_PRIVATE);
            String token = legacy.getString("server_token", null);
            if (TextUtils.isEmpty(token)) {
                return;
            }
            String card = legacy.getString("card_key", "");
            long expireAt = legacy.getLong("expire_at", 0L);
            String deviceId = getDeviceId(context);
            persistLicense(context, SOURCE_SERVER, card, token, expireAt, deviceId);
            legacy.edit().clear().apply();
        } catch (Exception ignored) {
        }
    }

    private static void persistLicense(Context context, String source, String card,
                                       String token, long expireAt, String deviceId) {
        try {
            JSONObject o = new JSONObject();
            o.put("source", source == null ? "" : source);
            o.put("card", card == null ? "" : card);
            o.put("token", token == null ? "" : token);
            o.put("expireAt", expireAt);
            o.put("deviceId", deviceId == null ? "" : deviceId);
            SxPrefs.putJson(context, SxPrefs.KEY_LICENSE, o);
        } catch (Exception ignored) {
        }
    }

    public static ActivateResult activate(Context context, String cardKey) {
        if (TextUtils.isEmpty(cardKey)) {
            return ActivateResult.fail("卡密不能为空");
        }
        String card = cardKey.trim().toUpperCase(Locale.US);
        if (!(isDebug(context) && card.startsWith(LicenseConfig.DEV_KEY_PREFIX))) {
            throw new IllegalStateException("请通过 activateAsync() 在后台线程调用");
        }

        long expireAt = parseDevCard(card);
        if (expireAt <= 0) {
            return ActivateResult.fail("卡密无效");
        }
        long now = TimeGuard.getTrustedNow(context);
        if (now >= expireAt) {
            return ActivateResult.fail("卡密已过期");
        }
        String deviceId = getDeviceId(context);
        String token = issueToken(deviceId, expireAt);
        persistLicense(context, SOURCE_DEV, card, token, expireAt, deviceId);
        TimeGuard.refreshNetworkTimeAsync(context);
        return ActivateResult.ok(expireAt);
    }

    /**
     * Async activate (worker thread), callback on main thread.
     */
    public static void activateAsync(Context context, String cardKey,
                                     java.util.function.Consumer<ActivateResult> callback) {
        final Context appCtx = context.getApplicationContext();
        new Thread(() -> {
            ActivateResult result;
            try {
                String normalized = cardKey == null ? "" : cardKey.trim().toUpperCase(Locale.US);
                if (isDebug(appCtx) && normalized.startsWith(LicenseConfig.DEV_KEY_PREFIX)) {
                    result = activate(appCtx, cardKey);
                } else {
                    String deviceId = getDeviceId(appCtx);
                    LicenseResult serverResult = SxServerLicenseClient.activate(cardKey, deviceId);
                    if (serverResult.success) {
                        persistLicense(appCtx, SOURCE_SERVER,
                                cardKey == null ? "" : cardKey.trim(),
                                serverResult.token,
                                serverResult.expireAt,
                                deviceId);
                        if (!isActivated(appCtx)) {
                            clearLicense(appCtx);
                            result = ActivateResult.fail(
                                    "服务端授权签名校验失败，请检查客户端公钥配置");
                        } else {
                            result = ActivateResult.ok(serverResult.expireAt);
                            if (!TextUtils.isEmpty(serverResult.message)
                                    && !"激活成功".equals(serverResult.message)) {
                                result = new ActivateResult(
                                        true, serverResult.message, serverResult.expireAt);
                            }
                        }
                    } else {
                        result = ActivateResult.fail(
                                serverResult.message != null ? serverResult.message : "激活失败");
                    }
                }
            } catch (Exception e) {
                result = ActivateResult.fail(
                        e.getMessage() != null ? e.getMessage() : "激活异常");
            }
            ActivateResult finalResult = result;
            new android.os.Handler(android.os.Looper.getMainLooper())
                    .post(() -> {
                        if (callback != null) {
                            callback.accept(finalResult);
                        }
                    });
        }, "sx-license-activate").start();
    }

    /**
     * Background silent refresh for server tokens. Network failure keeps local token.
     */
    public static void refreshTokenAsync(Context context) {
        final Context appCtx = context.getApplicationContext();
        new Thread(() -> {
            try {
                LicenseInfo info = load(appCtx);
                if (info == null || TextUtils.isEmpty(info.token)) {
                    return;
                }
                if (SOURCE_DEV.equals(info.source)) {
                    // Local DEV: nothing to refresh online
                    return;
                }
                String deviceId = getDeviceId(appCtx);
                LicenseResult result = SxServerLicenseClient.verify(info.token, deviceId);
                if (result == null) {
                    return; // network failure
                }
                if (!result.success) {
                    clearLicense(appCtx);
                } else if (result.expireAt != 0) {
                    String refreshedToken = TextUtils.isEmpty(result.token)
                            ? info.token : result.token;
                    persistLicense(appCtx, SOURCE_SERVER, info.card, refreshedToken,
                            result.expireAt, deviceId);
                }
            } catch (Exception ignored) {
            }
        }, "sx-license-refresh").start();
    }

    public static void clearLicense(Context context) {
        SxPrefs.get(context).edit().remove(SxPrefs.KEY_LICENSE).apply();
        try {
            context.getSharedPreferences("sx_license", Context.MODE_PRIVATE)
                    .edit().clear().apply();
        } catch (Exception ignored) {
        }
    }

    /** SX-DEV-YYYYMMDD → expire at end of that day (UTC, +24h-1ms from midnight parse). */
    private static long parseDevCard(String card) {
        if (!card.startsWith("SX-DEV-") || card.length() < 15) {
            return -1L;
        }
        String ymd = card.substring(7);
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd", Locale.US);
            sdf.setLenient(false);
            java.util.Date d = sdf.parse(ymd);
            if (d == null) {
                return -1L;
            }
            return d.getTime() + 24L * 60 * 60 * 1000 - 1;
        } catch (Exception e) {
            return -1L;
        }
    }

    private static String issueToken(String deviceId, long expireAt) {
        String payload = deviceId + "|" + expireAt;
        String sig = CryptoUtil.hmacSha256(payload, hmacSecret());
        if (TextUtils.isEmpty(sig)) {
            return "";
        }
        return CryptoUtil.b64Encode(payload) + "." + sig;
    }

    public static boolean verifyToken(Context context, String token) {
        if (TextUtils.isEmpty(token) || !token.contains(".")) {
            return false;
        }
        int idx = token.lastIndexOf('.');
        String payloadB64 = token.substring(0, idx);
        String sig = token.substring(idx + 1);
        String payload = CryptoUtil.b64Decode(payloadB64);
        if (TextUtils.isEmpty(payload) || !payload.contains("|")) {
            return false;
        }
        String expect = CryptoUtil.hmacSha256(payload, hmacSecret());
        if (TextUtils.isEmpty(expect) || !CryptoUtil.constantTimeEquals(expect, sig)) {
            return false;
        }
        String[] parts = payload.split("\\|");
        if (parts.length != 2) {
            return false;
        }
        String deviceId = parts[0];
        long expireAt;
        try {
            expireAt = Long.parseLong(parts[1]);
        } catch (Exception e) {
            return false;
        }
        if (!deviceId.equals(getDeviceId(context))) {
            return false;
        }
        long now = TimeGuard.getTrustedNow(context);
        return now < expireAt;
    }

    private static boolean verifyServerToken(Context context, LicenseInfo info) {
        if (info == null || TextUtils.isEmpty(info.token)
                || TextUtils.isEmpty(LicenseConfig.TOKEN_PUBLIC_KEY)) {
            return false;
        }
        int idx = info.token.lastIndexOf('.');
        if (idx <= 0 || idx >= info.token.length() - 1) {
            return false;
        }
        String payloadB64 = info.token.substring(0, idx);
        String signature = info.token.substring(idx + 1);
        if (!CryptoUtil.verifyRsaSha256(
                payloadB64, signature, LicenseConfig.TOKEN_PUBLIC_KEY)) {
            return false;
        }
        try {
            JSONObject payload = new JSONObject(CryptoUtil.b64UrlDecode(payloadB64));
            String deviceId = payload.optString("device_id", "");
            String card = payload.optString("card_key", "");
            long expireAt = payload.optLong("expire_at", 0L);
            if (!getDeviceId(context).equals(deviceId)
                    || !deviceId.equals(info.deviceId)
                    || expireAt != info.expireAt
                    || (!TextUtils.isEmpty(info.card) && !info.card.equals(card))) {
                return false;
            }
            return expireAt == EXPIRE_PERMANENT
                    || (expireAt > 0 && TimeGuard.getTrustedNow(context) < expireAt);
        } catch (Exception e) {
            return false;
        }
    }

    public static String formatExpire(long expireAt) {
        if (expireAt == EXPIRE_PERMANENT) {
            return "永久";
        }
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.CHINA);
        return sdf.format(new java.util.Date(expireAt));
    }

    public static class LicenseInfo {
        public String card = "";
        public String token = "";
        public long expireAt;
        public String deviceId = "";
        public String source = "";
    }

    public static class ActivateResult {
        public final boolean success;
        public final String message;
        public final long expireAt;

        public ActivateResult(boolean success, String message) {
            this.success = success;
            this.message = message;
            this.expireAt = 0L;
        }

        public ActivateResult(boolean success, String message, long expireAt) {
            this.success = success;
            this.message = message;
            this.expireAt = expireAt;
        }

        public static ActivateResult ok(long expireAt) {
            return new ActivateResult(true, "激活成功", expireAt);
        }

        public static ActivateResult fail(String msg) {
            return new ActivateResult(false, msg, 0L);
        }
    }
}
