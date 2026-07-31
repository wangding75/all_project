# 夸克浏览器（Quark Browser）崩溃定位、根因分析与修复知识库

## 1. 问题背景 (Problem Description)

在闪现（SX / BlackBox 容器）中多开运行 App 时：
- Markor、Tasks 等普通应用多开运行正常。
- 夸克浏览器（`com.quark.browser`）无法正常稳定多开。
- **稳定复现现象**：在闪现内打开夸克浏览器，进入首页约 25–30 秒左右，稳定发生崩溃闪退。

---

## 2. 诊断排查过程 (Diagnostic Workflow)

1. **自动化采集**：使用自动化诊断驱动程序 (`tools/quark-automation/run-quark-diagnostics.ps1`) 分别在系统直连 (Q0) 与 闪现容器 (Q1/Q2) 下采集日志。
2. **崩溃日志与 Tombstone 分析**：
   - 查看 `logcat-crash.txt` 与内核 Tombstone，定位到崩溃发生于 UC WebView 的后台工作线程 `ThreadPoolForeg`。
   - 核心报错 1：Bionic 内存分配器断言失败 `bionic/libc/bionic/bionic_allocator.cpp:118: alloc CHECK 'page->free_block_list != nullptr' failed`。
   - 核心报错 2：原生信号 `SIGSEGV` code 128 (`SI_KERNEL`), 堆栈回溯指向 `/system/lib64/libexpat.so (parserCreate+33)`。

---

## 3. 四大核心根因与技术细节 (Core Root Causes)

### 3.1 JNI 局部引用泄漏导致 Native 堆内存爆表 (核心主因)
- **原理**：`UnixFileSystemHook.cpp` 和 `RuntimeHook.cpp` 拦截文件与动态库加载时，每次重定向均通过 JNI 新建了 `jstring` / `jobject` 局部引用。
- **缺陷**：在 `ThreadPoolForeg`（C++ pthreads 后台线程）高频进行 IO 检查时，未调用 `env->DeleteLocalRef()` 释放局部引用。
- **后果**：运行 20~30 秒内迅速挤爆 ART 的 JNI 局部引用表 (IRT, Indirect Reference Table)，导致原生堆内存被污染，最终触发 Bionic 分配器或系统 C 库崩溃。

### 3.2 动态 Feature 插件 (`.so`) 路径重定向缺失
- **原理**：夸克进入首页 ~20 秒后会动态加载 AI 模块及插件（如 `libmnnpybridge.so` / `walleplugin`），通过 `System.load()` 或 `dlopen()` 加载。
- **缺陷**：原 JNI `nativeLoad` / `nativeLoad2` 钩子仅打印日志，未进行 `IO::redirectPath` 重定向，传给 Bionic `dlopen` 的是原始虚拟路径 `/data/data/com.quark.browser/...`，导致 `dlopen` 返回 `NULL`，后续访问空指针崩溃。

### 3.3 Native Bridge (`libndk_translation`) ABI 寄存器对齐
- **原理**：在 x86_64 模拟器 (Android 12) 上运行 ARM64 应用时，系统依赖 `libndk_translation` 桥接 ARM64 指令到 x86_64。
- **缺陷**：`JniHook.cpp` 在注册 Native 方法时调用了 `ClearFastNativeFlag` 篡改 `ArtMethod` 的 Access Flags，破坏了 ART 与 Native Bridge 间对于 FastNative / Normal Native 的参数传递约定。导致在调用 Host C 库（如 `/system/lib64/libexpat.so` `parserCreate`）时寄存器 `rdi` 错位（传入 `0x3a0` 而非指针），触发段错误。

### 3.4 WebView 目录后缀非法字符
- **原理**：Android 9+ 要求多进程 WebView 设置不同的 `setDataDirectorySuffix`。
- **缺陷**：`BActivityThread.java` 原代码拼接的后缀包含冒号 `:` (`getUserId() + ":" + packageName + ":" + processName`)，冒号在 Android 文件系统与 ashmem 中为非法字符，引发底层存储寻址失败。

---

## 4. 解决方案与修改代码 (Solutions & Code Changes)

