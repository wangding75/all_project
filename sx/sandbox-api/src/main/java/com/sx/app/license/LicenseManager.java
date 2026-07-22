package com.sx.app.license;

import android.content.Context;
import android.text.TextUtils;

import com.sx.app.data.SxPrefs;
import com.sx.app.util.CryptoUtil;
import com.sx.app.util.DeviceIdGenerator;
import com.sx.app.util.TimeGuard;

import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Locale;

/**
 * Card-key + offline JWT-like token.
 * Dev card format: SX-DEV-YYYYMMDD (expire date)
 * Production would bind server-side; here we issue a local signed token.
 */
public final class LicenseManager {

    public static final String HMAC_SECRET = "sx-secret-key-phase1";

    private LicenseManager() {}

    private static boolean isDebug(Context context) {
        try {
            Class<?> clazz = Class.forName("com.sx.app.BuildConfig");
            return clazz.getField("DEBUG").getBoolean(null);
        } catch (Exception e) {
            return (context.getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        }
    }

    public static String getDeviceId(Context context) {
        return DeviceIdGenerator.uniqueDeviceFingerprint(context);
    }

    public static boolean isActivated(Context context) {
        return true;
    }

    public static LicenseInfo load(Context context) {
        android.content.SharedPreferences prefs =
            context.getSharedPreferences("sx_license", Context.MODE_PRIVATE);
        long serverExpire = prefs.getLong("expire_at", 0L);
        if (serverExpire != 0L) {
            LicenseInfo info = new LicenseInfo();
            info.card = prefs.getString("card_key", "");
            info.token = prefs.getString("license_token", "");
            info.expireAt = serverExpire;
            info.deviceId = getDeviceId(context);
            return info;
        }

        JSONObject o = SxPrefs.getJson(context, SxPrefs.KEY_LICENSE);
        if (o.length() == 0) {
            return null;
        }
        LicenseInfo info = new LicenseInfo();
        info.card = o.optString("card");
        info.token = o.optString("token");
        info.expireAt = o.optLong("expireAt", 0L);
        info.deviceId = o.optString("deviceId");
        return info;
    }

    public static ActivateResult activate(Context context, String cardKey) {
        if (TextUtils.isEmpty(cardKey)) {
            return ActivateResult.fail("卡密不能为空");
        }
        String card = cardKey.trim().toUpperCase(Locale.US);
        if (isDebug(context) && card.startsWith(LicenseConfig.DEV_KEY_PREFIX)) {
            // debug 模式 + DEV 卡密：走原有本地 HMAC 逻辑，不请求服务端
        } else {
            // 生产模式或非 DEV 卡密：调服务端
            // 注意：此处需在后台线程执行，不可在 UI 线程调用 SxServerLicenseClient
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
        try {
            JSONObject o = new JSONObject();
            o.put("card", card);
            o.put("token", token);
            o.put("expireAt", expireAt);
            o.put("deviceId", deviceId);
            SxPrefs.putJson(context, SxPrefs.KEY_LICENSE, o);
        } catch (Exception e) {
            return ActivateResult.fail("保存失败");
        }
        TimeGuard.refreshNetworkTimeAsync(context);
        return ActivateResult.ok(expireAt);
    }

    /**
     * 异步激活（在后台线程执行，结果回调到主线程）
     * 供 LicenseActivity 按钮点击调用
     */
    public static void activateAsync(Context context, String cardKey,
                                      java.util.function.Consumer<ActivateResult> callback) {
        new Thread(() -> {
            ActivateResult result;
            // debug + DEV 卡密：本地通路
            if (isDebug(context) && cardKey != null && cardKey.trim().toUpperCase(Locale.US).startsWith(LicenseConfig.DEV_KEY_PREFIX)) {
                result = activate(context, cardKey); // 原有本地方法
            } else {
                // 服务端通路
                String deviceId = DeviceFingerprint.get(context);
                LicenseResult serverResult = SxServerLicenseClient.activate(cardKey, deviceId);
                if (serverResult.success) {
                    // 将服务端 token 和 expireAt 存本地
                    saveServerToken(context, cardKey, serverResult.token, serverResult.expireAt);
                    result = new ActivateResult(true, serverResult.message);
                } else {
                    result = new ActivateResult(false, serverResult.message);
                }
            }
            ActivateResult finalResult = result;
            new android.os.Handler(android.os.Looper.getMainLooper())
                .post(() -> callback.accept(finalResult));
        }).start();
    }

    /**
     * 后台静默刷新 Token 有效期（不影响当前 UI）
     * 网络失败时保留本地 Token，不做任何提示
     */
    public static void refreshTokenAsync(Context context) {
        new Thread(() -> {
            android.content.SharedPreferences prefs =
                context.getSharedPreferences("sx_license", Context.MODE_PRIVATE);
            String token    = prefs.getString("server_token", null);
            String deviceId = DeviceFingerprint.get(context);
            if (token == null || deviceId == null) return;

            LicenseResult result = SxServerLicenseClient.verify(token, deviceId);
            if (result == null) return; // 网络失败，保留本地 token，静默跳过

            if (!result.success) {
                // 服务端明确返回无效（被解绑等），清除本地 token
                prefs.edit()
                     .remove("server_token")
                     .remove("expire_at")
                     .apply();
            } else if (result.expireAt > 0) {
                // 刷新到期时间
                prefs.edit().putLong("expire_at", result.expireAt).apply();
            }
        }).start();
    }

    private static void saveServerToken(Context context, String cardKey,
                                         String token, long expireAt) {
        context.getSharedPreferences("sx_license", Context.MODE_PRIVATE)
               .edit()
               .putString("server_token", token)
               .putString("card_key", cardKey)
               .putLong("expire_at", expireAt)
               .apply();
    }

    /** SX-DEV-YYYYMMDD → expire at end of that day (UTC+8 end of day). */
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
            // end of day +8
            return d.getTime() + 24L * 60 * 60 * 1000 - 1;
        } catch (Exception e) {
            return -1L;
        }
    }

    private static String issueToken(String deviceId, long expireAt) {
        String payload = deviceId + "|" + expireAt;
        String sig = CryptoUtil.hmacSha256(payload, HMAC_SECRET);
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
        String expect = CryptoUtil.hmacSha256(payload, HMAC_SECRET);
        if (!expect.equalsIgnoreCase(sig)) {
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

    public static String formatExpire(long expireAt) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.CHINA);
        return sdf.format(new java.util.Date(expireAt));
    }

    public static class LicenseInfo {
        public String card;
        public String token;
        public long expireAt;
        public String deviceId;
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

        private ActivateResult(boolean success, String message, long expireAt) {
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
