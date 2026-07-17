package com.custom.spoofer.utils;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.text.TextUtils;
import android.util.Base64;
import java.io.UnsupportedEncodingException;
import java.lang.reflect.Method;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.UUID;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import org.json.JSONException;
import org.json.JSONObject;

public class MyUtil {

    private static final String IV_KEY = "1201230125462244"; // Static IV vector from XH

    public static String aesEncrypt(String data, String charset, String transformation, String secretKey, String iv) {
        try {
            Cipher cipher = Cipher.getInstance(transformation);
            SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(charset), "AES");
            IvParameterSpec ivParameterSpec = new IvParameterSpec(iv.getBytes(charset));
            if (transformation.contains("CBC")) {
                cipher.init(Cipher.ENCRYPT_MODE, secretKeySpec, ivParameterSpec);
            } else {
                cipher.init(Cipher.ENCRYPT_MODE, secretKeySpec);
            }
            byte[] encrypted = cipher.doFinal(data.getBytes(charset));
            return new String(Base64.encode(encrypted, Base64.DEFAULT)).trim().replaceAll("\n", "").replaceAll("\r", "");
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String aesDecrypt(String encryptedData, String charset, String transformation, String secretKey, String iv) {
        try {
            SecretKeySpec secretKeySpec = new SecretKeySpec(secretKey.getBytes(charset), "AES");
            Cipher cipher = Cipher.getInstance(transformation);
            IvParameterSpec ivParameterSpec = new IvParameterSpec(iv.getBytes(charset));
            if (transformation.contains("CBC")) {
                cipher.init(Cipher.DECRYPT_MODE, secretKeySpec, ivParameterSpec);
            } else {
                cipher.init(Cipher.DECRYPT_MODE, secretKeySpec);
            }
            byte[] decoded = Base64.decode(encryptedData, Base64.DEFAULT);
            return new String(cipher.doFinal(decoded), charset);
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String aesEncrypt_iv(String data, String secretKey) {
        return aesEncrypt(data, "utf-8", "AES/CBC/PKCS5Padding", secretKey, IV_KEY);
    }

    public static String aesDecrypt_iv(String encryptedData, String secretKey) {
        return aesDecrypt(encryptedData, "utf-8", "AES/CBC/PKCS5Padding", secretKey, IV_KEY);
    }

    public static String b_dec(String str) {
        try {
            return new String(Base64.decode(str, Base64.DEFAULT)).trim();
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String b_enc(String str) {
        try {
            return new String(Base64.encode(str.getBytes(), Base64.DEFAULT)).trim();
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    /**
     * Reflectively query device IMEI (slots 0 and 1) on legacy Android APIs.
     */
    public static String getDeviceImei(Context context) {
        if (Build.VERSION.SDK_INT > 28) {
            return "";
        }
        TelephonyManager telephonyManager = (TelephonyManager) context.getSystemService(Context.TELEPHONY_SERVICE);
        try {
            Method method = telephonyManager.getClass().getMethod("getImei", Integer.TYPE);
            String imei1 = (String) method.invoke(telephonyManager, 0);
            String imei2 = (String) method.invoke(telephonyManager, 1);
            if (TextUtils.isEmpty(imei1)) {
                return telephonyManager.getDeviceId();
            }
            if (!TextUtils.isEmpty(imei2)) {
                return imei1.compareTo(imei2) <= 0 ? imei1 : imei2;
            }
            return imei1;
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String getDeviceSerial() {
        try {
            Method declaredMethod = Class.forName("android.os.Build").getDeclaredMethod("getString", String.class);
            if (!declaredMethod.isAccessible()) {
                declaredMethod.setAccessible(true);
            }
            return (String) declaredMethod.invoke(new Build(), "ro.serialno");
        } catch (Exception e) {
            e.printStackTrace();
            return "unknown";
        }
    }

    public static String md5(byte[] data) {
        try {
            MessageDigest messageDigest = MessageDigest.getInstance("MD5");
            messageDigest.update(data);
            return bytesToHex(messageDigest.digest());
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
            return "";
        }
    }

    public static String bytesToHex(byte[] bytes) {
        if (bytes == null) {
            return "";
        }
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            String hex = Integer.toString(b & 255, 16);
            if (hex.length() == 1) {
                sb.append("0");
            }
            sb.append(hex);
        }
        return sb.toString();
    }

    /**
     * Generate unique device UUID based on Android ID and Hardware specs.
     */
    public static String getUniqueDeviceId(Context context) {
        String imei = getDeviceImei(context);
        if (imei != null && imei.length() > 4) {
            return imei;
        }
        String androidId = Settings.System.getString(context.getContentResolver(), Settings.System.ANDROID_ID);
        StringBuilder sb = new StringBuilder();
        sb.append(androidId);
        if (Build.VERSION.SDK_INT >= 26) {
            sb.append(getDeviceSerial());
        } else {
            sb.append(Build.SERIAL);
        }
        sb.append(Build.BRAND);
        sb.append(Build.MODEL);
        return md5(sb.toString().getBytes()).substring(8, 24);
    }

    public static String getConfig(Context context, String key) {
        return context.getSharedPreferences("DEFAULT", Context.MODE_PRIVATE).getString(key, "");
    }

    public static void setConfig(Context context, String key, String value) {
        SharedPreferences.Editor edit = context.getSharedPreferences("DEFAULT", Context.MODE_PRIVATE).edit();
        edit.putString(key, value);
        edit.apply();
    }

    public static String getJsonConfig(Context context, String subKey) {
        String config = getConfig(context, "CORE");
        if (TextUtils.isEmpty(config)) {
            return "";
        }
        String decoded = b_dec(config);
        if (TextUtils.isEmpty(decoded)) {
            return "";
        }
        try {
            return new JSONObject(decoded).getString(subKey);
        } catch (JSONException e) {
            e.printStackTrace();
            return "";
        }
    }

    public static void setJsonConfig(Context context, String subKey, String value) {
        String config = getConfig(context, "CORE");
        try {
            JSONObject jsonObject;
            if (TextUtils.isEmpty(config)) {
                jsonObject = new JSONObject();
            } else {
                jsonObject = new JSONObject(b_dec(config));
            }
            jsonObject.put(subKey, value);
            setConfig(context, "CORE", b_enc(jsonObject.toString()));
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }
}
