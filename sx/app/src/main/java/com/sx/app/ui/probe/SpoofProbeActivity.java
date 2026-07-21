package com.sx.app.ui.probe;

import android.annotation.SuppressLint;
import android.content.Context;
import android.location.Location;
import android.location.LocationManager;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.telephony.gsm.GsmCellLocation;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import com.google.android.material.button.MaterialButton;
import com.sx.app.R;

public class SpoofProbeActivity extends AppCompatActivity {

    private TextView mTvLocationInfo;
    private TextView mTvDeviceInfo;
    private TextView mTvNetworkInfo;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_spoof_probe);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle("环境伪装探针");
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        mTvLocationInfo = findViewById(R.id.tv_location_info);
        mTvDeviceInfo = findViewById(R.id.tv_device_info);
        mTvNetworkInfo = findViewById(R.id.tv_network_info);

        MaterialButton btnRefresh = findViewById(R.id.btn_refresh);
        btnRefresh.setOnClickListener(v -> refreshProbe());

        refreshProbe();
    }

    @SuppressLint({"MissingPermission", "HardwareIds"})
    private void refreshProbe() {
        // 1. Location
        StringBuilder locSb = new StringBuilder();
        try {
            LocationManager lm = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
            if (lm != null) {
                Location loc = lm.getLastKnownLocation(LocationManager.GPS_PROVIDER);
                if (loc == null) {
                    loc = lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
                }
                if (loc != null) {
                    locSb.append("Latitude: ").append(loc.getLatitude()).append("\n");
                    locSb.append("Longitude: ").append(loc.getLongitude()).append("\n");
                    locSb.append("Altitude: ").append(loc.getAltitude()).append("\n");
                    locSb.append("Accuracy: ").append(loc.getAccuracy()).append(" m\n");
                    locSb.append("Time: ").append(loc.getTime()).append("\n");
                    locSb.append("isFromMockProvider: ").append(loc.isFromMockProvider()).append("\n");
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                        locSb.append("isMock: ").append(loc.isMock()).append("\n");
                    }
                } else {
                    locSb.append("No location sample available.");
                }
            }
        } catch (Exception e) {
            locSb.append("Error reading location: ").append(e.getMessage());
        }
        mTvLocationInfo.setText(locSb.toString());

        // 2. Device
        StringBuilder devSb = new StringBuilder();
        try {
            devSb.append("BRAND: ").append(Build.BRAND).append("\n");
            devSb.append("MODEL: ").append(Build.MODEL).append("\n");
            devSb.append("MANUFACTURER: ").append(Build.MANUFACTURER).append("\n");
            devSb.append("BOARD: ").append(Build.BOARD).append("\n");
            devSb.append("SERIAL: ").append(Build.SERIAL).append("\n");

            String androidId = Settings.Secure.getString(getContentResolver(), Settings.Secure.ANDROID_ID);
            devSb.append("ANDROID_ID: ").append(androidId).append("\n");

            TelephonyManager tm = (TelephonyManager) getSystemService(Context.TELEPHONY_SERVICE);
            if (tm != null) {
                try {
                    devSb.append("IMEI: ").append(tm.getDeviceId()).append("\n");
                } catch (Throwable ignored) {}
                try {
                    devSb.append("Operator: ").append(tm.getNetworkOperatorName()).append("\n");
                } catch (Throwable ignored) {}
            }
        } catch (Exception e) {
            devSb.append("Error reading device: ").append(e.getMessage());
        }
        mTvDeviceInfo.setText(devSb.toString());

        // 3. Network & Cell
        StringBuilder netSb = new StringBuilder();
        try {
            WifiManager wm = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            if (wm != null) {
                WifiInfo info = wm.getConnectionInfo();
                if (info != null) {
                    netSb.append("SSID: ").append(info.getSSID()).append("\n");
                    netSb.append("BSSID: ").append(info.getBSSID()).append("\n");
                    netSb.append("MAC: ").append(info.getMacAddress()).append("\n");
                }
            }

            TelephonyManager tm = (TelephonyManager) getSystemService(Context.TELEPHONY_SERVICE);
            if (tm != null) {
                try {
                    android.telephony.CellLocation cellLoc = tm.getCellLocation();
                    if (cellLoc instanceof GsmCellLocation) {
                        GsmCellLocation gsm = (GsmCellLocation) cellLoc;
                        netSb.append("Cell LAC: ").append(gsm.getLac()).append("\n");
                        netSb.append("Cell CID: ").append(gsm.getCid()).append("\n");
                    }
                } catch (Throwable ignored) {}
            }
        } catch (Exception e) {
            netSb.append("Error reading network: ").append(e.getMessage());
        }
        mTvNetworkInfo.setText(netSb.toString());
    }
}
