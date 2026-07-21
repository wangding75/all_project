# 实机验证已知问题记录 (Real-Device Feedback Log)

## 一、 问题列表

### 问题 1：LSPosed 模块显示未激活
- **现象**：在真机环境安装应用后，LSPosed 框架检测提示闪现 (sx) Xposed 模块未激活或未生效。
- **排查方向（仅记录）**：
  - 需检查 `AndroidManifest.xml` 中的 Xposed 模块声明 (`xposedmodule`, `xposeddescription`, `xposedminversion`)；
  - 需检查 LSPosed 作用域（Scope）选择是否绑定了宿主/目标应用。

### 问题 2：沙盒调起提示“启动失败：授权未激活或底层引擎没有启动”
- **现象**：在真机上试图调起谷歌浏览器 (Chrome) / 夸克浏览器时，弹窗提示 `启动失败：授权未激活或底层引擎未就绪`。
- **排查方向（仅记录）**：
  - `SandboxEngine.launch()` 返回 `false` 的两项硬性条件：
    1. `mReady == false`（即 `BlackBoxCore.get().doCreate()` 在真机架构或特定权限下发生 Exception/Initialization Failure，导致引擎未处于 ready 状态）；
    2. 授权判定在多 Context / Application 隔离下未同步拿到激活状态。

---

> **注**：本文档仅用于记录实机反馈问题，遵守“先记录问题不做任何开发”的操作规程。
