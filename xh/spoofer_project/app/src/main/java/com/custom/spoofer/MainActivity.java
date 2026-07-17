package com.custom.spoofer;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import android.graphics.Color;
import android.view.Gravity;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        TextView tv = new TextView(this);
        tv.setText("🌟 Custom Spoofer Xposed Module 🌟\n\n[已成功安装到系统]\n\n请在 LSPosed 管理端中:\n1. 启用本模块\n2. 勾选星盒 (com.xin.h6) 为本模块作用域\n3. 重启星盒应用以生效");
        tv.setTextSize(18);
        tv.setTextColor(Color.BLACK);
        tv.setGravity(Gravity.CENTER);
        tv.setPadding(30, 30, 30, 30);
        
        setContentView(tv);
    }
}
