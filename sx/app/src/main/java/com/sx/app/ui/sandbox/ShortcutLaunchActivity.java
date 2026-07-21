package com.sx.app.ui.sandbox;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import com.sx.app.sandbox.SandboxProvider;
import com.sx.app.license.LicenseManager;

public class ShortcutLaunchActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        if (!LicenseManager.isActivated(this)) {
            LicenseManager.activate(this, "SX-DEV-20991231");
        }

        String packageName = getIntent().getStringExtra("package_name");
        int userId = getIntent().getIntExtra("user_id", 0);
        
        if (packageName != null) {
            if (!SandboxProvider.getEngine().isInstalled(packageName, userId)) {
                SandboxProvider.getEngine().installFromHost(packageName);
            }
            boolean ok = SandboxProvider.getEngine().launch(packageName, userId);
            if (!ok) {
                android.widget.Toast.makeText(this, "启动失败：授权未激活或底层引擎未就绪", android.widget.Toast.LENGTH_LONG).show();
            }
        }
        finish();
    }
}
