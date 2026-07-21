package com.sx.app.util;

import java.util.Locale;
import java.util.Random;
import java.util.UUID;

/** Generators for plausible device / network identifiers. */
public final class DeviceIdGenerator {

    private static final Random R = new Random();

    private DeviceIdGenerator() {}

    public static class DeviceBundle {
        public String brand;
        public String model;
        public String manufacturer;
        public String board;
        public String serial;
        public String imei;
        public String meid;
        public String androidId;
        public String phoneNumber;
        public String imsi;
        public String iccid;
        public String operatorName;
    }

    private static final String[][] DEVICES = {
            {"Xiaomi", "Xiaomi", "2211133C", "taro"},
            {"HUAWEI", "HUAWEI", "VIC-AN00", "VIC"},
            {"OPPO", "OPPO", "PHQ110", "OP4E75L1"},
            {"vivo", "vivo", "V2243A", "SM8450"},
            {"samsung", "samsung", "SM-S9180", "s5e9925"},
            {"OnePlus", "OnePlus", "GM1910", "msmnile"},
            {"realme", "realme", "RMX3706", "sm6450"},
    };

    private static final String[][] OPERATORS = {
            {"46000", "中国移动", "898600"},
            {"46001", "中国联通", "898601"},
            {"46002", "中国移动", "898600"},
            {"46003", "中国电信", "898603"},
            {"46007", "中国移动", "898600"},
            {"46011", "中国电信", "898603"},
    };

    public static DeviceBundle randomBundle() {
        DeviceBundle b = new DeviceBundle();
        String[] d = DEVICES[R.nextInt(DEVICES.length)];
        b.brand = d[0];
        b.manufacturer = d[1];
        b.model = d[2];
        b.board = d[3];
        b.serial = randomAlphaNum(12);
        b.imei = generateImei();
        b.meid = randomHex(14).toUpperCase(Locale.US);
        b.androidId = randomHex(16);
        b.phoneNumber = "1" + (3 + R.nextInt(7)) + String.format(Locale.US, "%09d", R.nextInt(1_000_000_000));
        String[] op = OPERATORS[R.nextInt(OPERATORS.length)];
        b.imsi = op[0] + String.format(Locale.US, "%010d", Math.abs(R.nextLong()) % 10_000_000_000L);
        b.iccid = op[2] + String.format(Locale.US, "%014d", Math.abs(R.nextLong()) % 100_000_000_000_000L);
        b.operatorName = op[1];
        return b;
    }

    public static String generateImei() {
        StringBuilder sb = new StringBuilder(14);
        sb.append("86");
        for (int i = 0; i < 12; i++) {
            sb.append(R.nextInt(10));
        }
        int check = luhnCheckDigit(sb.toString());
        return sb.append(check).toString();
    }

    public static int luhnCheckDigit(String number) {
        int sum = 0;
        for (int i = 0; i < number.length(); i++) {
            int digit = number.charAt(i) - '0';
            if (i % 2 == 1) {
                digit *= 2;
                if (digit > 9) {
                    digit -= 9;
                }
            }
            sum += digit;
        }
        return (10 - (sum % 10)) % 10;
    }

    public static String randomMac() {
        byte[] mac = new byte[6];
        R.nextBytes(mac);
        mac[0] = (byte) ((mac[0] | 0x02) & 0xFE);
        return String.format(Locale.US, "%02x:%02x:%02x:%02x:%02x:%02x",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    }

    public static String randomHex(int len) {
        StringBuilder sb = new StringBuilder(len);
        for (int i = 0; i < len; i++) {
            sb.append(Integer.toHexString(R.nextInt(16)));
        }
        return sb.toString();
    }

    public static String randomAlpha(int len) {
        final String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        StringBuilder sb = new StringBuilder(len);
        for (int i = 0; i < len; i++) {
            sb.append(chars.charAt(R.nextInt(chars.length())));
        }
        return sb.toString();
    }

    public static String randomAlphaNum(int len) {
        final String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        StringBuilder sb = new StringBuilder(len);
        for (int i = 0; i < len; i++) {
            sb.append(chars.charAt(R.nextInt(chars.length())));
        }
        return sb.toString();
    }

    public static String uniqueDeviceFingerprint(android.content.Context context) {
        String androidId = android.provider.Settings.Secure.getString(
                context.getContentResolver(),
                android.provider.Settings.Secure.ANDROID_ID);
        String seed = (androidId == null ? "unknown" : androidId)
                + android.os.Build.BRAND
                + android.os.Build.MODEL
                + android.os.Build.FINGERPRINT;
        try {
            java.security.MessageDigest md = java.security.MessageDigest.getInstance("SHA-256");
            byte[] dig = md.digest(seed.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 8; i++) {
                sb.append(String.format(Locale.US, "%02x", dig[i]));
            }
            return sb.toString();
        } catch (Exception e) {
            return UUID.randomUUID().toString().replace("-", "").substring(0, 16);
        }
    }
}
