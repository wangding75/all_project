package com.sx.app.ui.camera;

import android.content.Intent;
import android.os.Bundle;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import com.google.android.material.switchmaterial.SwitchMaterial;
import com.sx.app.R;
import com.sx.app.data.CameraConfig;

public class VirtualCameraActivity extends AppCompatActivity {

    private SwitchMaterial mSwitchEnabled;
    private RadioGroup mRgSource;
    private RadioButton mRbVideo;
    private RadioButton mRbImage;
    private TextView mTvPath;

    private CameraConfig mConfig;
    private String mSelectedPath = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_camera);

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle(R.string.module_camera);
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        mSwitchEnabled = findViewById(R.id.switch_enabled);
        mRgSource = findViewById(R.id.rg_source);
        mRbVideo = findViewById(R.id.rb_video);
        mRbImage = findViewById(R.id.rb_image);
        mTvPath = findViewById(R.id.tv_path);

        mConfig = CameraConfig.load(this);
        loadConfigUI();

        mRgSource.setOnCheckedChangeListener((group, checkedId) -> {
            // If checked type changes and path was selected, reset or keep
        });

        findViewById(R.id.btn_pick).setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
            if (mRbVideo.isChecked()) {
                intent.setType("video/*");
            } else {
                intent.setType("image/*");
            }
            startActivityForResult(Intent.createChooser(intent, getString(R.string.action_pick_media)), 200);
        });

        findViewById(R.id.btn_save).setOnClickListener(v -> {
            mConfig.enabled = mSwitchEnabled.isChecked();
            mConfig.sourceType = mRbVideo.isChecked() ? CameraConfig.TYPE_VIDEO : CameraConfig.TYPE_IMAGE;
            mConfig.mediaPath = mSelectedPath;
            mConfig.save(this);
            Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show();
        });
    }

    private void loadConfigUI() {
        mSwitchEnabled.setChecked(mConfig.enabled);
        if (CameraConfig.TYPE_VIDEO.equals(mConfig.sourceType)) {
            mRbVideo.setChecked(true);
        } else {
            mRbImage.setChecked(true);
        }
        mSelectedPath = mConfig.mediaPath;
        if (mSelectedPath == null || mSelectedPath.isEmpty()) {
            mTvPath.setText("未选择媒体文件");
        } else {
            mTvPath.setText(mSelectedPath);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 200 && resultCode == RESULT_OK && data != null && data.getData() != null) {
            mSelectedPath = data.getData().toString();
            mTvPath.setText(mSelectedPath);
        }
    }
}
