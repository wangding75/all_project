package com.sx.app.ui.camera;

import android.content.Intent;
import android.os.Bundle;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import com.google.android.material.switchmaterial.SwitchMaterial;
import com.sx.app.R;
import com.sx.app.data.CameraConfig;
import com.sx.app.util.PermissionHelper;

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
            if (!PermissionHelper.hasStoragePermission(this)) {
                PermissionHelper.requestStoragePermission(this, 101);
                return;
            }
            openMediaPicker();
        });

        findViewById(R.id.btn_save).setOnClickListener(v -> {
            mConfig.enabled = mSwitchEnabled.isChecked();
            mConfig.sourceType = mRbVideo.isChecked() ? CameraConfig.TYPE_VIDEO : CameraConfig.TYPE_IMAGE;
            mConfig.mediaPath = mSelectedPath;
            mConfig.save(this);
            Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show();
        });
    }

    private void openMediaPicker() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        if (mRbVideo.isChecked()) {
            intent.setType("video/*");
        } else {
            intent.setType("image/*");
        }
        startActivityForResult(Intent.createChooser(intent, getString(R.string.action_pick_media)), 200);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == 101) {
            // 可能一次申请多项权限，用 Helper 综合判断
            if (PermissionHelper.hasStoragePermission(this)) {
                openMediaPicker();
            } else {
                Toast.makeText(this, "需要存储/媒体权限以选择视频或图片", Toast.LENGTH_SHORT).show();
            }
        }
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

    private String copyMediaToInternal(android.net.Uri uri) {
        try {
            String extension = mRbVideo.isChecked() ? ".mp4" : ".jpg";
            java.io.File dir = getExternalFilesDir("camera");
            if (dir == null) {
                java.io.File externalCache = getExternalCacheDir();
                if (externalCache != null) {
                    dir = new java.io.File(externalCache, "camera");
                }
            }
            if (dir == null) {
                dir = new java.io.File(getFilesDir(), "camera");
            }
            if (!dir.exists() && !dir.mkdirs()) {
                return null;
            }
            java.io.File dest = new java.io.File(dir, "temp_camera_source" + extension);
            try (java.io.InputStream is = getContentResolver().openInputStream(uri);
                 java.io.FileOutputStream os = new java.io.FileOutputStream(dest)) {
                if (is == null) {
                    return null;
                }
                byte[] buffer = new byte[8192];
                int read;
                while ((read = is.read(buffer)) != -1) {
                    os.write(buffer, 0, read);
                }
                os.flush();
            }
            return dest.getAbsolutePath();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == 200 && resultCode == RESULT_OK && data != null && data.getData() != null) {
            android.net.Uri uri = data.getData();
            String localPath = copyMediaToInternal(uri);
            if (localPath != null) {
                mSelectedPath = localPath;
            } else {
                mSelectedPath = uri.toString();
            }
            mTvPath.setText(mSelectedPath);
        }
    }
}
