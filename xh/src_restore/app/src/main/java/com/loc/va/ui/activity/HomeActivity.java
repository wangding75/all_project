package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/**
 * 主页 Activity（底部 Tab 导航）
 * 功能：
 *   1. 底部 Tab：首页、我的应用（App列表）、我的（用户信息）
 *   2. 顶部菜单：账号管理、GMS框架、机型模拟、设置
 *   3. 清理后台 App
 *   4. 版本更新检测
 *   5. 快速切换虚拟定位开关
 *
 * 原始类名：com.loc.va.ui.activity.HomeActivity
 */
public class HomeActivity extends Activity {

    // Tab 索引
    public static final int TAB_HOME = 0;
    public static final int TAB_MY_APPS = 1;
    public static final int TAB_ME = 2;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // setContentView(R.layout.activity_home);

        initBottomNav();
        checkUpdate();
    }

    private void initBottomNav() {
        // 初始化底部导航 Tab
        // 首页 (home_page)
        // 我的应用 (my_apps)
        // 我的 (me)
    }

    /**
     * 进入 App 列表（我的应用）
     * 展示已添加到 VirtualApp 沙箱的所有 App
     */
    private void goToMyApps() {
        startActivity(new Intent(this, ListAppActivity.class));
    }

    /**
     * 进入虚拟设置中心
     * 包含：位置模拟、设备信息、相机、WiFi、蓝牙等模拟设置
     */
    private void goToVirtualSettings() {
        startActivity(new Intent(this, LocationSettingsActivity.class));
    }

    /**
     * 检测新版本
     */
    private void checkUpdate() {
        // 网络请求：GET /api/check_update
        // 有新版本时弹窗提示升级
    }

    /**
     * 清理 VirtualApp 沙箱内后台运行的 App
     */
    private void killAllApps() {
        // 调用 VirtualApp API 清理后台
    }

    /**
     * 顶部菜单 - 账号管理（多账号切换）
     */
    private void openAccountManager() {
        // 打开账号管理页
    }

    /**
     * 顶部菜单 - Google GMS 框架
     */
    private void openGmsSettings() {
        // 打开 WebView 引导安装 GMS
        Intent intent = new Intent(this, WebViewActivity.class);
        startActivity(intent);
    }

    /**
     * 顶部菜单 - 机型模拟
     */
    private void openPhoneSimulation() {
        startActivity(new Intent(this, PhoneSettingsActivity.class));
    }
}
