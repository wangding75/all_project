package com.sx.app.ui.sandbox;

import android.os.Bundle;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class ShortcutLaunchActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        String packageName = getIntent().getStringExtra("package_name");
        int userId = getIntent().getIntExtra("user_id", 0);
        
        Toast.makeText(this, "Phase 0 模拟启动 " + packageName + "#" + userId, Toast.LENGTH_LONG).show();
        finish();
    }
}
