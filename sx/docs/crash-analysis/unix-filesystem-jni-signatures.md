# UnixFileSystem JNI 签名核验对照表

| 方法名 | static/instance | Java 方法签名 | C++ 参数列表 | C++ 返回类型 | 强类型指针与静态断言 | 核验结果 |
|---|---|---|---|---|---|---|
| `canonicalize0` | instance | `(Ljava/lang/String;)Ljava/lang/String;` | `(JNIEnv *env, jobject obj, jstring path)` | `jstring` | `static_assert` 检查通过 | ✅ 完全对齐 |
| `getBooleanAttributes0` | instance | `(Ljava/lang/String;)I` | `(JNIEnv *env, jobject obj, jstring abspath)` | `jint` | `jint (*orig_...)(...)` | ✅ 完全对齐 |
| `getLastModifiedTime0` | instance | `(Ljava/io/File;)J` | `(JNIEnv *env, jobject obj, jobject path)` | `jlong` | `static_assert` 检查通过 | ✅ 完全对齐 |
| `setPermission0` | instance | `(Ljava/io/File;IZZ)Z` | `(JNIEnv *env, jobject obj, jobject file, jint access, jboolean enable, jboolean owneronly)` | `jboolean` | `static_assert` 检查通过 | ✅ 完全对齐 |
| `createFileExclusively0` | instance | `(Ljava/lang/String;)Z` | `(JNIEnv *env, jobject obj, jstring path)` | `jboolean` | `static_assert` 检查通过 | ✅ 完全对齐 |
| `list0` | instance | `(Ljava/io/File;)[Ljava/lang/String;` | `(JNIEnv *env, jobject obj, jobject file)` | `jobjectArray` | `static_assert` 检查通过 | ✅ 完全对齐 |
| `createDirectory0` | instance | `(Ljava/io/File;)Z` | `(JNIEnv *env, jobject obj, jobject path)` | `jboolean` | `static_assert` 检查通过 | ✅ 完全对齐 |
| `setLastModifiedTime0` | instance | `(Ljava/io/File;J)Z` | `(JNIEnv *env, jobject obj, jobject file, jlong time)` | `jboolean` | `static_assert` 检查通过（原 `jobject time` 已修正为 `jlong time`） | ✅ 完全对齐 |
| `setReadOnly0` | instance | `(Ljava/io/File;)Z` | `(JNIEnv *env, jobject obj, jobject file)` | `jboolean` | `static_assert` 检查通过 | ✅ 完全对齐 |
| `getSpace0` | instance | `(Ljava/io/File;I)J` | `(JNIEnv *env, jobject obj, jobject file, jint t)` | `jlong` | `static_assert` 检查通过（原 `jboolean` 已修正为 `jlong`） | ✅ 完全对齐 |
