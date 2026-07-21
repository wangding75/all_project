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

    public static String getDeviceId(Context context) {
        return DeviceIdGenerator.uniqueDeviceFingerprint(context);
    }

    public static boolean isActivated(Context context) {
        LicenseInfo info = load(context);
        if (info == null || TextUtils.isEmpty(info.token)) {
            return false;
        }
        return verifyToken(context, info.token);
    }

    public static LicenseInfo load(Context context) {
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
        cardKey = cardKey.trim().toUpperCase(Locale.US);
        long expireAt = parseDevCard(cardKey);
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
            o.put("card", cardKey);
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
