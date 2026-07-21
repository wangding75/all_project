package com.sx.app.ui;

import android.content.Intent;
import android.os.Bundle;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import com.sx.app.R;
import com.sx.app.license.LicenseManager;

public class LicenseActivity extends AppCompatActivity {

    private EditText mEtCard;
    private TextView mTvStatus;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_license);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        TextView tvDeviceId = findViewById(R.id.tv_device_id);
        String deviceId = LicenseManager.getDeviceId(this);
        tvDeviceId.setText(getString(R.string.license_device, deviceId));

        mTvStatus = findViewById(R.id.tv_status);
        mEtCard = findViewById(R.id.et_card);

        updateStatusText();

        findViewById(R.id.btn_activate).setOnClickListener(v -> {
            String card = mEtCard.getText().toString().trim();
            if (card.isEmpty()) {
                Toast.makeText(this, "请输入卡密", Toast.LENGTH_SHORT).show();
                return;
            }
            // 禁用按钮，防重复点击
            v.setEnabled(false);

            LicenseManager.activateAsync(this, card, result -> {
                v.setEnabled(true);
                if (result.success) {
                    Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show();
                    updateStatusText();
                    Intent intent = new Intent(this, MainActivity.class);
                    intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                    finish();
                } else {
                    mTvStatus.setText(result.message);
                    Toast.makeText(this, result.message, Toast.LENGTH_LONG).show();
                }
            });
        });
    }

    private void updateStatusText() {
        if (LicenseManager.isActivated(this)) {
            LicenseManager.LicenseInfo info = LicenseManager.load(this);
            if (info != null) {
                mTvStatus.setText(getString(R.string.license_ok, LicenseManager.formatExpire(info.expireAt)));
                mTvStatus.setTextColor(getResources().getColor(R.color.accent));
            }
        } else {
            mTvStatus.setText(R.string.license_expired);
            mTvStatus.setTextColor(getResources().getColor(R.color.danger));
        }
    }
}
