package com.sx.app.ui.device;

import android.os.Bundle;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import com.google.android.material.switchmaterial.SwitchMaterial;
import com.sx.app.R;
import com.sx.app.data.DeviceProfile;

public class DeviceSettingsActivity extends AppCompatActivity {

    private SwitchMaterial mSwitchEnabled;
    private EditText mEtBrand;
    private EditText mEtModel;
    private EditText mEtManufacturer;
    private EditText mEtBoard;
    private EditText mEtSerial;
    private EditText mEtImei;
    private EditText mEtMeid;
    private EditText mEtAndroidId;
    private EditText mEtPhone;
    private EditText mEtImsi;
    private EditText mEtIccid;
    private EditText mEtOperator;

    private DeviceProfile mProfile;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_device_settings);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle(R.string.module_device);
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        mSwitchEnabled = findViewById(R.id.switch_enabled);
        mEtBrand = findViewById(R.id.et_brand);
        mEtModel = findViewById(R.id.et_model);
        mEtManufacturer = findViewById(R.id.et_manufacturer);
        mEtBoard = findViewById(R.id.et_board);
        mEtSerial = findViewById(R.id.et_serial);
        mEtImei = findViewById(R.id.et_imei);
        mEtMeid = findViewById(R.id.et_meid);
        mEtAndroidId = findViewById(R.id.et_android_id);
        mEtPhone = findViewById(R.id.et_phone);
        mEtImsi = findViewById(R.id.et_imsi);
        mEtIccid = findViewById(R.id.et_iccid);
        mEtOperator = findViewById(R.id.et_operator);

        mProfile = DeviceProfile.load(this);
        loadProfileUI();

        findViewById(R.id.btn_random).setOnClickListener(v -> {
            mProfile.randomize();
            loadProfileUI();
            Toast.makeText(this, "随机参数已生成，请点击保存生效", Toast.LENGTH_SHORT).show();
        });

        findViewById(R.id.btn_reset).setOnClickListener(v -> {
            mProfile.resetToReal();
            loadProfileUI();
            Toast.makeText(this, "已重置为真机信息，请点击保存生效", Toast.LENGTH_SHORT).show();
        });

        findViewById(R.id.btn_save).setOnClickListener(v -> {
            mProfile.enabled = mSwitchEnabled.isChecked();
            mProfile.brand = mEtBrand.getText().toString();
            mProfile.model = mEtModel.getText().toString();
            mProfile.manufacturer = mEtManufacturer.getText().toString();
            mProfile.board = mEtBoard.getText().toString();
            mProfile.serial = mEtSerial.getText().toString();
            mProfile.imei = mEtImei.getText().toString();
            mProfile.meid = mEtMeid.getText().toString();
            mProfile.androidId = mEtAndroidId.getText().toString();
            mProfile.phoneNumber = mEtPhone.getText().toString();
            mProfile.imsi = mEtImsi.getText().toString();
            mProfile.iccid = mEtIccid.getText().toString();
            mProfile.operatorName = mEtOperator.getText().toString();

            mProfile.save(this);
            Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show();
        });
    }

    private void loadProfileUI() {
        mSwitchEnabled.setChecked(mProfile.enabled);
        mEtBrand.setText(mProfile.brand);
        mEtModel.setText(mProfile.model);
        mEtManufacturer.setText(mProfile.manufacturer);
        mEtBoard.setText(mProfile.board);
        mEtSerial.setText(mProfile.serial);
        mEtImei.setText(mProfile.imei);
        mEtMeid.setText(mProfile.meid);
        mEtAndroidId.setText(mProfile.androidId);
        mEtPhone.setText(mProfile.phoneNumber);
        mEtImsi.setText(mProfile.imsi);
        mEtIccid.setText(mProfile.iccid);
        mEtOperator.setText(mProfile.operatorName);
    }
}
