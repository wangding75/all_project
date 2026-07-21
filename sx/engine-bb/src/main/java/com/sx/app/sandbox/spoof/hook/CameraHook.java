package com.sx.app.sandbox.spoof.hook;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.hardware.Camera;
import android.util.Log;

import com.sx.app.data.CameraConfig;

import java.io.ByteArrayOutputStream;
import java.io.File;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XC_MethodHook.MethodHookParam;
import de.robv.android.xposed.XposedHelpers;

public class CameraHook {

    private static final String TAG = "SX-CameraHook";
    private static CameraConfig sConfig;
    private static byte[] sNv21Frame;
    private static byte[] sJpegData;
    private static int mFrameWidth = 640;
    private static int mFrameHeight = 480;

    public static void install(ClassLoader classLoader, CameraConfig config) {
        if (config == null || !config.enabled) return;
        sConfig = config;
        prepareFakeMediaData();

        try {
            // 1. Camera1 PreviewCallback Hooks
            XposedHelpers.findAndHookMethod(Camera.class, "setPreviewCallback", Camera.PreviewCallback.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled && param.args[0] != null) {
                        final Camera.PreviewCallback original = (Camera.PreviewCallback) param.args[0];
                        param.args[0] = new Camera.PreviewCallback() {
                            @Override
                            public void onPreviewFrame(byte[] data, Camera camera) {
                                byte[] fakeData = getFakeNv21Data(data != null ? data.length : 0);
                                original.onPreviewFrame(fakeData, camera);
                            }
                        };
                    }
                }
            });

            XposedHelpers.findAndHookMethod(Camera.class, "setOneShotPreviewCallback", Camera.PreviewCallback.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled && param.args[0] != null) {
                        final Camera.PreviewCallback original = (Camera.PreviewCallback) param.args[0];
                        param.args[0] = new Camera.PreviewCallback() {
                            @Override
                            public void onPreviewFrame(byte[] data, Camera camera) {
                                byte[] fakeData = getFakeNv21Data(data != null ? data.length : 0);
                                original.onPreviewFrame(fakeData, camera);
                            }
                        };
                    }
                }
            });

            XposedHelpers.findAndHookMethod(Camera.class, "setPreviewCallbackWithBuffer", Camera.PreviewCallback.class, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (sConfig != null && sConfig.enabled && param.args[0] != null) {
                        final Camera.PreviewCallback original = (Camera.PreviewCallback) param.args[0];
                        param.args[0] = new Camera.PreviewCallback() {
                            @Override
                            public void onPreviewFrame(byte[] data, Camera camera) {
                                byte[] fakeData = getFakeNv21Data(data != null ? data.length : 0);
                                original.onPreviewFrame(fakeData, camera);
                            }
                        };
                    }
                }
            });

            // 2. Camera1 takePicture Hook
            XposedHelpers.findAndHookMethod(Camera.class, "takePicture",
                    Camera.ShutterCallback.class,
                    Camera.PictureCallback.class,
                    Camera.PictureCallback.class,
                    Camera.PictureCallback.class,
                    new XC_MethodHook() {
                        @Override
                        protected void beforeHookedMethod(MethodHookParam param) {
                            if (sConfig != null && sConfig.enabled) {
                                final Camera.PictureCallback originalJpeg = (Camera.PictureCallback) param.args[3];
                                if (originalJpeg != null) {
                                    param.args[3] = new Camera.PictureCallback() {
                                        @Override
                                        public void onPictureTaken(byte[] data, Camera camera) {
                                            byte[] fakeJpeg = getFakeJpegData(data);
                                            originalJpeg.onPictureTaken(fakeJpeg, camera);
                                        }
                                    };
                                }
                            }
                        }
                    });

            Log.d(TAG, "CameraHook installed successfully.");
        } catch (Throwable e) {
            Log.e(TAG, "Failed to install CameraHook", e);
        }
    }

    private static void prepareFakeMediaData() {
        if (sConfig == null || sConfig.mediaPath == null || sConfig.mediaPath.isEmpty()) {
            return;
        }
        try {
            File file = new File(sConfig.mediaPath);
            if (!file.exists()) {
                Log.w(TAG, "Media file does not exist: " + sConfig.mediaPath);
                return;
            }

            Bitmap bitmap = BitmapFactory.decodeFile(file.getAbsolutePath());
            if (bitmap != null) {
                // Scale bitmap to frame dimensions
                Bitmap scaled = Bitmap.createScaledBitmap(bitmap, mFrameWidth, mFrameHeight, true);

                // Convert to JPEG bytes for takePicture
                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                scaled.compress(Bitmap.CompressFormat.JPEG, 90, baos);
                sJpegData = baos.toByteArray();

                // Convert to NV21 YUV420sp for preview frame
                sNv21Frame = getNV21(mFrameWidth, mFrameHeight, scaled);
                Log.d(TAG, "Prepared fake camera media bytes, jpegLen=" + (sJpegData != null ? sJpegData.length : 0) + ", nv21Len=" + (sNv21Frame != null ? sNv21Frame.length : 0));
            }
        } catch (Throwable e) {
            Log.e(TAG, "Error preparing fake media data", e);
        }
    }

    private static byte[] getFakeNv21Data(int requestedLength) {
        if (sNv21Frame != null && sNv21Frame.length > 0) {
            return sNv21Frame;
        }
        int len = requestedLength > 0 ? requestedLength : (mFrameWidth * mFrameHeight * 3 / 2);
        return new byte[len];
    }

    private static byte[] getFakeJpegData(byte[] originalData) {
        if (sJpegData != null && sJpegData.length > 0) {
            return sJpegData;
        }
        return originalData != null ? originalData : new byte[0];
    }

    private static byte[] getNV21(int inputWidth, int inputHeight, Bitmap scaled) {
        int[] argb = new int[inputWidth * inputHeight];
        scaled.getPixels(argb, 0, inputWidth, 0, 0, inputWidth, inputHeight);
        byte[] yuv = new byte[inputWidth * inputHeight * 3 / 2];
        encodeYUV420SP(yuv, argb, inputWidth, inputHeight);
        return yuv;
    }

    private static void encodeYUV420SP(byte[] yuv420sp, int[] argb, int width, int height) {
        final int frameSize = width * height;
        int yIndex = 0;
        int uvIndex = frameSize;
        int a, R, G, B, Y, U, V;
        int index = 0;
        for (int j = 0; j < height; j++) {
            for (int i = 0; i < width; i++) {
                a = (argb[index] & 0xff000000) >> 24;
                R = (argb[index] & 0xff0000) >> 16;
                G = (argb[index] & 0xff00) >> 8;
                B = (argb[index] & 0xff);

                Y = ((66 * R + 129 * G + 25 * B + 128) >> 8) + 16;
                U = ((-38 * R - 74 * G + 112 * B + 128) >> 8) + 128;
                V = ((112 * R - 94 * G - 18 * B + 128) >> 8) + 128;

                yuv420sp[yIndex++] = (byte) ((Y < 0) ? 0 : ((Y > 255) ? 255 : Y));
                if (j % 2 == 0 && index % 2 == 0) {
                    yuv420sp[uvIndex++] = (byte) ((V < 0) ? 0 : ((V > 255) ? 255 : V));
                    yuv420sp[uvIndex++] = (byte) ((U < 0) ? 0 : ((U > 255) ? 255 : U));
                }
                index++;
            }
        }
    }
}
