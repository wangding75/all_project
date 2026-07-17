package com.loc.va.utils;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.text.TextUtils;
import android.util.Base64;
import java.io.UnsupportedEncodingException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.URLEncoder;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.UUID;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class MyUtil {
    

    

    public static String aesDecrypt(String str, String str2, String str3, String str4, String str5) {
        try {
            SecretKeySpec secretKeySpec = new SecretKeySpec(str4.getBytes(str2), "AES");
            Cipher cipher = Cipher.getInstance(str3);
            IvParameterSpec ivParameterSpec = new IvParameterSpec(str5.getBytes(str2));
            if (str3.contains("CBC")) {
                cipher.init(2, secretKeySpec, ivParameterSpec);
            } else {
                cipher.init(2, secretKeySpec);
            }
            return new String(cipher.doFinal(Base64.decode(str, 0)), str2);
        } catch (Exception e6) {
            e6.printStackTrace();
            return "";
        }
    }

    public static String aesDecrypt_iv(String str, String str2) {
        return aesDecrypt(str, "utf-8", "AES/CBC/PKCS5Padding", str2, "1201230125462244");
    }

    public static String aesEncrypt(String str, String str2, String str3, String str4, String str5) {
        try {
            Cipher cipher = Cipher.getInstance(str3);
            SecretKeySpec secretKeySpec = new SecretKeySpec(str4.getBytes(str2), "AES");
            IvParameterSpec ivParameterSpec = new IvParameterSpec(str5.getBytes(str2));
            if (str3.contains("CBC")) {
                cipher.init(1, secretKeySpec, ivParameterSpec);
            } else {
                cipher.init(1, secretKeySpec);
            }
            return new String(Base64.encode(cipher.doFinal(str.getBytes(str2)), 0)).trim().replaceAll("\n", "").replaceAll("\r", "");
        } catch (Exception e6) {
            e6.printStackTrace();
            return "";
        }
    }

    public static String aesEncrypt_iv(String str, String str2) {
        return aesEncrypt(str, "utf-8", "AES/CBC/PKCS5Padding", str2, "1201230125462244");
    }

    public static String b_dec(String str) {
        try {
            return new String(Base64.decode(str, 0)).trim();
        } catch (Exception e6) {
            e6.printStackTrace();
            return "";
        }
    }

    public static String b_enc(String str) {
        try {
            return new String(Base64.encode(str.getBytes(), 0)).trim();
        } catch (Exception e6) {
            e6.printStackTrace();
            return "";
        }
    }

    public static String c(Context context) {
        if (Build.VERSION.SDK_INT > 28) {
            return "";
        }
        TelephonyManager telephonyManager = (TelephonyManager) context.getSystemService("phone");
        try {
            Method method = telephonyManager.getClass().getMethod("getImei", Integer.TYPE);
            String str = (String) method.invoke(telephonyManager, 0);
            String str2 = (String) method.invoke(telephonyManager, 1);
            return TextUtils.isEmpty(str) ? str : !TextUtils.isEmpty(str2) ? str.compareTo(str2) <= 0 ? str : str2 : telephonyManager.getDeviceId();
        } catch (Exception e6) {
            e6.printStackTrace();
            return "";
        }
    }

    public static String getConfig(Context context, String str) {
        return context.getSharedPreferences("DEFAULT", 0).getString(str, "");
    }

    public static String getConfig2(Context context, String str) {
        String config = getConfig(context, "CORE");
        if (config.equals("")) {
            return "";
        }
        String b_dec = b_dec(config);
        if (b_dec.equals("")) {
            return "";
        }
        if (config.equals("")) {
            new JSONObject();
            return "";
        }
        try {
            return new JSONObject(b_dec).getString(str);
        } catch (JSONException e6) {
            e6.printStackTrace();
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
        } catch (ClassNotFoundException | IllegalAccessException | NoSuchMethodException | InvocationTargetException e6) {
            e6.printStackTrace();
            return "unknown";
        }
    }

    public static String getUUID() {
        return UUID.randomUUID().toString().replaceAll("-", "");
    }

    public static String getUUID(int i5) {
        if (i5 <= 0) {
            return null;
        }
        String uuid = getUUID();
        StringBuffer stringBuffer = new StringBuffer();
        for (int i6 = 0; i6 < i5; i6++) {
            stringBuffer.append(uuid.charAt(i6));
        }
        return stringBuffer.toString();
    }

    public static String gm(byte[] bArr) {
        try {
            MessageDigest messageDigest = MessageDigest.getInstance("MD5");
            messageDigest.update(bArr);
            return ths(messageDigest.digest());
        } catch (NoSuchAlgorithmException e6) {
            e6.printStackTrace();
            return "";
        }
    }

    public static String gma(Context context) {
        StringBuilder sb;
        String str;
        String c6 = c(context);
        if (c6 != null && c6.length() > 4) {
            return c6;
        }
        String string = Settings.System.getString(context.getContentResolver(), "android_id");
        if (Build.VERSION.SDK_INT >= 26) {
            sb = new StringBuilder();
            sb.append(string);
            str = getDeviceSerial();
        } else {
            sb = new StringBuilder();
            sb.append(string);
            str = Build.SERIAL;
        }
        sb.append(str);
        sb.append(Build.BRAND);
        sb.append(Build.MODEL);
        return gm(sb.toString().getBytes()).substring(8, 24);
    }

    public static void setConfig(Context context, String str, String str2) {
        SharedPreferences.Editor edit = context.getSharedPreferences("DEFAULT", 0).edit();
        edit.putString(str, str2);
        edit.apply();
    }

    public static void setConfig2(Context context, String str, String str2) {
        String $2 = "CORE";
        String config = getConfig(context, $2);
        try {
            if (config.equals("")) {
                JSONObject jSONObject = new JSONObject();
                jSONObject.put(str, str2);
                setConfig(context, $2, b_enc(jSONObject.toString()));
            } else {
                JSONObject jSONObject2 = new JSONObject(b_dec(config));
                jSONObject2.put(str, str2);
                setConfig(context, $2, b_enc(jSONObject2.toString()));
            }
        } catch (JSONException e6) {
            e6.printStackTrace();
        }
    }

    public static String ths(byte[] bArr) {
        if (bArr == null) {
            return "";
        }
        StringBuilder sb = new StringBuilder(bArr.length * 2);
        for (byte b6 : bArr) {
            String num = Integer.toString(b6 & 255, 16);
            if (num.length() == 1) {
                num = "0" + num;
            }
            sb.append(num);
        }
        return sb.toString();
    }

    public static String url_encode(String str) {
        try {
            return URLEncoder.encode(str, "UTF-8");
        } catch (UnsupportedEncodingException e6) {
            e6.printStackTrace();
            return str;
        }
    }
}
