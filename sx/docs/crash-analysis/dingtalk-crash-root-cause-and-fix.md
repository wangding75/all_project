# 钉钉 (DingTalk) 闪现多开崩溃定位、根因分析与修复报告

## 1. 问题现象 (Problem Description)

在闪现（Shanxian / BlackBox 容器）中：
- Markor、Tasks、夸克浏览器可正常多开与稳定运行。
- 钉钉（`com.alibaba.android.rimet`）在闪现内打开时**无法正常稳定多开，频繁发生崩溃闪退**（启动后 8~30 秒内必定发生退出/闪退）。

---

## 2. 诊断排查与 Tombstone 日志分析

1. **Native Tombstone 崩溃栈**：
   ```text
   pid: 3434, tid: 3443, name: HeapTaskDaemon  >>> com.alibaba.android.rimet <<<
   signal 11 (SIGSEGV), code 128 (SI_KERNEL), fault addr 0x0
   backtrace:
         #00 pc 000000000041e6ec  /apex/com.android.art/lib64/libart.so (art::ArtMethod::GetOatQuickMethodHeader(unsigned long)+28)
         #01 pc 000000000084f570  /apex/com.android.art/lib64/libart.so (void art::StackVisitor::WalkStack<(art::StackVisitor::CountTransitions)1>(bool)+480)
         #02 pc 00000000008922bf  /apex/com.android.art/lib64/libart.so (art::Thread::VisitRoots(art::RootVisitor*, art::VisitRootFlags)+2975)
         #03 pc 00000000004efd4d  /apex/com.android.art/lib64/libart.so (art::gc::collector::ConcurrentCopying::ThreadFlipVisitor::Run(art::Thread*)+301)
         #04 pc 000000000089e501  /apex/com.android.art/lib64/libart.so (art::ThreadList::FlipThreadRoots...)
   ```
2. **根因归因**：
   - **`RuntimeHook.cpp` JNI 局部引用泄露**：钉钉在启动与运行期间频繁通过 `System.load` / `nativeLoad` 动态加载 `.so` 插件（如 `libweexjsb.so`、`libwebviewuc.so`、`libxquic.so` 等）。C++ 层 `RuntimeHook.cpp` 调用 `IO::redirectPath(env, name)` 生成了新的 JNI `jstring`，但缺失了 `if (redirect && redirect != name) env->DeleteLocalRef(redirect);`。这导致 JNI 局部引用表溢出、破坏 ART 垃圾回收堆指针，使 `HeapTaskDaemon` 在进行 `ConcurrentCopying` GC 遍历 Stack 帧时触发 `SIGSEGV`。
   - **`IOCore.java` Android Device Protected Storage 重定向缺失**：未配置 `/data/user_de/%d/%s` 重定向规则，导致多开（User ID 1+）环境下的设备加密存储路径无法透明重定向。
   - **`RuntimeHook.cpp` / `VMClassLoaderHook.cpp` 空指针安全隐患**：缺少针对 `GetStringUTFChars` 返回 NULL 的非空保护。

---

## 3. 代码修复方案 (Fixes Applied)

1. [RuntimeHook.cpp](../../blackbox/Bcore/src/main/cpp/Hook/RuntimeHook.cpp)：
   - 补齐 `if (redirect && redirect != name) env->DeleteLocalRef(redirect);` 释放 JNI 局部引用。
   - 增加 `if (nameC)` 非空保护。
2. [VMClassLoaderHook.cpp](../../blackbox/Bcore/src/main/cpp/Hook/VMClassLoaderHook.cpp)：
   - 增加 `nameC` 非空校验。
3. [IOCore.java](../../blackbox/Bcore/src/main/java/top/niunaijun/blackbox/core/IOCore.java)：
   - 添加 `rule.put(String.format("/data/user_de/%d/%s", systemUserId, packageName), packageInfo.dataDir);`，支持高版本 Android 多用户存储隔离。
4. [test-dingtalk-stability.ps1](../../tools/dingtalk-automation/test-dingtalk-stability.ps1)：
   - 自动跑满连续 3 轮 x 20 分钟（1200 秒/轮）长效观察，包含进程存活校验与界面截图存盘 (`screenshot_run<N>.png`)。

---

## 4. 自动化测试与任务停止条件

- **停止条件**：
  1. 钉钉进程在 (`ps -ef | grep rimet`)
  2. 截图模拟器首页显示的是钉钉 (包含 UI Screen & Focus Window 校验)
  3. 连续 3 次启动都可以稳定运行 20 分钟 (Total 60 分钟)
