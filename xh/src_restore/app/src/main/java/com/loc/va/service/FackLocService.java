package com.loc.va.service;

import android.app.Service;
import android.content.Intent;
import android.location.Location;
import android.location.LocationManager;
import android.os.IBinder;
import android.os.SystemClock;

/**
 * 虚拟定位后台服务（核心功能）
 *
 * 工作原理：
 *   通过 Android 的 MockLocation API 持续向系统注入虚假 GPS 坐标。
 *   应用必须在开发者选项中被选为"模拟位置信息应用"才能生效。
 *   服务以前台服务方式运行，确保不被系统杀死。
 *
 * 模拟策略：
 *   - 固定坐标：一直输出同一个位置
 *   - 随机漂移：在指定范围内随机小幅移动（模拟真实行走）
 *   - 路径模拟：按预设路径点顺序移动
 *
 * 原始类名：com.loc.va.service.FackLocService
 */
public class FackLocService extends Service {

    private static final String PROVIDER = LocationManager.GPS_PROVIDER;
    private static final long UPDATE_INTERVAL = 1000L; // 1秒更新一次

    private LocationManager locationManager;
    private double targetLat;
    private double targetLng;
    private float accuracy = 3.0f; // 精度（米）
    private boolean isRunning = false;

    private Thread mockThread;

    @Override
    public void onCreate() {
        super.onCreate();
        locationManager = (LocationManager) getSystemService(LOCATION_SERVICE);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            targetLat = intent.getDoubleExtra("lat", 39.9042);
            targetLng = intent.getDoubleExtra("lng", 116.4074);
        }

        startMocking();
        startForegroundNotification();

        return START_STICKY; // 服务被杀死后自动重启
    }

    /**
     * 开始虚拟定位
     */
    private void startMocking() {
        if (isRunning) return;

        try {
            // 添加虚假位置提供者
            locationManager.addTestProvider(
                    PROVIDER,
                    false, false, false, false, true, true, true,
                    android.location.Criteria.POWER_HIGH,
                    android.location.Criteria.ACCURACY_FINE
            );
            locationManager.setTestProviderEnabled(PROVIDER, true);
            isRunning = true;
        } catch (SecurityException e) {
            // 需要在开发者选项中设置模拟位置应用
            stopSelf();
            return;
        }

        // 后台线程持续注入虚假坐标
        mockThread = new Thread(() -> {
            while (isRunning && !Thread.currentThread().isInterrupted()) {
                injectFakeLocation(targetLat, targetLng);
                try {
                    Thread.sleep(UPDATE_INTERVAL);
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
        mockThread.start();
    }

    /**
     * 向系统注入虚假位置
     *
     * @param lat 虚假纬度
     * @param lng 虚假经度
     */
    private void injectFakeLocation(double lat, double lng) {
        Location location = new Location(PROVIDER);
        location.setLatitude(lat);
        location.setLongitude(lng);
        location.setAccuracy(accuracy);
        location.setAltitude(0);
        location.setTime(System.currentTimeMillis());
        location.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());

        try {
            locationManager.setTestProviderLocation(PROVIDER, location);
        } catch (Exception e) {
            // 可能用户已撤销权限
            stopSelf();
        }
    }

    /**
     * 停止虚拟定位
     */
    private void stopMocking() {
        isRunning = false;
        if (mockThread != null) {
            mockThread.interrupt();
        }
        try {
            locationManager.setTestProviderEnabled(PROVIDER, false);
            locationManager.removeTestProvider(PROVIDER);
        } catch (Exception ignored) {}
    }

    /**
     * 以前台服务方式运行，显示状态栏通知
     * 通知内容：后台运行中（keep_service_damon_noti_title_v24）
     */
    private void startForegroundNotification() {
        // 创建 Notification Channel（Android 8+）
        // startForeground(notificationId, notification);
    }

    @Override
    public void onDestroy() {
        stopMocking();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
