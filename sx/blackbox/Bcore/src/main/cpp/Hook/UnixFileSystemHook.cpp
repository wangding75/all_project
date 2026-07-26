#include <IO.h>
#include "UnixFileSystemHook.h"
#include "JniHook/JniHook.h"
#include "BaseHook.h"
#include <type_traits>

/*
 * Class:     java_io_UnixFileSystem
 * Method:    canonicalize0
 * Signature: (Ljava/lang/String;)Ljava/lang/String;
 */
HOOK_JNI(jstring, canonicalize0, JNIEnv *env, jobject obj, jstring path) {
    jstring redirect = IO::redirectPath(env, path);
    jstring res = orig_canonicalize0(env, obj, redirect);
    if (redirect && redirect != path) env->DeleteLocalRef(redirect);
    return res;
}

/*
 * Class:     java_io_UnixFileSystem
 * Method:    getBooleanAttributes0
 * Signature: (Ljava/lang/String;)I
 */
HOOK_JNI(jint, getBooleanAttributes0, JNIEnv *env, jobject obj, jstring abspath) {
    jstring redirect = IO::redirectPath(env, abspath);
    jint res = orig_getBooleanAttributes0(env, obj, redirect);
    if (redirect && redirect != abspath) env->DeleteLocalRef(redirect);
    return res;
}

/*
 * Class:     java_io_UnixFileSystem
 * Method:    getLastModifiedTime0
 * Signature: (Ljava/io/File;)J
 */
HOOK_JNI(jlong, getLastModifiedTime0, JNIEnv *env, jobject obj, jobject path) {
    jobject redirect = IO::redirectPath(env, path);
    jlong res = orig_getLastModifiedTime0(env, obj, redirect);
    if (redirect && redirect != path) env->DeleteLocalRef(redirect);
    return res;
}

/*
 * Class:     java_io_UnixFileSystem
 * Method:    setPermission0
 * Signature: (Ljava/io/File;IZZ)Z
 */
HOOK_JNI(jboolean, setPermission0, JNIEnv *env, jobject obj, jobject file, jint access,
         jboolean enable, jboolean owneronly) {
    jobject redirect = IO::redirectPath(env, file);
    jboolean res = orig_setPermission0(env, obj, redirect, access, enable, owneronly);
    if (redirect && redirect != file) env->DeleteLocalRef(redirect);
    return res;
}

/*
 * Class:     java_io_UnixFileSystem
 * Method:    createFileExclusively0
 * Signature: (Ljava/lang/String;)Z
 */
HOOK_JNI(jboolean, createFileExclusively0, JNIEnv *env, jobject obj, jstring path) {
    jstring redirect = IO::redirectPath(env, path);
    jboolean res = orig_createFileExclusively0(env, obj, redirect);
    if (redirect && redirect != path) env->DeleteLocalRef(redirect);
    return res;
}

/*
 * Class:     java_io_UnixFileSystem
 * Method:    list0
 * Signature: (Ljava/io/File;)[Ljava/lang/String;
 */
HOOK_JNI(jobjectArray, list0, JNIEnv *env, jobject obj, jobject file) {
    jobject redirect = IO::redirectPath(env, file);
    jobjectArray res = orig_list0(env, obj, redirect);
    if (redirect && redirect != file) env->DeleteLocalRef(redirect);
    return res;
}

/*
 * Class:     java_io_UnixFileSystem
 * Method:    createDirectory0
 * Signature: (Ljava/io/File;)Z
 */
HOOK_JNI(jboolean, createDirectory0, JNIEnv *env, jobject obj, jobject path) {
    jobject redirect = IO::redirectPath(env, path);
    jboolean res = orig_createDirectory0(env, obj, redirect);
    if (redirect && redirect != path) env->DeleteLocalRef(redirect);
    return res;
}

/*
 * Class:     java_io_UnixFileSystem
 * Method:    setLastModifiedTime0
 * Signature: (Ljava/io/File;J)Z
 */
HOOK_JNI(jboolean, setLastModifiedTime0, JNIEnv *env, jobject obj, jobject file, jlong time) {
    jobject redirect = IO::redirectPath(env, file);
    jboolean res = orig_setLastModifiedTime0(env, obj, redirect, time);
    if (redirect && redirect != file) env->DeleteLocalRef(redirect);
    return res;
}

/*
 * Class:     java_io_UnixFileSystem
 * Method:    setReadOnly0
 * Signature: (Ljava/io/File;)Z
 */
HOOK_JNI(jboolean, setReadOnly0, JNIEnv *env, jobject obj, jobject file) {
    jobject redirect = IO::redirectPath(env, file);
    jboolean res = orig_setReadOnly0(env, obj, redirect);
    if (redirect && redirect != file) env->DeleteLocalRef(redirect);
    return res;
}

/*
 * Class:     java_io_UnixFileSystem
 * Method:    getSpace0
 * Signature: (Ljava/io/File;I)J
 */
