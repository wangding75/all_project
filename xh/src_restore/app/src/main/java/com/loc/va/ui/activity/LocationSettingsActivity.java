package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/**
 * 虚拟地理位置设置页
 * 功能：
 *   1. 开启/关闭位置模拟总开关
 *   2. 显示当前模拟坐标（纬度、经度）
 *   3. 跳转地图选点
 *   4. 手动输入经纬度
 *   5. 随机位置（在指定范围内随机生成坐标）
 *   6. 全局设置 vs 独立设置（针对单个 App）
 *   7. 启动/停止 FackLocService 服务
 *
 * 原始类名：com.loc.va.ui.activity.LocationSettingsActivity
 * 标题：虚拟地理位置（activity_location_settings）
 */
public class LocationSettingsActivity extends Activity {

    private static final int REQUEST_SELECT_LOCATION = 100;

    // 当前设置的虚拟坐标
    private double virtualLat = 0.0;
    private double virtualLng = 0.0;

    // 随机位置范围（米）
    private int randomRange = 500;

    // 是否是全局模式（true=所有App，false=当前App独立）
    private boolean isGlobalMode = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // setContentView(R.layout.activity_location_settings);

        loadSavedLocation();
        initViews();
        updateLocationDisplay();
    }

    /**
     * 加载之前保存的虚拟位置
     */
    private void loadSavedLocation() {
        // 从 SharedPreferences 读取保存的坐标
    }

    private void initViews() {
        // 初始化所有控件
        // 开关：enable_loc_simulation
        // 坐标显示：virtual_coordinate（纬度 %.8f; 经度 %.8f）
        // 按钮：在地图上选择位置、手动输入、随机位置、启动模拟
    }

    /**
     * 跳转百度地图选点页面
     */
    private void openMapPicker() {
        // 检测是否需要引导开启"模拟位置"开发者选项
        if (!isMockLocationEnabled()) {
            showEnableMockLocationGuide();
            return;
        }
        startActivityForResult(
            new Intent(this, LocationSearchActivity.class),
            REQUEST_SELECT_LOCATION
        );
    }

    /**
     * 手动输入经纬度
     * 纬度范围：-90 ~ 90
     * 经度范围：-180 ~ 180
     */
    private void inputLocationManually() {
        // 弹出输入框，验证格式：input_loc_error
        // "输入内容有误，请检查格式：纬度-90~90，经度-180~180"
    }

    /**
     * 在指定范围内随机生成虚拟位置坐标
     */
    private void generateRandomLocation() {
        // 以当前坐标为中心，在 randomRange 米范围内随机生成新坐标
        double latOffset = (Math.random() - 0.5) * 2 * metersToLatDegree(randomRange);
        double lngOffset = (Math.random() - 0.5) * 2 * metersToLngDegree(randomRange, virtualLat);

        virtualLat += latOffset;
        virtualLng += lngOffset;

        updateLocationDisplay();
    }

    /**
     * 启动位置模拟服务
     */
    private void startLocationSimulation() {
        Intent intent = new Intent(this, com.loc.va.service.FackLocService.class);
        intent.putExtra("lat", virtualLat);
        intent.putExtra("lng", virtualLng);
        startService(intent);

        // 提示：位置模拟中，请在桌面打开应用...
    }

    /**
     * 停止位置模拟服务
     */
    private void stopLocationSimulation() {
        stopService(new Intent(this, com.loc.va.service.FackLocService.class));
    }

    /**
     * 更新界面上的坐标显示
     * 格式：坐标：纬度 %.8f; 经度 %.8f
     */
    private void updateLocationDisplay() {
        String display = String.format("坐标：纬度 %.8f; 经度 %.8f", virtualLat, virtualLng);
        // tvCoordinate.setText(display);
    }

    /**
     * 检测系统是否已开启模拟位置
     */
    private boolean isMockLocationEnabled() {
        // 检测 Settings.Secure.ALLOW_MOCK_LOCATION
        return false;
    }

    /**
     * 显示开启模拟位置引导对话框
     * 步骤：
     *   1. 在设置中，打开开发者选项
     *   2. 找到"选择模拟位置信息应用"
     *   3. 选择本程序
     */
    private void showEnableMockLocationGuide() {
        // 弹窗说明如何开启开发者选项中的模拟位置
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_SELECT_LOCATION && resultCode == RESULT_OK && data != null) {
            virtualLat = data.getDoubleExtra("lat", 0.0);
            virtualLng = data.getDoubleExtra("lng", 0.0);
            updateLocationDisplay();
        }
    }

    private double metersToLatDegree(int meters) {
        return meters / 111000.0;
    }

    private double metersToLngDegree(int meters, double lat) {
        return meters / (111000.0 * Math.cos(Math.toRadians(lat)));
    }
}
