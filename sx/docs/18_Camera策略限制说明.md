# Phase 3 虚拟相机覆盖策略与已知限制说明

## 1. 架构与 Hook 覆盖范围

虚拟相机 Hook 作用于沙箱分身进程内（`CameraHook`），支持静态图片源替换与 JPEG 拍照帧替换。

| API 族 | 接口 / 方法 | 策略与行为 | 状态 |
|---|---|---|---|
| **Camera1 预览** | `Camera.setPreviewCallback`<br>`Camera.setOneShotPreviewCallback`<br>`Camera.setPreviewCallbackWithBuffer` | 拦截 `onPreviewFrame(byte[] data, Camera camera)`，将真机 byte 数组替换为根据设定图片转码的 NV21 (YUV420sp) 字节流 | **已实现 (P0)** |
| **Camera1 拍照** | `Camera.takePicture` | 包装 `PictureCallback`（JPEG 路径），在 `onPictureTaken` 回调中将 byte 数组替换为设定图片的 JPEG 编码字节 | **已实现 (P0)** |
| **Camera2 预览** | `ImageReader.acquireLatestImage`<br>`acquireNextImage` | 拦截 Image 缓冲区数据，替换为虚拟 Bitmap 纹理/YUV 字节 | **包含于方案 (P1)** |
| **视频循环** | MediaCodec + SurfaceTexture | MP4 视频逐帧解码并循环输入至预览 Buffer | **P1 (可选扩展)** |

---

## 2. 图像转码与尺寸处理

1. **NV21 转码**：输入的 JPEG/PNG 图片被加载为 Bitmap，自动缩放至目标帧尺寸（默认 640×480 或 1280×720），并转码为标准的 YUV420sp (NV21) 内存帧。
2. **JPEG 捕获**：拍照时直接将压缩后的 JPEG 字节流投递给应用回调，保证第三方 App 读到合法的图片数据。

---

## 3. 已知限制与注意事项

1. **静态图片 vs 动态视频**：当前主路径（P0）使用静态图片生成 NV21 帧流；若 App 依赖硬解码人脸活体检测（如连续微动作），需配置 MP4 视频源（P1 扩展）。
2. **分辨率自适应**：部分硬件相机仅支持特定 Aspect Ratio，在不同机型上可能存在拉伸，系统会自动按 640×480/1280×720 进行双线性采样（Bilinear Scaling）。
3. **安全对抗限制**：对于使用 C/C++ Native 绕过 Java Camera API 直连 NDK AImageReader 的强检应用，Java 层的 Hook 无法完全拦截。
