package com.sx.app.ui.home;

import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import com.sx.app.R;
import com.sx.app.license.LicenseManager;
import com.sx.app.ui.LicenseActivity;
import com.sx.app.ui.MainActivity;
import com.sx.app.ui.camera.VirtualCameraActivity;
import com.sx.app.ui.device.DeviceSettingsActivity;
import com.sx.app.ui.location.LocationSettingsActivity;
import com.sx.app.ui.network.NetworkSettingsActivity;

public class HomeFragment extends Fragment {

    private TextView mTvXposedStatus;
    private TextView mTvLicenseStatus;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.fragment_home, container, false);

        mTvXposedStatus = view.findViewById(R.id.tv_xposed_status);
        mTvLicenseStatus = view.findViewById(R.id.tv_license_status);

        // Click listeners for cards
        view.findViewById(R.id.card_sandbox).setOnClickListener(v -> {
            if (getActivity() instanceof MainActivity) {
                ((MainActivity) getActivity()).switchToAppsTab();
            }
        });

        view.findViewById(R.id.card_location).setOnClickListener(v -> {
            startActivity(new Intent(getContext(), LocationSettingsActivity.class));
        });

        view.findViewById(R.id.card_camera).setOnClickListener(v -> {
            startActivity(new Intent(getContext(), VirtualCameraActivity.class));
        });

        view.findViewById(R.id.card_device).setOnClickListener(v -> {
            startActivity(new Intent(getContext(), DeviceSettingsActivity.class));
        });

        view.findViewById(R.id.card_network).setOnClickListener(v -> {
            startActivity(new Intent(getContext(), NetworkSettingsActivity.class));
        });

        view.findViewById(R.id.card_license).setOnClickListener(v -> {
            startActivity(new Intent(getContext(), LicenseActivity.class));
        });

        return view;
    }

    @Override
    public void onResume() {
        super.onResume();
        updateStatus();
    }

    private void updateStatus() {
        if (mTvXposedStatus != null) {
            mTvXposedStatus.setText("LSPosed 模块未激活（Phase 0 不依赖）");
            mTvXposedStatus.setTextColor(getResources().getColor(R.color.text_secondary));
        }

        if (mTvLicenseStatus != null && getContext() != null) {
            if (LicenseManager.isActivated(getContext())) {
                LicenseManager.LicenseInfo info = LicenseManager.load(getContext());
                if (info != null) {
                    mTvLicenseStatus.setText(getString(R.string.license_ok, LicenseManager.formatExpire(info.expireAt)));
                    mTvLicenseStatus.setTextColor(getResources().getColor(R.color.accent));
                }
            } else {
                mTvLicenseStatus.setText(R.string.license_expired);
                mTvLicenseStatus.setTextColor(getResources().getColor(R.color.danger));
            }
        }
    }
}