HOOK_JNI(jlong, getSpace0, JNIEnv *env, jobject obj, jobject file, jint t) {
    jobject redirect = IO::redirectPath(env, file);
    jlong res = orig_getSpace0(env, obj, redirect, t);
    if (redirect && redirect != file) env->DeleteLocalRef(redirect);
    return res;
}

static_assert(std::is_same<decltype(new_canonicalize0(nullptr, nullptr, nullptr)), jstring>::value,
              "canonicalize0 return type must be jstring");
static_assert(std::is_same<decltype(new_getLastModifiedTime0(nullptr, nullptr, nullptr)), jlong>::value,
              "getLastModifiedTime0 return type must be jlong");
static_assert(std::is_same<decltype(new_setPermission0(nullptr, nullptr, nullptr, 0, false, false)), jboolean>::value,
              "setPermission0 return type must be jboolean");
static_assert(std::is_same<decltype(new_createFileExclusively0(nullptr, nullptr, nullptr)), jboolean>::value,
              "createFileExclusively0 return type must be jboolean");
static_assert(std::is_same<decltype(new_list0(nullptr, nullptr, nullptr)), jobjectArray>::value,
              "list0 return type must be jobjectArray");
static_assert(std::is_same<decltype(new_createDirectory0(nullptr, nullptr, nullptr)), jboolean>::value,
              "createDirectory0 return type must be jboolean");
static_assert(std::is_same<decltype(new_setLastModifiedTime0(nullptr, nullptr, nullptr, 0L)), jboolean>::value,
              "setLastModifiedTime0 return type must be jboolean");
static_assert(std::is_same<decltype(new_setReadOnly0(nullptr, nullptr, nullptr)), jboolean>::value,
              "setReadOnly0 return type must be jboolean");
static_assert(std::is_same<decltype(new_getSpace0(nullptr, nullptr, nullptr, 0)), jlong>::value,
              "getSpace0 JNI hook return type must be jlong to match (Ljava/io/File;I)J");

// Try "name0" first (classic Android), then "name" (some ART / Android 14+ variants).
// Failures must not leave pending JNI exceptions (cleared inside HookJniFun).
static void hookUnixFs(JNIEnv *env, const char *className,
                       const char *name0, const char *namePlain, const char *sign,
                       void *newFun, void **origFun) {
    JniHook::HookJniFun(env, className, name0, sign, newFun, origFun, false);
    if (*origFun == nullptr && namePlain != nullptr) {
        JniHook::HookJniFun(env, className, namePlain, sign, newFun, origFun, false);
    }
    if (env->ExceptionCheck()) {
        env->ExceptionClear();
    }
}

void UnixFileSystemHook::init(JNIEnv *env) {
    const char *className = "java/io/UnixFileSystem";
    hookUnixFs(env, className, "canonicalize0", "canonicalize",
               "(Ljava/lang/String;)Ljava/lang/String;",
               (void *) new_canonicalize0, (void **) (&orig_canonicalize0));
//    JniHook::HookJniFun(env, className, "getBooleanAttributes0", "(Ljava/lang/String;)I",
//                        (void *) new_getBooleanAttributes0,
//                        (void **) (&orig_getBooleanAttributes0), false);
    hookUnixFs(env, className, "getLastModifiedTime0", "getLastModifiedTime",
               "(Ljava/io/File;)J",
               (void *) new_getLastModifiedTime0, (void **) (&orig_getLastModifiedTime0));
    hookUnixFs(env, className, "setPermission0", "setPermission",
               "(Ljava/io/File;IZZ)Z",
               (void *) new_setPermission0, (void **) (&orig_setPermission0));
    hookUnixFs(env, className, "createFileExclusively0", "createFileExclusively",
               "(Ljava/lang/String;)Z",
               (void *) new_createFileExclusively0, (void **) (&orig_createFileExclusively0));
    hookUnixFs(env, className, "list0", "list",
               "(Ljava/io/File;)[Ljava/lang/String;",
               (void *) new_list0, (void **) (&orig_list0));
    hookUnixFs(env, className, "createDirectory0", "createDirectory",
               "(Ljava/io/File;)Z",
               (void *) new_createDirectory0, (void **) (&orig_createDirectory0));
    hookUnixFs(env, className, "setLastModifiedTime0", "setLastModifiedTime",
               "(Ljava/io/File;J)Z",
               (void *) new_setLastModifiedTime0, (void **) (&orig_setLastModifiedTime0));
    hookUnixFs(env, className, "setReadOnly0", "setReadOnly",
               "(Ljava/io/File;)Z",
               (void *) new_setReadOnly0, (void **) (&orig_setReadOnly0));
    hookUnixFs(env, className, "getSpace0", "getSpace",
               "(Ljava/io/File;I)J",
               (void *) new_getSpace0, (void **) (&orig_getSpace0));
    if (env->ExceptionCheck()) {
        env->ExceptionClear();
    }
}