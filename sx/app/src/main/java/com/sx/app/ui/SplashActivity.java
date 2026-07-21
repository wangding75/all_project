package com.sx.app.ui;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import androidx.appcompat.app.AppCompatActivity;
import com.sx.app.R;
import com.sx.app.license.LicenseManager;

public class SplashActivity extends AppCompatActivity {
    private final Handler mHandler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);

        mHandler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (isFinishing() || isDestroyed()) {
                    return;
                }
                Intent intent;
                if (LicenseManager.isActivated(SplashActivity.this)) {
                    intent = new Intent(SplashActivity.this, MainActivity.class);
                    startActivity(intent);
                    finish();
                    // 进入主界面后，后台静默刷新 token 有效期
                    LicenseManager.refreshTokenAsync(SplashActivity.this);
                } else {
                    intent = new Intent(SplashActivity.this, LicenseActivity.class);
                    startActivity(intent);
                    finish();
                }
            }
        }, 2000);
    }

    @Override
    protected void onDestroy() {
        mHandler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }
}