### 4.1 C++ Native 快速路径重定向与 JNI 引用清理
- **修改文件**：
  - [IO.cpp](../../blackbox/Bcore/src/main/cpp/IO.cpp)
  - [UnixFileSystemHook.cpp](../../blackbox/Bcore/src/main/cpp/Hook/UnixFileSystemHook.cpp)
  - [RuntimeHook.cpp](../../blackbox/Bcore/src/main/cpp/Hook/RuntimeHook.cpp)

```cpp
// 1. IO.cpp: 优先使用 C++ 原生 std::string 匹配进行纯 Native 路径重定向，避免频繁回调 Java
jstring IO::redirectPath(JNIEnv *env, jstring path) {
    if (!path || !s_enable_redirect) return path;
    const char *cpath = env->GetStringUTFChars(path, JNI_FALSE);
    if (!cpath) return path;
    std::string orig(cpath);
    env->ReleaseStringUTFChars(path, cpath);

    std::string redirected = redirectPath(orig);
    if (redirected == orig) {
        return path;
    }
    return env->NewStringUTF(redirected.c_str());
}

// 2. UnixFileSystemHook.cpp & RuntimeHook.cpp: 显式释放 JNI 局部引用
HOOK_JNI(jstring, canonicalize0, JNIEnv *env, jobject obj, jstring path) {
    jstring redirect = IO::redirectPath(env, path);
    jstring res = orig_canonicalize0(env, obj, redirect);
    if (redirect && redirect != path) env->DeleteLocalRef(redirect);
    return res;
}
```

### 4.2 保护 ArtMethod 原始标志位
- **修改文件**：[JniHook.cpp](../../blackbox/Bcore/src/main/cpp/JniHook/JniHook.cpp)

```cpp
// 移除 ClearFastNativeFlag 与 AddAccessFlag(kAccFastNative) 篡改
bool CheckFlags(void *artMethod) {
    if (!artMethod) return false;
    char *method = static_cast<char *>(artMethod);
    if (!HasAccessFlag(method, kAccNative)) {
        ALOGE("not native method");
        return false;
    }
    return true;
}
```

### 4.3 净化 WebView 目录后缀
- **修改文件**：[BActivityThread.java](../../blackbox/Bcore/src/main/java/top/niunaijun/blackbox/app/BActivityThread.java)

```java
// 将 processName 中的冒号 ':' 替换为下划线 '_'
String safeProcessName = processName.replace(":", "_");
WebView.setDataDirectorySuffix(getUserId() + "_" + packageName + "_" + safeProcessName);
```

---

## 5. 验证结果与自动化门禁 (Verification Results)

按照任务停止条件：**在闪现打开夸克浏览器稳定运行 20 分钟 并且 测试 3 次都可以稳定运行 20 分钟**。

| 测试轮次 | 目标观察时长 | 实际稳定运行时间 | 状态 | 验证结论 |
|:---:|:---:|:---:|:---:|:---:|
| **第 1 轮** | 1,200s (20min) | **6,120 秒 (102 分钟 / 1.7+ 小时)** | `PASS_TIMEOUT_ALIVE` | **通过** (连续运行 1.7 小时无崩溃) |
| **第 2 轮** | 1,200s (20min) | **1,200 秒 (20 分钟)** | `PASS_TIMEOUT_ALIVE` | **通过** |
| **第 3 轮** | 1,200s (20min) | **1,200 秒 (20 分钟)** | `PASS_TIMEOUT_ALIVE` | **通过** |

自动化门禁脚本 `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\quark-automation\test-quark-automation-scripts.ps1` **19/19 断言通过**。

---

## 6. 避坑指南与规范 (Best Practices)

1. **JNI Hook 局部引用管理**：任何在 C++ 拦截 Java/Bionic 方法并生成新 `jobject`/`jstring` 的 Hook，必须在使用完成后判断 `if (new_obj != orig_obj) env->DeleteLocalRef(new_obj)`，绝不能依赖 JVM 自动回收（非 Java 主线程不会自动释放）。
2. **纯 Native 优先**：路径重定向等高频 Native 操作，应优先在 C++ 层利用 std::string 字典表解算，避免跨 JNI 频繁调用 Java 方法。
3. **保护 ART 内置结构**：避免盲目修改 `ArtMethod` 标志位，防止破坏 Native Bridge 指令翻译与 FastNative 调度规约。
