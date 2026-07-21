package com.sx.app.ui.sandbox;

import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import com.sx.app.R;
import com.sx.app.data.SandboxAppInfo;
import com.sx.app.sandbox.SandboxEngine;
import com.sx.app.sandbox.SandboxProvider;
import com.sx.app.ui.location.LocationSettingsActivity;

public class AppDetailActivity extends AppCompatActivity {

    private String mPackageName;
    private int mUserId;
    private SandboxEngine mEngine;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_app_detail);

        mPackageName = getIntent().getStringExtra("package_name");
        mUserId = getIntent().getIntExtra("user_id", 0);
        mEngine = SandboxProvider.getEngine();

        SandboxAppInfo appInfo = mEngine.get(mPackageName, mUserId);
        if (appInfo == null) {
            Toast.makeText(this, "未找到应用信息", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle("应用详情");
        }
        toolbar.setNavigationOnClickListener(v -> finish());

        ImageView ivIcon = findViewById(R.id.iv_icon);
        TextView tvName = findViewById(R.id.tv_name);
        TextView tvPkg = findViewById(R.id.tv_pkg);

        tvName.setText(appInfo.displayName());
        tvPkg.setText(mPackageName);

        PackageManager pm = getPackageManager();
        try {
            Drawable icon = pm.getApplicationIcon(mPackageName);
            ivIcon.setImageDrawable(icon);
        } catch (PackageManager.NameNotFoundException e) {
            ivIcon.setImageResource(R.drawable.ic_launcher);
        }

        findViewById(R.id.btn_launch).setOnClickListener(v -> {
            if (!com.sx.app.license.LicenseManager.isActivated(this)) {
                new AlertDialog.Builder(this)
                        .setTitle("未激活或已过期")
                        .setMessage("软件授权未激活或已过期，无法启动沙箱分身。请前往【我的 -> 授权管理】输入有效卡密激活。")
                        .setPositiveButton("去激活", (dialog, which) -> {
                            startActivity(new Intent(this, com.sx.app.ui.license.LicenseActivity.class));
                        })
                        .setNegativeButton("取消", null)
                        .show();
                return;
            }
            mEngine.launch(mPackageName, mUserId);
            Toast.makeText(this, "正在启动 " + appInfo.displayName() + "...", Toast.LENGTH_SHORT).show();
        });

        findViewById(R.id.btn_clone).setOnClickListener(v -> {
            int newUserId = mEngine.clone(mPackageName);
            if (newUserId >= 0) {
                Toast.makeText(this, "克隆分身成功", Toast.LENGTH_SHORT).show();
                finish();
            } else {
                Toast.makeText(this, "克隆分身失败", Toast.LENGTH_SHORT).show();
            }
        });

        findViewById(R.id.btn_shortcut).setOnClickListener(v -> {
            boolean success = mEngine.createShortcut(this, mPackageName, mUserId);
            if (success) {
                Toast.makeText(this, "快捷方式已创建", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "快捷方式创建失败（可能系统不支持或无权限）", Toast.LENGTH_LONG).show();
            }
        });

        findViewById(R.id.btn_independent_loc).setOnClickListener(v -> {
            Intent intent = new Intent(this, LocationSettingsActivity.class);
            intent.putExtra("package_name", mPackageName);
            intent.putExtra("user_id", mUserId);
            startActivity(intent);
        });

        findViewById(R.id.btn_independent_device).setOnClickListener(v -> {
            Intent intent = new Intent(this, com.sx.app.ui.device.DeviceSettingsActivity.class);
            intent.putExtra("package_name", mPackageName);
            intent.putExtra("user_id", mUserId);
            startActivity(intent);
        });

        findViewById(R.id.btn_independent_network).setOnClickListener(v -> {
            Intent intent = new Intent(this, com.sx.app.ui.network.NetworkSettingsActivity.class);
            intent.putExtra("package_name", mPackageName);
            intent.putExtra("user_id", mUserId);
            startActivity(intent);
        });

        findViewById(R.id.btn_clear).setOnClickListener(v -> {
            new AlertDialog.Builder(this)
                    .setTitle("确认清除")
                    .setMessage("是否确认清除 " + appInfo.displayName() + " 的所有分身数据？")
                    .setPositiveButton(R.string.action_confirm, (dialog, which) -> {
                        boolean ok = mEngine.clearData(mPackageName, mUserId);
                        if (ok) {
                            Toast.makeText(this, "数据已清除", Toast.LENGTH_SHORT).show();
                        } else {
                            Toast.makeText(this, "清除失败", Toast.LENGTH_SHORT).show();
                        }
                    })
                    .setNegativeButton(R.string.action_cancel, null)
                    .show();
        });

        findViewById(R.id.btn_remove).setOnClickListener(v -> {
            new AlertDialog.Builder(this)
                    .setTitle("确认卸载")
                    .setMessage("是否确认移除 " + appInfo.displayName() + "？")
                    .setPositiveButton(R.string.action_confirm, (dialog, which) -> {
                        boolean ok = mEngine.uninstall(mPackageName, mUserId);
                        if (ok) {
                            Toast.makeText(this, "应用已卸载", Toast.LENGTH_SHORT).show();
                            finish();
                        } else {
                            Toast.makeText(this, "卸载失败", Toast.LENGTH_SHORT).show();
                        }
                    })
                    .setNegativeButton(R.string.action_cancel, null)
                    .show();
        });
    }
}
