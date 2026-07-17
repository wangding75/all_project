# 星盒 App 业务源码代码地图 (Code Map)

本文档旨在梳理脱壳后的 `src_clean` 业务源码，帮助你快速理清整体架构、混淆类的真实命名映射以及核心功能对应的代码位置。

---

## 一、 核心技术点警示：VMP 方法保护 (Native 编译)

在阅读源码时，你会发现很多类（如 `HomeFragment`、`PhoneSettingsActivity` 等）的核心方法（如 `onCreate`、`onClick` 等）都只有一行声明：
```java
public native void onClick(View view);
private native void C0();
```
同时在类的静态代码块（`static`）中存在：
```java
Loader.registerNativesForClass(54);
```

> [!IMPORTANT]
> **原理解析**：这是 360 加固的 **VMP（虚拟机方法保护 / Native 编译）** 机制。
> 加固在打包时，将这些关键 Java 方法的字节码翻译成了 C/C++ 代码，并编译进了 Native 动态链接库（`libjiagu.so`）中。在运行时通过 `Loader.registerNatives` 动态注册到虚拟机。
> **这意味着**：这部分被 VMP 保护的函数，在 DEX 文件中**本来就没有 Java 字节码**。无论用何种脱壳工具，我们都只能看到 `native` 声明。其真正的执行逻辑都在 C/C++ 层的 `.so` 文件中。

---

## 二、 核心混淆类真实命名映射 (Deobfuscation Mapping)

由于混淆器（R8/Proguard）去除了部分调试信息，我们无法直接物理重命名文件（强行重命名会导致数千个 `import` 和引用报错失效，导致工程彻底瘫痪）。你可以通过下表进行代码阅读时的命名对照：

### 1. 通用辅助类 (Common & Utils)
| 混淆文件名 | 所在目录 | 继承关系 / 接口 | 真实推测命名 | 功能与作用描述 |
| :--- | :--- | :--- | :--- | :--- |
| `a.java` | `com/loc/va/common/activity` | `extends Fragment` | `BaseFragment` | 基础 Fragment 类，封装了通用的 Dialog 弹出、加载动画 `SpotsDialog2` 的逻辑。 |
| `BaseActivity.java` | `com/loc/va/common/activity` | `extends AppCompatActivity` | `BaseActivity` | 基础 Activity 类，封装了全局权限申请、状态栏管理等。 |

### 2. 主页面业务类 (Main / Home Module)
| 混淆文件名 | 所在目录 | 继承关系 / 接口 | 真实推测命名 | 功能与作用描述 |
| :--- | :--- | :--- | :--- | :--- |
| `HomeContract.java` | `com/loc/va/ui/activity` | - | `HomeContract` | **主页 MVP 契约接口**。定义了 `HomeView`（主页视图接口，包含加载 App 列表、弹框）和 `HomePresenter`（添加/删除分身、启动 App 接口）。 |
| `n0.java` | `com/loc/va/ui/activity` | `implements HomePresenter` | `HomePresenterImpl` | **主页业务控制实现类**。包含具体的添加 App 分身、从容器删除 App、启动分身 App 的逻辑。 |
| `HomeFragment.java` | `com/loc/va/ui/activity` | `implements HomeView` | `HomeFragment` | **主页核心 UI 界面**。控制 Banner 轮播图，展示分身应用列表的 GridView，处理应用点击启动。 |

---

## 三、 业务功能与代码位置地图 (Business Mapping)

根据你的逆向目的，你可以直接前往以下代码位置阅读对应的未混淆入口文件：

### 1. 核心功能入口
* **应用启动与权限校验**：
  * [SplashActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/SplashActivity.java) (闪屏/欢迎页，在这里进行加固层后的初始化、权限申请拦截)。
* **多开容器主架构**：
  * [MainActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/MainActivity.java) (主页面承载器，负责初始化分身运行环境，切换 Home 页面与个人中心)。

### 2. 伪装与定位业务 (主要逆向分析对象)
* **虚拟定位 (位置伪装)**：
  * **主界面**：[LocationSettingsActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/LocationSettingsActivity.java)
  * **位置搜索**：[LocationSearchActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/LocationSearchActivity.java)
  * **后台代理服务**：[FackLocService.java](file:///D:/github/xh/src_clean/sources/com/loc/va/service/FackLocService.java) (通过它欺骗系统 GPS API)。
* **手机硬件信息伪装 (设备伪装)**：
  * **设备参数设置**：[PhoneSettingsActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/PhoneSettingsActivity.java) (修改 IMEI、IMSI、手机型号、MAC 地址等参数，以防风控检测)。
* **虚拟网络伪装 (Wifi/蓝牙伪装)**：
  * **Wifi 伪装**：[WifiSettingsActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/WifiSettingsActivity.java) (伪装 SSID、BSSID，规避 Wifi 地理位置风控)。
  * **蓝牙伪装**：[BluetootSettingsActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/BluetootSettingsActivity.java)
* **虚拟多媒体拦截 (相机/相册/视频伪装)**：
  * **虚拟相机拦截**：[VirtualCameraActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/VirtualCameraActivity.java) (劫持 Camera API，将摄像头画面替换为预设视频或图片)。
  * **虚拟相册设置**：[ImageSettingsActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/ImageSettingsActivity.java)
  * **视频伪装设置**：[VideoSettingsActivity.java](file:///D:/github/xh/src_clean/sources/com/loc/va/ui/activity/VideoSettingsActivity.java)

---

## 四、 阅读与还原技巧

由于大量的逻辑被下放到了 Native 层的 `libjiagu.so` 或 `libaa.so` 等二进制库中，如果你需要分析这部分 native 函数：
1. **获取 SO 库**：使用 `Apktool` 提取出的 [lib](file:///D:/github/xh/apktool_out/lib/) 目录，进入 `arm64-v8a`，找到对应的加密 `.so` 文件。
2. **静态分析**：使用 **IDA Pro** 载入该 `.so` 文件。
3. **定位函数**：在 IDA 中搜索 `Java_` 前缀的导出函数，或者在 `JNI_OnLoad` 中寻找动态绑定的 Native 函数列表，即可对应上如 `C0`、`D0` 等被混淆的 native 方法。
