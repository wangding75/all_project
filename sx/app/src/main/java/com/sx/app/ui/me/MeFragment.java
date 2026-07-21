package com.sx.app.ui.me;

import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import com.sx.app.BuildConfig;
import com.sx.app.R;
import com.sx.app.license.LicenseManager;
import com.sx.app.ui.LicenseActivity;

public class MeFragment extends Fragment {

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_me, container, false);

        TextView tvVersion = view.findViewById(R.id.tv_version);
        tvVersion.setText("版本: " + BuildConfig.VERSION_NAME);

        TextView tvDevice = view.findViewById(R.id.tv_device);
        if (getContext() != null) {
            String deviceId = LicenseManager.getDeviceId(getContext());
            tvDevice.setText(getString(R.string.license_device, deviceId));
        }

        view.findViewById(R.id.btn_license).setOnClickListener(v -> {
            startActivity(new Intent(getContext(), LicenseActivity.class));
        });

        view.findViewById(R.id.btn_probe).setOnClickListener(v -> {
            startActivity(new Intent(getContext(), com.sx.app.ui.probe.SpoofProbeActivity.class));
        });

        view.findViewById(R.id.btn_privacy_policy).setOnClickListener(v -> {
            startActivity(new Intent(getContext(), com.sx.app.ui.legal.PrivacyPolicyActivity.class));
        });

        return view;
    }
}
