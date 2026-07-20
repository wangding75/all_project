package com.sx.app.ui.location;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.switchmaterial.SwitchMaterial;
import com.sx.app.R;
import com.sx.app.data.LocationConfig;

public class LocationSettingsActivity extends AppCompatActivity {

    private SwitchMaterial mSwitchEnabled;
    private TextView mTvCoord;
    private EditText mEtLat;
    private EditText mEtLng;
    private EditText mEtAccuracy;
    private EditText mEtInterval;
    private SwitchMaterial mSwitchDrift;
    private SwitchMaterial mSwitchAntiMock;
    private MaterialButton mBtnToggleService;

    private LocationConfig mConfig;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_location_settings);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle(R.string.module_location);
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        mSwitchEnabled = findViewById(R.id.switch_enabled);
        mTvCoord = findViewById(R.id.tv_coord);
        mEtLat = findViewById(R.id.et_lat);
        mEtLng = findViewById(R.id.et_lng);
        mEtAccuracy = findViewById(R.id.et_accuracy);
        mEtInterval = findViewById(R.id.et_interval);
        mSwitchDrift = findViewById(R.id.switch_drift);
        mSwitchAntiMock = findViewById(R.id.switch_anti_mock);
        mBtnToggleService = findViewById(R.id.btn_toggle_service);

        mConfig = LocationConfig.load(this);
        loadConfigUI();

        findViewById(R.id.btn_save).setOnClickListener(v -> saveConfig(true));

        findViewById(R.id.btn_random).setOnClickListener(v -> {
            try {
                double lat = Double.parseDouble(mEtLat.getText().toString());
                double lng = Double.parseDouble(mEtLng.getText().toString());
                lat += (Math.random() - 0.5) * 0.005;
                lng += (Math.random() - 0.5) * 0.005;
                mEtLat.setText(String.format(java.util.Locale.US, "%.6f", lat));
                mEtLng.setText(String.format(java.util.Locale.US, "%.6f", lng));
            } catch (Exception e) {
                // If inputs are empty or invalid, randomize based on config defaults
                double lat = mConfig.latitude + (Math.random() - 0.5) * 0.005;
                double lng = mConfig.longitude + (Math.random() - 0.5) * 0.005;
                mEtLat.setText(String.format(java.util.Locale.US, "%.6f", lat));
                mEtLng.setText(String.format(java.util.Locale.US, "%.6f", lng));
            }
        });

        findViewById(R.id.btn_pick).setOnClickListener(v -> {
            Intent intent = new Intent(this, LocationPickerActivity.class);
            startActivityForResult(intent, 100);
        });

        mBtnToggleService.setOnClickListener(v -> {
            if (saveConfig(false)) {
                Toast.makeText(this, "已保存。Phase 0 不启动系统模拟定位服务。", Toast.LENGTH_LONG).show();
            }
        });
    }

    private void loadConfigUI() {
        mSwitchEnabled.setChecked(mConfig.enabled);
        mTvCoord.setText(getString(R.string.loc_coord, mConfig.latitude, mConfig.longitude));
        mEtLat.setText(String.valueOf(mConfig.latitude));
        mEtLng.setText(String.valueOf(mConfig.longitude));
        mEtAccuracy.setText(String.valueOf(mConfig.accuracy));
        mEtInterval.setText(String.valueOf(mConfig.intervalMs));
        mSwitchDrift.setChecked(mConfig.microDrift);
        mSwitchAntiMock.setChecked(mConfig.antiMockDetect);
    }

    private boolean saveConfig(boolean showSavedToast) {
        String latStr = mEtLat.getText().toString();
        String lngStr = mEtLng.getText().toString();
        if (TextUtils.isEmpty(latStr) || TextUtils.isEmpty(lngStr)) {
            Toast.makeText(this, R.string.loc_input_error, Toast.LENGTH_SHORT).show();
            return false;
        }

        try {
            double lat = Double.parseDouble(latStr);
            double lng = Double.parseDouble(lngStr);
            if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
                Toast.makeText(this, R.string.loc_input_error, Toast.LENGTH_SHORT).show();
                return false;
            }

            mConfig.enabled = mSwitchEnabled.isChecked();
            mConfig.latitude = lat;
            mConfig.longitude = lng;
            mConfig.accuracy = Float.parseFloat(mEtAccuracy.getText().toString());
            mConfig.intervalMs = Long.parseLong(mEtInterval.getText().toString());
            mConfig.microDrift = mSwitchDrift.isChecked();
            mConfig.antiMockDetect = mSwitchAntiMock.isChecked();
            mConfig.save(this);

            mTvCoord.setText(getString(R.string.loc_coord, lat, lng));
            if (showSavedToast) {
                Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show();
            }
            return true;
        } catch (NumberFormatException e) {
            Toast.makeText(this, R.string.loc_input_error, Toast.LENGTH_SHORT).show();
            return false;
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 100 && resultCode == RESULT_OK && data != null) {
            double lat = data.getDoubleExtra("lat", mConfig.latitude);
            double lng = data.getDoubleExtra("lng", mConfig.longitude);
            mEtLat.setText(String.valueOf(lat));
            mEtLng.setText(String.valueOf(lng));
        }
    }
}
