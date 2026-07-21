package com.sx.app.license;

import android.util.Log;
import org.json.JSONObject;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * 调用本项目服务端的授权接口
 * 在后台线程中调用，不可在主线程执行
 */
public class SxServerLicenseClient {

    private static final String TAG = "SxServerLicense";

    /** 激活卡密：POST /api/license/activate */
    public static LicenseResult activate(String cardKey, String deviceId) {
        try {
            String sign = sign(cardKey, deviceId, LicenseConfig.APP_SECRET);
            JSONObject body = new JSONObject();
            body.put("card_key",  cardKey);
            body.put("device_id", deviceId);
            body.put("sign",      sign);

            JSONObject resp = post(LicenseConfig.BASE_URL + "/api/license/activate", body.toString());
            if (resp == null) return LicenseResult.fail("网络请求失败，请检查网络后重试");

            int code = resp.getInt("code");
            String msg = resp.optString("msg", "未知错误");
            if (code == 200) {
                JSONObject data = resp.getJSONObject("data");
                return new LicenseResult(true, data.getString("token"),
                        data.getLong("expire_at"), msg);
            }
            return LicenseResult.fail(msg);

        } catch (Exception e) {
            Log.e(TAG, "activate error", e);
            return LicenseResult.fail("网络异常：" + e.getMessage());
        }
    }

    /** 鉴权刷新：GET /api/license/verify */
    public static LicenseResult verify(String token, String deviceId) {
        try {
            String urlStr = LicenseConfig.BASE_URL + "/api/license/verify?device_id=" + deviceId;
            HttpURLConnection conn = (HttpURLConnection) new URL(urlStr).openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("Authorization", "Bearer " + token);
            conn.setConnectTimeout((int) LicenseConfig.TIMEOUT_MS);
            conn.setReadTimeout((int) LicenseConfig.TIMEOUT_MS);

            int httpCode = conn.getResponseCode();
            String respBody = readStream(conn);
            conn.disconnect();

            JSONObject resp = new JSONObject(respBody);
            int code = resp.getInt("code");
            String msg = resp.optString("msg", "");
            if (code == 200) {
                JSONObject data = resp.getJSONObject("data");
                boolean valid = data.optBoolean("valid", false);
                long expireAt = data.optLong("expire_at", 0L);
                return new LicenseResult(valid, token, expireAt, msg);
            }
            return LicenseResult.fail(msg);

        } catch (Exception e) {
            Log.e(TAG, "verify error", e);
            return null; // 网络失败时返回 null，由调用方决定是否使用本地 token
        }
    }

    // ── 私有工具 ──────────────────────────────────────────────────────

    private static String sign(String cardKey, String deviceId, String secret) throws Exception {
        String raw = cardKey + deviceId + secret;
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] bytes = md.digest(raw.getBytes(StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) sb.append(String.format("%02x", b));
        return sb.toString().toUpperCase();
    }

    private static JSONObject post(String urlStr, String jsonBody) {
        try {
            HttpURLConnection conn = (HttpURLConnection) new URL(urlStr).openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setConnectTimeout((int) LicenseConfig.TIMEOUT_MS);
            conn.setReadTimeout((int) LicenseConfig.TIMEOUT_MS);
            conn.setDoOutput(true);

            try (OutputStream os = conn.getOutputStream()) {
                os.write(jsonBody.getBytes(StandardCharsets.UTF_8));
            }
            String body = readStream(conn);
            conn.disconnect();
            return new JSONObject(body);
        } catch (Exception e) {
            Log.e(TAG, "post error", e);
            return null;
        }
    }

    private static String readStream(HttpURLConnection conn) throws Exception {
        BufferedReader reader;
        try {
            reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        } catch (Exception e) {
            reader = new BufferedReader(new InputStreamReader(conn.getErrorStream()));
        }
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) sb.append(line);
        reader.close();
        return sb.toString();
    }
}
