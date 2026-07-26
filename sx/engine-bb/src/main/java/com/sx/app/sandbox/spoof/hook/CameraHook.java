package com.sx.app.sandbox.spoof.hook;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.hardware.Camera;
import android.media.MediaMetadataRetriever;
import android.util.Log;

import com.sx.app.data.CameraConfig;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.nio.ByteBuffer;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XC_MethodHook.MethodHookParam;
import de.robv.android.xposed.XposedHelpers;

public class CameraHook {

    private static final String TAG = "SX-CameraHook";
    private static CameraConfig sConfig;
    private static volatile byte[] sNv21Frame;
    private static volatile byte[] sJpegData;
    private static int mFrameWidth = 640;
    private static int mFrameHeight = 480;
    private static volatile boolean sIsVideoLoopRunning = false;
    private static volatile boolean sPlaneHooksInstalled = false;

    /** Hot-refresh config without re-installing hooks. */
    public static void updateConfig(CameraConfig config) {
        sConfig = config;
    }

    public static void install(android.content.Context context, ClassLoader classLoader, CameraConfig config) {
        if (config == null || !config.enabled) return;
        sConfig = config;

        boolean isVideo = CameraConfig.TYPE_VIDEO.equalsIgnoreCase(sConfig.sourceType)
                          || (sConfig.mediaPath != null && sConfig.mediaPath.toLowerCase().endsWith(".mp4"));

        if (isVideo) {
            startVideoLoopPlayer(context);
        } else {
            prepareFakeMediaData(context);
        }

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

            // 3. Camera2 ImageReader: hook Image.getPlanes / Plane.getBuffer once (no per-frame re-hook)
            try {
                installCamera2PlaneHooksOnce();
                Class<?> imageReaderClass = Class.forName("android.hardware.camera2.ImageReader");
                // acquire hooks only need to exist so Image objects flow through our plane hooks;
                // no nested findAndHookMethod here.
                XC_MethodHook imageAcquireHook = new XC_MethodHook() {
                    @Override
                    protected void afterHookedMethod(MethodHookParam param) {
                        // Intentionally empty: plane/buffer hooks replace data when clients read Image.
                    }
                };
                XposedHelpers.findAndHookMethod(imageReaderClass, "acquireLatestImage", imageAcquireHook);
                XposedHelpers.findAndHookMethod(imageReaderClass, "acquireNextImage", imageAcquireHook);
                Log.d(TAG, "Camera2 ImageReader hooks installed.");
            } catch (Throwable t) {
                Log.w(TAG, "Camera2 ImageReader hook unavailable", t);
            }

            Log.d(TAG, "CameraHook installed successfully (Camera1 + Camera2 + VideoLoop).");
        } catch (Throwable e) {
            Log.e(TAG, "Failed to install CameraHook", e);
        }
    }

    private static synchronized void installCamera2PlaneHooksOnce() {
        if (sPlaneHooksInstalled) {
            return;
        }
        try {
            Class<?> imageClass = Class.forName("android.media.Image");
            XposedHelpers.findAndHookMethod(imageClass, "getPlanes", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam paramPlanes) {
                    if (sConfig == null || !sConfig.enabled) {
                        return;
                    }
                    byte[] fakeNv21 = getFakeNv21Data(0);
                    if (fakeNv21 == null || fakeNv21.length == 0) {
                        return;
                    }
                    Object[] planes = (Object[]) paramPlanes.getResult();
                    if (planes == null || planes.length == 0) {
                        return;
                    }
                    // Replace plane0 buffer content via already-installed Plane.getBuffer hook.
                    // Stash frame on thread-local for getBuffer after-hook.
                    sPendingPlaneBytes.set(fakeNv21);
                }
            });
            Class<?> planeClass = Class.forName("android.media.Image$Plane");
            XposedHelpers.findAndHookMethod(planeClass, "getBuffer", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam paramBuffer) {
                    if (sConfig == null || !sConfig.enabled) {
                        return;
                    }
                    byte[] fake = sPendingPlaneBytes.get();
                    if (fake != null && fake.length > 0) {
                        paramBuffer.setResult(ByteBuffer.wrap(fake));
                    }
                }
            });
            sPlaneHooksInstalled = true;
            Log.d(TAG, "Camera2 Image/Plane hooks installed once.");
        } catch (Throwable t) {
            Log.w(TAG, "Failed to install Camera2 plane hooks once", t);
        }
    }

    private static final ThreadLocal<byte[]> sPendingPlaneBytes = new ThreadLocal<>();

    private static void startVideoLoopPlayer(android.content.Context context) {
        if (sConfig == null || sConfig.mediaPath == null || sConfig.mediaPath.isEmpty()) return;
        if (sIsVideoLoopRunning) return;
        sIsVideoLoopRunning = true;

        new Thread(() -> {
            Log.d(TAG, "Starting MP4 Video Loop Player for path: " + sConfig.mediaPath);
            MediaMetadataRetriever retriever = new MediaMetadataRetriever();
            try {
                File f = new File(sConfig.mediaPath);
                if (f.exists() && f.canRead()) {
                    retriever.setDataSource(f.getAbsolutePath());
                } else {
                    retriever.setDataSource(sConfig.mediaPath);
                }
                String durStr = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION);
                long durationMs = durStr != null ? Long.parseLong(durStr) : 5000L;
                long currentUs = 0L;
                long stepUs = 33000L; // ~30 fps

                while (sConfig != null && sConfig.enabled && sIsVideoLoopRunning) {
                    try {
                        Bitmap frame = retriever.getFrameAtTime(currentUs, MediaMetadataRetriever.OPTION_CLOSEST);
                        if (frame != null) {
                            Bitmap scaled = Bitmap.createScaledBitmap(frame, mFrameWidth, mFrameHeight, true);
                            ByteArrayOutputStream baos = new ByteArrayOutputStream();
                            scaled.compress(Bitmap.CompressFormat.JPEG, 90, baos);
                            sJpegData = baos.toByteArray();
                            sNv21Frame = getNV21(mFrameWidth, mFrameHeight, scaled);
                        }
                    } catch (Throwable t) {
                        Log.w(TAG, "Error fetching video frame at " + currentUs + "us", t);
                    }
                    currentUs += stepUs;
                    if (currentUs >= durationMs * 1000L) {
                        currentUs = 0L;
                    }
                    try {
                        Thread.sleep(33);
                    } catch (InterruptedException e) {
                        break;
                    }
                }
            } catch (Throwable t) {
                Log.e(TAG, "VideoLoopPlayer encountered error", t);
            } finally {
                try {
                    retriever.release();
                } catch (Throwable ignored) {}
                sIsVideoLoopRunning = false;
            }
        }, "SX-VideoLoopPlayer").start();
    }

    private static void prepareFakeMediaData(android.content.Context context) {
        if (sConfig == null || sConfig.mediaPath == null || sConfig.mediaPath.isEmpty()) {
            return;
        }
        try {
            Bitmap bitmap = null;
            File file = new File(sConfig.mediaPath);
            if (file.exists() && file.canRead()) {
                bitmap = BitmapFactory.decodeFile(file.getAbsolutePath());
            } else if (context != null) {
                try {
                    String hostPkg = top.niunaijun.blackbox.BlackBoxCore.getHostPkg();
                    if (hostPkg == null || hostPkg.isEmpty()) {
                        hostPkg = context.getPackageName();
                    }
                    android.net.Uri providerUri = android.net.Uri.parse("content://" + hostPkg + ".config.provider");
                    android.os.Bundle extras = new android.os.Bundle();
                    extras.putString("path", sConfig.mediaPath);
                    android.os.Bundle reply = context.getContentResolver().call(providerUri, "get_camera_bytes", null, extras);
                    if (reply != null) {
                        byte[] rawBytes = reply.getByteArray("camera_bytes");
                        if (rawBytes != null && rawBytes.length > 0) {
                            bitmap = BitmapFactory.decodeByteArray(rawBytes, 0, rawBytes.length);
                            Log.d(TAG, "Loaded camera media bytes via ConfigProvider fallback, bytes=" + rawBytes.length);
                        }
                    }
                } catch (Throwable t) {
                    Log.w(TAG, "Failed to fetch camera bytes from ConfigProvider fallback", t);
                }
            }

            if (bitmap != null) {
                Bitmap scaled = Bitmap.createScaledBitmap(bitmap, mFrameWidth, mFrameHeight, true);
                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                scaled.compress(Bitmap.CompressFormat.JPEG, 90, baos);
                sJpegData = baos.toByteArray();
                sNv21Frame = getNV21(mFrameWidth, mFrameHeight, scaled);
                Log.d(TAG, "Prepared fake camera media bytes, jpegLen=" + (sJpegData != null ? sJpegData.length : 0) + ", nv21Len=" + (sNv21Frame != null ? sNv21Frame.length : 0));
            } else {
                Log.w(TAG, "Could not load camera bitmap from path: " + sConfig.mediaPath);
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
