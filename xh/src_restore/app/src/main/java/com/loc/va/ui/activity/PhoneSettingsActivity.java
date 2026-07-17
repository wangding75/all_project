package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;

/**
 * 手机信息伪造设置页
 * 功能：
 *   1. 显示/修改真实设备信息
 *   2. 伪造 IMEI（设备标识）
 *   3. 伪造 IMSI（SIM卡标识）
 *   4. 伪造手机品牌（Brand）
 *   5. 伪造手机型号（Model）
 *   6. 伪造硬件序列号（Serial）
 *   7. 伪造 Android ID
 *   8. 随机生成所有信息
 *   9. 重置为真实手机信息
 *
 * 工作原理：
 *   通过 Pine ART Hook 框架拦截以下系统 API：
 *   - TelephonyManager.getDeviceId() / getImei()
 *   - TelephonyManager.getSubscriberId()
 *   - Build.BRAND / Build.MODEL / Build.SERIAL
 *   - Settings.Secure.getString(ANDROID_ID)
 *
 * 原始类名：com.loc.va.ui.activity.PhoneSettingsActivity
 */
public class PhoneSettingsActivity extends Activity {

    // 伪造设备信息
    private String fakeImei;
    private String fakeImsi;
    private String fakeBrand;
    private String fakeModel;
    private String fakeSerial;
    private String fakeAndroidId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // setContentView(R.layout.activity_phone_settings);

        loadCurrentDeviceInfo();
        initViews();
        setupNotice();
    }

    /**
     * 加载当前设备信息（真实或已保存的虚假信息）
     */
    private void loadCurrentDeviceInfo() {
        // 读取真实设备信息
        // android.telephony.TelephonyManager tm = (TelephonyManager) getSystemService(TELEPHONY_SERVICE);
        // realImei = tm.getDeviceId();
        // realImsi = tm.getSubscriberId();
        // realBrand = android.os.Build.BRAND;
        // realModel = android.os.Build.MODEL;
        // realSerial = android.os.Build.SERIAL;

        // 从 SharedPreferences 读取已保存的虚假信息
        // ...
    }

    private void initViews() {
        // 提示说明（device_virtual_notice）：
        // "1、默认显示是的手机真实的信息
        //  2、目前大部分设备IMEI、IMSI已无法获取，因此会无法显示
        //  3、用户可以手动录入信息，也可以点击随机按钮，自动生成信息
        //  4、若用户只需要模拟部分内容，其它地方请选择本机按钮即可
        //  5、用户可以在上一级界面关闭模拟信息功能"
    }

    private void setupNotice() {
        // 注意：部分手机已无法正常获取IMEI
    }

    /**
     * 随机生成所有设备信息
     */
    private void randomizeAllInfo() {
        fakeImei = generateRandomImei();
        fakeImsi = generateRandomImsi();
        fakeBrand = getRandomBrand();
        fakeModel = getRandomModel(fakeBrand);
        fakeSerial = generateRandomSerial();
        fakeAndroidId = generateRandomAndroidId();

        updateUiWithFakeInfo();
    }

    /**
     * 保存虚假设备信息并激活 Hook
     */
    private void saveAndApply() {
        if (fakeBrand == null || fakeBrand.isEmpty()) {
            // 品牌不能为空（brand_empty_error）
            return;
        }
        if (fakeModel == null || fakeModel.isEmpty()) {
            // 手机型号不能为空（model_empty_error）
            return;
        }

        // 保存到 SharedPreferences
        getSharedPreferences("fake_device", MODE_PRIVATE)
                .edit()
                .putString("imei", fakeImei)
                .putString("imsi", fakeImsi)
                .putString("brand", fakeBrand)
                .putString("model", fakeModel)
                .putString("serial", fakeSerial)
                .putString("android_id", fakeAndroidId)
                .putBoolean("enabled", true)
                .apply();

        // 激活 Pine Hook，使虚假信息生效
        applyDeviceHook();
    }

    /**
     * 激活 ART Hook（Pine 框架）
     * Hook 系统方法返回虚假设备信息
     */
    private void applyDeviceHook() {
        // 通过 libpine.so 实现 ART inline hook
        // 拦截 TelephonyManager.getImei() 等方法
    }

    /**
     * 重置为真实手机信息
     */
    private void resetToRealInfo() {
        getSharedPreferences("fake_device", MODE_PRIVATE)
                .edit()
                .clear()
                .apply();
        // 取消 Hook
    }

    private void updateUiWithFakeInfo() {
        // 更新界面显示
        // tvImei.setText(fakeImei);
        // tvImsi.setText(fakeImsi);
        // 等...
    }

    // === 随机信息生成工具方法 ===

    /**
     * 生成随机 IMEI（符合 Luhn 校验算法）
     */
    private String generateRandomImei() {
        StringBuilder sb = new StringBuilder();
        java.util.Random rand = new java.util.Random();

        // 生成 14 位随机数字
        for (int i = 0; i < 14; i++) {
            sb.append(rand.nextInt(10));
        }

        // Luhn 算法补全最后一位校验位
        String imei14 = sb.toString();
        int checkDigit = calculateLuhnCheckDigit(imei14);
        return imei14 + checkDigit;
    }

    private int calculateLuhnCheckDigit(String number) {
        int sum = 0;
        for (int i = 0; i < number.length(); i++) {
            int digit = number.charAt(i) - '0';
            if (i % 2 == 1) {
                digit *= 2;
                if (digit > 9) digit -= 9;
            }
            sum += digit;
        }
        return (10 - (sum % 10)) % 10;
    }

    private String generateRandomImsi() {
        // MCC(3) + MNC(2) + MSIN(10)
        java.util.Random rand = new java.util.Random();
        String[] mccMnc = {"46000", "46001", "46002", "46003", "46007", "46011"};
        String prefix = mccMnc[rand.nextInt(mccMnc.length)];
        StringBuilder msin = new StringBuilder();
        for (int i = 0; i < 10; i++) msin.append(rand.nextInt(10));
        return prefix + msin;
    }

    private String getRandomBrand() {
        String[] brands = {"Xiaomi", "HUAWEI", "OPPO", "vivo", "Samsung", "OnePlus", "Realme"};
        return brands[(int) (Math.random() * brands.length)];
    }

    private String getRandomModel(String brand) {
        // 根据品牌返回对应型号
        switch (brand) {
            case "Xiaomi": return "2211133C";     // Xiaomi 13
            case "HUAWEI": return "VIC-AN00";      // HUAWEI Mate 50
            case "OPPO": return "PHQ110";           // OPPO Find X5
            case "vivo": return "V2243A";           // vivo X90
            case "Samsung": return "SM-S9180";      // Galaxy S23
            default: return "GM1910";               // OnePlus 7T
        }
    }

    private String generateRandomSerial() {
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        StringBuilder sb = new StringBuilder();
        java.util.Random rand = new java.util.Random();
        for (int i = 0; i < 12; i++) {
            sb.append(chars.charAt(rand.nextInt(chars.length())));
        }
        return sb.toString();
    }

    private String generateRandomAndroidId() {
        java.util.Random rand = new java.util.Random();
        StringBuilder sb = new StringBuilder();
        String hex = "0123456789abcdef";
        for (int i = 0; i < 16; i++) {
            sb.append(hex.charAt(rand.nextInt(hex.length())));
        }
        return sb.toString();
    }
}
