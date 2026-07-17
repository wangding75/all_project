package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;

/**
 * 启动页 Activity
 * 功能：
 *   1. 显示启动 Logo
 *   2. 检测运行环境（是否 Xposed/VirtualApp 环境）
 *   3. 首次运行显示用户协议
 *   4. 校验登录状态，未登录跳转 ActiveCardActivity
 *   5. 已登录跳转 HomeActivity
 *
 * 原始类名：com.loc.va.ui.activity.SplashActivity
 * 入口 Action：android.intent.action.MAIN
 */
public class SplashActivity extends Activity {

    private static final int SPLASH_DELAY = 2000; // 2秒启动页

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // setContentView(R.layout.activity_splash);

        // 检测 Xposed 框架
        if (isXposedInstalled()) {
            showXposedWarning();
            return;
        }

        // 检测是否运行在虚拟环境中
        if (isRunningInVirtualApp()) {
            showVirtualEnvWarning();
            return;
        }

        // 延迟启动
        new Handler().postDelayed(this::navigateToNext, SPLASH_DELAY);
    }

    /**
     * 检测 Xposed 框架是否安装
     */
    private boolean isXposedInstalled() {
        try {
            throw new Exception("StackTrace Check");
        } catch (Exception e) {
            for (StackTraceElement element : e.getStackTrace()) {
                if (element.getClassName().contains("de.robv.android.xposed")) {
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * 检测是否运行在 VirtualApp 虚拟环境中
     */
    private boolean isRunningInVirtualApp() {
        // 通过检测运行进程名或特定文件来判断
        return false; // 实际实现需通过 native 层检测
    }

    private void showXposedWarning() {
        // 提示："您的手机安装了Xposed框架，请卸载后使用"
        finish();
    }

    private void showVirtualEnvWarning() {
        // 提示："当前运行在虚拟环境，请在正常环境下运行本程序"
        finish();
    }

    private void navigateToNext() {
        boolean isLoggedIn = checkLoginStatus();
        Intent intent;
        if (isLoggedIn) {
            intent = new Intent(this, HomeActivity.class);
        } else {
            intent = new Intent(this, ActiveCardActivity.class);
        }
        startActivity(intent);
        finish();
    }

    private boolean checkLoginStatus() {
        // 从 SharedPreferences 读取登录状态
        return getSharedPreferences("user_info", MODE_PRIVATE)
                .getString("token", null) != null;
    }
}
