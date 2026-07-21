package com.sx.app.license;

import android.content.Context;
import android.os.Build;
import android.provider.Settings;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * 获取宿主设备真实指纹
 * 必须在宿主主进程调用 —— Hook 层会伪造 AndroidID，沙箱进程内调用会拿到假值
 */
public final class DeviceFingerprint {

    private DeviceFingerprint() {}

    public static String get(Context context) {
        String raw = Settings.Secure.getString(
                context.getContentResolver(), Settings.Secure.ANDROID_ID);
        if (raw == null || raw.isEmpty()) {
            raw = Build.SERIAL;
        }
        if (raw == null || raw.isEmpty()) {
            raw = "unknown_device";
        }
        return sha256(raw).substring(0, 32);
    }

    private static String sha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(input.getBytes());
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            return input; // fallback
        }
    }
}
