package com.sx.app.ui.network;

import android.os.Bundle;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import com.google.android.material.switchmaterial.SwitchMaterial;
import com.sx.app.R;
import com.sx.app.data.NetworkProfile;

public class NetworkSettingsActivity extends AppCompatActivity {

    private SwitchMaterial mSwitchEnabled;
    private EditText mEtSsid;
    private EditText mEtBssid;
    private EditText mEtMac;
    private EditText mEtMcc;
    private EditText mEtMnc;
    private EditText mEtLac;
    private EditText mEtCid;
    private EditText mEtScanList;

    private NetworkProfile mProfile;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_network_settings);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle(R.string.module_network);
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        mSwitchEnabled = findViewById(R.id.switch_enabled);
        mEtSsid = findViewById(R.id.et_ssid);
        mEtBssid = findViewById(R.id.et_bssid);
        mEtMac = findViewById(R.id.et_mac);
        mEtMcc = findViewById(R.id.et_mcc);
        mEtMnc = findViewById(R.id.et_mnc);
        mEtLac = findViewById(R.id.et_lac);
        mEtCid = findViewById(R.id.et_cid);
        mEtScanList = findViewById(R.id.et_scan_list);

        mProfile = NetworkProfile.load(this);
        loadProfileUI();

        findViewById(R.id.btn_random).setOnClickListener(v -> {
            mProfile.randomize();
            loadProfileUI();
            Toast.makeText(this, "随机网络参数已生成，请点击保存生效", Toast.LENGTH_SHORT).show();
        });

        findViewById(R.id.btn_save).setOnClickListener(v -> {
            mProfile.enabled = mSwitchEnabled.isChecked();
            mProfile.ssid = mEtSsid.getText().toString();
            mProfile.bssid = mEtBssid.getText().toString();
            mProfile.mac = mEtMac.getText().toString();

            try {
                mProfile.mcc = Integer.parseInt(mEtMcc.getText().toString());
            } catch (Exception ignored) {}
            try {
                mProfile.mnc = Integer.parseInt(mEtMnc.getText().toString());
            } catch (Exception ignored) {}
            try {
                mProfile.lac = Integer.parseInt(mEtLac.getText().toString());
            } catch (Exception ignored) {}
            try {
                mProfile.cid = Integer.parseInt(mEtCid.getText().toString());
            } catch (Exception ignored) {}

            mProfile.parseScanListText(mEtScanList.getText().toString());
            mProfile.save(this);
            Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show();
        });
    }

    private void loadProfileUI() {
        mSwitchEnabled.setChecked(mProfile.enabled);
        mEtSsid.setText(mProfile.ssid);
        mEtBssid.setText(mProfile.bssid);
        mEtMac.setText(mProfile.mac);
        mEtMcc.setText(String.valueOf(mProfile.mcc));
        mEtMnc.setText(String.valueOf(mProfile.mnc));
        mEtLac.setText(String.valueOf(mProfile.lac));
        mEtCid.setText(String.valueOf(mProfile.cid));
        mEtScanList.setText(mProfile.scanListAsText());
    }
}
