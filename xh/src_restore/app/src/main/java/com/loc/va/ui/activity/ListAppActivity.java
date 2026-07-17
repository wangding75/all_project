package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;
import android.widget.PopupMenu;

import java.util.ArrayList;
import java.util.List;

/**
 * 已安装 App 列表页（VirtualApp 沙箱管理）
 * 功能：
 *   1. 显示已添加到 VirtualApp 沙箱的所有 App
 *   2. 点击 App 图标启动（在沙箱内运行）
 *   3. 长按菜单：
 *      - 启动
 *      - 添加新应用
 *      - 克隆 App（多开）
 *      - 卸载应用
 *      - 清除数据
 *      - 创建快捷方式
 *      - 独立设置（为这个 App 单独配置虚拟参数）
 *      - 重命名
 *
 * 原始类名：com.loc.va.ui.activity.ListAppActivity
 */
public class ListAppActivity extends Activity {

    private ListView lvApps;
    private View btnAddApp;

    // 已安装的应用列表（VirtualApp 内）
    private List<ApplicationInfo> installedApps = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // setContentView(R.layout.activity_list_app);

        loadInstalledApps();
        initViews();
    }

    /**
     * 加载 VirtualApp 沙箱内已安装的 App 列表
     */
    private void loadInstalledApps() {
        // 通过 VirtualApp API 获取已安装的虚拟包
        // installedApps = VirtualCore.get().getInstalledApps(0);

        if (installedApps.isEmpty()) {
            // 显示空状态："您还没有添加任何程序哦~~"
        }
    }

    private void initViews() {
        // lvApps = findViewById(R.id.lv_apps);
        // btnAddApp = findViewById(R.id.btn_add_app);

        // 点击启动 App
        // lvApps.setOnItemClickListener((parent, view, position, id) -> {
        //     launchApp(installedApps.get(position));
        // });

        // 长按显示菜单
        // lvApps.setOnItemLongClickListener((parent, view, position, id) -> {
        //     showAppMenu(view, position);
        //     return true;
        // });

        // 添加新 App
        // btnAddApp.setOnClickListener(v -> addNewApp());
    }

    /**
     * 启动沙箱内的 App
     */
    private void launchApp(ApplicationInfo appInfo) {
        // VirtualCore.get().launchApp(appInfo.packageName, 0);
        // 如果是64位App需要提示安装插件（install_arm_plugin）
    }

    /**
     * 添加新 App 到沙箱
     * 支持：
     *   1. 选择手机已安装的 App（克隆）
     *   2. 选择本地 APK 文件安装
     * 注意：不能一次性安装超过9个App（install_too_much_once_time）
     */
    private void addNewApp() {
        Intent intent = new Intent(this, ListAppActivity2.class);
        startActivity(intent);
    }

    /**
     * 显示 App 操作菜单
     */
    private void showAppMenu(View anchorView, int position) {
        PopupMenu popup = new PopupMenu(this, anchorView);
        // popup.getMenuInflater().inflate(R.menu.menu_app_item, popup.getMenu());
        // popup.setOnMenuItemClickListener(item -> { ... });
        popup.show();
    }

    /**
     * 卸载 App（从沙箱中移除）
     */
    private void uninstallApp(String packageName) {
        // 弹窗确认："是否移除应用 %s ?"
        // VirtualCore.get().uninstallPackage(packageName, 0);
    }

    /**
     * 清除 App 数据
     */
    private void clearAppData(String packageName) {
        // 弹窗确认："是否清除应用数据 %s ?"
        // VirtualCore.get().clearPackage(packageName, 0);
    }

    /**
     * 为指定 App 单独配置虚拟参数
     */
    private void openAppSettings(String packageName) {
        // 弹窗："您是否要对%s进行单独虚拟设置"
        // 跳转到独立设置页
        Intent intent = new Intent(this, LocationSettingsActivity.class);
        intent.putExtra("package_name", packageName);
        intent.putExtra("is_app_mode", true);
        startActivity(intent);
    }

    /**
     * 创建桌面快捷方式
     */
    private void createShortcut(ApplicationInfo appInfo) {
        // 在桌面创建该沙箱 App 的快捷方式
    }
}
