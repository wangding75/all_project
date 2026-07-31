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
                LicenseManager.checkActivationAsync(
                        SplashActivity.this, SplashActivity.this::openNextScreen);
            }
        }, 2000);
    }

    private void openNextScreen(boolean activated) {
        if (isFinishing() || isDestroyed()) {
            return;
        }
        Intent intent = new Intent(
                this, activated ? MainActivity.class : LicenseActivity.class);
        startActivity(intent);
        finish();
    }

    @Override
    protected void onDestroy() {
        mHandler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }
}
