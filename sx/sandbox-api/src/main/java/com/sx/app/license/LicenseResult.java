package com.sx.app.license;

public class LicenseResult {
    public final boolean success;
    public final String  token;      // 服务端下发的 token（激活成功时有值）
    public final long    expireAt;   // Unix ms；-1 = 永久；0 = 无效
    public final String  message;

    public LicenseResult(boolean success, String token, long expireAt, String message) {
        this.success  = success;
        this.token    = token;
        this.expireAt = expireAt;
        this.message  = message;
    }

    public static LicenseResult fail(String message) {
        return new LicenseResult(false, null, 0L, message);
    }
}
