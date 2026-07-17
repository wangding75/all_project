package com.loc.va.ui.activity;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.hardware.Camera;
import android.os.Bundle;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

/**
 * 虚拟摄像头 Activity
 * 功能：
 *   拦截相机调用，返回预设的图片（而非真实拍摄内容）
 *   主要用于绕过"拍照打卡"类应用的人脸验证/活体检测
 *
 * 工作原理：
 *   1. 通过 VirtualApp 拦截 Camera API 调用
 *   2. 将用户预设的图片作为相机预览帧和拍照结果
 *   3. 支持设置图片来源（相册选取、拍摄的实际照片）
 *
 * 调用入口：
 *   Action: com.xin.h6.image
 *   被 VA 内的 App 调用拍照时自动触发
 *
 * 原始类名：com.loc.va.ui.activity.VirtualCameraActivity
 */
public class VirtualCameraActivity extends Activity implements SurfaceHolder.Callback {

    // 虚拟图片的路径（用户预设）
    private String virtualImagePath;

    // 虚拟相机图片（Bitmap）
    private Bitmap virtualBitmap;

    private SurfaceView surfaceView;
    private SurfaceHolder surfaceHolder;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 从设置中读取虚拟图片路径
        virtualImagePath = getSharedPreferences("virtual_camera", MODE_PRIVATE)
                .getString("image_path", null);

        if (virtualImagePath == null) {
            // "您还没有设置模拟照片，请先设置模拟照片"
            setResult(RESULT_CANCELED);
            finish();
            return;
        }

        loadVirtualImage();
        initCamera();
    }

    /**
     * 加载虚拟图片
     */
    private void loadVirtualImage() {
        // virtualBitmap = BitmapFactory.decodeFile(virtualImagePath);
    }

    /**
     * 初始化相机预览（实际上是展示虚拟图片）
     */
    private void initCamera() {
        // 创建一个 SurfaceView 显示"相机预览"
        // 实际上渲染的是虚拟图片而非真实相机帧
    }

    /**
     * 模拟拍照 - 返回虚拟图片
     */
    private void takeVirtualPhoto() {
        if (virtualBitmap == null) return;

        // 将 Bitmap 保存为临时文件
        // 通过 Intent 返回给调用方（模仿真实拍照结果）
        Intent resultIntent = new Intent();
        // resultIntent.putExtra("data", virtualBitmap);  // 小图
        // resultIntent.putExtra(MediaStore.EXTRA_OUTPUT, uri);  // 大图
        setResult(RESULT_OK, resultIntent);
        finish();
    }

    @Override
    public void surfaceCreated(SurfaceHolder holder) {
        // 显示虚拟图片到 Surface
        if (virtualBitmap != null) {
            android.graphics.Canvas canvas = holder.lockCanvas();
            if (canvas != null) {
                canvas.drawBitmap(virtualBitmap, 0, 0, null);
                holder.unlockCanvasAndPost(canvas);
            }
        }
    }

    @Override
    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {}

    @Override
    public void surfaceDestroyed(SurfaceHolder holder) {}
}
