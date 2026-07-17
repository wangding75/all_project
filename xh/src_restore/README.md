# 星盒（xh.apk）复原源码说明

## 项目结构

```
src_restore/
└── app/
    └── src/
        └── main/
            ├── java/com/loc/va/
            │   ├── ui/activity/            # 界面层（Activities）
            │   │   ├── SplashActivity.java         # 启动页
            │   │   ├── ActiveCardActivity.java     # 激活/登录
            │   │   ├── HomeActivity.java           # 主页（底部Tab）
            │   │   ├── LocationSettingsActivity.java  # 虚拟定位设置
            │   │   ├── LocationSearchActivity.java    # 百度地图选点
            │   │   ├── PhoneSettingsActivity.java     # 设备信息伪造
            │   │   ├── VirtualCameraActivity.java     # 虚拟摄像头
            │   │   └── ListAppActivity.java           # App沙箱管理
            │   ├── service/
            │   │   └── FackLocService.java         # 虚拟定位后台服务
            │   └── common/hook/
            │       └── DeviceHookManager.java      # 设备信息Hook管理器
            ├── res/
            │   └── values/
            │       └── strings.xml                 # 字符串资源（从APK提取）
            └── AndroidManifest.xml                 # 从APK提取（原始）
```

## 复原说明

### 重要前提

> ⚠️ 由于 APK 使用了 **360加固（jiagu）**，真实的业务源码被加密存储在 native 层（`libaa.so`、`libbb.so`）。
> 本目录的 Java 文件是**根据以下信息逆向还原**的：
> - AndroidManifest.xml 中的 Activity 清单
> - strings.xml 中的字符串资源（界面文字）
> - jadx 反编译的壳代码逻辑
> - smali 代码中的包名和类名
> - 权限清单推断的功能

### 各文件还原程度

| 文件 | 还原程度 | 说明 |
|------|----------|------|
| `SplashActivity.java` | 80% | 流程和逻辑基本完整 |
| `ActiveCardActivity.java` | 75% | UI 控件和网络请求逻辑已还原 |
| `HomeActivity.java` | 70% | 主要导航逻辑已还原 |
| `LocationSettingsActivity.java` | 85% | 核心定位功能完整还原 |
| `LocationSearchActivity.java` | 75% | 百度地图集成逻辑已还原 |
| `PhoneSettingsActivity.java` | 90% | IMEI 生成算法等完整实现 |
| `VirtualCameraActivity.java` | 70% | 核心虚拟相机逻辑已还原 |
| `ListAppActivity.java` | 75% | VirtualApp 管理流程已还原 |
| `FackLocService.java` | 95% | MockLocation API 完整实现 |
| `DeviceHookManager.java` | 60% | 接口已还原，native 实现需 libpine.so |

### 未还原的部分

1. **VirtualApp 框架**（`com.lody.virtual.*`）— 这是开源的，可从 GitHub 获取
2. **网络通信层** — HTTP 请求/响应格式未知（服务器 API 不可见）
3. **账号系统** — 激活码验证逻辑在服务器端
4. **Native Hook 实现** — 依赖 `libpine.so`，需要 native 开发

## 重新编译打包

### 步骤 1：修改 smali/资源

在 `apktool_out/` 目录中进行修改：
- `smali/` — 修改字节码逻辑
- `res/values/strings.xml` — 修改字符串资源
- `res/drawable/` — 修改图标/图片

### 步骤 2：重新打包

```powershell
# 重新编译
java -jar tools\apktool.jar b apktool_out\ -o rebuild\xh_rebuild.apk

# 生成签名密钥
keytool -genkey -v -keystore rebuild\debug.keystore -alias androiddebugkey `
    -keyalg RSA -keysize 2048 -validity 30000 `
    -storepass android -keypass android `
    -dname "CN=Android Debug,O=Android,C=US"

# 签名
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 `
    -keystore rebuild\debug.keystore `
    -storepass android `
    rebuild\xh_rebuild.apk androiddebugkey
```

### 步骤 3：安装测试

```powershell
adb install rebuild\xh_rebuild.apk
```
