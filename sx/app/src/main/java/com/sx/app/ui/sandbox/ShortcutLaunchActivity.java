package com.sx.app.ui.sandbox;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import com.sx.app.sandbox.SandboxProvider;

public class ShortcutLaunchActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        String packageName = getIntent().getStringExtra("package_name");
        int userId = getIntent().getIntExtra("user_id", 0);
        
        if (packageName != null) {
            SandboxProvider.getEngine().launch(packageName, userId);
        }
        finish();
    }
}
