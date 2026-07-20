package com.sx.app.sandbox;

import android.app.Application;
import android.content.Context;
import com.sx.app.data.SandboxAppInfo;
import java.util.List;

public interface SandboxEngine {

    /** 宿主 Application 中初始化引擎 */
    void initialize(Application app);

    /** 引擎是否可用 */
    boolean isReady();

    /** 从本机已安装包导入沙箱 */
    InstallResult installFromHost(String packageName);

    /** 从 APK 路径安装（固定失败：Not supported in Phase 0） */
    InstallResult installFromApk(String apkPath);

    /** 卸载虚拟包 */
    boolean uninstall(String packageName, int userId);

    /** 清除分身数据 */
    boolean clearData(String packageName, int userId);

    /** 列出所有已安装的沙箱分身 */
    List<SandboxAppInfo> listInstalled();

    /** 获取指定分身 */
    SandboxAppInfo get(String packageName, int userId);

    /** 判断是否已安装 */
    boolean isInstalled(String packageName, int userId);

    /** 启动分身 */
    boolean launch(String packageName, int userId);

    /** 强停 */
    boolean kill(String packageName, int userId);

    /** 强停所有 */
    void killAll();

    /** 克隆新实例，返回新 userId */
    int clone(String packageName);

    /** 创建快捷方式 */
    boolean createShortcut(Context context, String packageName, int userId);

    /** 重命名 */
    void setDisplayName(String packageName, int userId, String name);
}
