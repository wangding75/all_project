package com.sx.app.ui.sandbox;

import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.text.TextUtils;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.sx.app.license.LicenseManager;
import com.sx.app.sandbox.InstallResult;
import com.sx.app.sandbox.SandboxProvider;
import com.sx.app.ui.LicenseActivity;

/**
 * Desktop pin-shortcut entry for a sandbox instance.
 * No DEV auto-activate. Only packages present on the host device may be launched
 * (install into sandbox on demand if missing).
 */
public class ShortcutLaunchActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!LicenseManager.isActivated(this)) {
            Toast.makeText(this, "请先激活授权", Toast.LENGTH_LONG).show();
            startActivity(new Intent(this, LicenseActivity.class)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            finish();
            return;
        }

        Intent in = getIntent();
        String packageName = in != null ? in.getStringExtra("package_name") : null;
        int userId = in != null ? in.getIntExtra("user_id", 0) : 0;

        if (TextUtils.isEmpty(packageName)) {
            Toast.makeText(this, "无效的快捷方式", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        // Reject packages that do not exist on the host device (forged intents).
        try {
            getPackageManager().getPackageInfo(packageName, 0);
        } catch (PackageManager.NameNotFoundException e) {
            Toast.makeText(this, "设备上未找到该应用", Toast.LENGTH_LONG).show();
            finish();
            return;
        }

        if (!SandboxProvider.getEngine().isInstalled(packageName, userId)) {
            InstallResult installResult = SandboxProvider.getEngine().installFromHost(packageName);
            if (installResult == null || !installResult.success) {
                String msg = installResult != null && !TextUtils.isEmpty(installResult.message)
                        ? installResult.message : "导入沙箱失败";
                Toast.makeText(this, msg, Toast.LENGTH_LONG).show();
                finish();
                return;
            }
        }

        boolean ok = SandboxProvider.getEngine().launch(packageName, userId);
        if (!ok) {
            Toast.makeText(this, "启动失败：授权未激活或底层引擎未就绪", Toast.LENGTH_LONG).show();
            finish();
        } else {
            finish();
        }
    }
}
