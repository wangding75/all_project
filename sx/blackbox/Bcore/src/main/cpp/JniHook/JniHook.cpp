//
// Created by Milk on 3/8/21.
//

#include <jni.h>
#include "JniHook.h"
#include "Log.h"
#include "ArtMethod.h"

static struct {
    int api_level;
    unsigned int art_field_size;
    int art_field_flags_offset;

    unsigned int art_method_size;
    int art_method_flags_offset;
    int art_method_native_offset;

    int class_flags_offset;

    jclass method_utils_class;
    jmethodID get_method_desc_id;
    jmethodID get_method_declaring_class_id;
    jmethodID get_method_name_id;

} HookEnv;

static const char *GetMethodDesc(JNIEnv *env, jobject javaMethod) {
    if (!HookEnv.method_utils_class || !HookEnv.get_method_desc_id) return nullptr;
    auto desc = reinterpret_cast<jstring>(env->CallStaticObjectMethod(HookEnv.method_utils_class,
                                                                      HookEnv.get_method_desc_id,
                                                                      javaMethod));
    if (!desc) return nullptr;
    const char *chars = env->GetStringUTFChars(desc, JNI_FALSE);
    env->DeleteLocalRef(desc);
    return chars;
}

static const char *GetMethodDeclaringClass(JNIEnv *env, jobject javaMethod) {
    if (!HookEnv.method_utils_class || !HookEnv.get_method_declaring_class_id) return nullptr;
    auto desc = reinterpret_cast<jstring>(env->CallStaticObjectMethod(HookEnv.method_utils_class,
                                                                      HookEnv.get_method_declaring_class_id,
                                                                      javaMethod));
    if (!desc) return nullptr;
    const char *chars = env->GetStringUTFChars(desc, JNI_FALSE);
    env->DeleteLocalRef(desc);
    return chars;
}

static const char *GetMethodName(JNIEnv *env, jobject javaMethod) {
    if (!HookEnv.method_utils_class || !HookEnv.get_method_name_id) return nullptr;
    auto desc = reinterpret_cast<jstring>(env->CallStaticObjectMethod(HookEnv.method_utils_class,
                                                                      HookEnv.get_method_name_id,
                                                                      javaMethod));
    if (!desc) return nullptr;
    const char *chars = env->GetStringUTFChars(desc, JNI_FALSE);
    env->DeleteLocalRef(desc);
    return chars;
}

inline static uint32_t GetAccessFlags(const char *art_method) {
    return *reinterpret_cast<const uint32_t *>(art_method + HookEnv.art_method_flags_offset);
}

inline static bool SetAccessFlags(char *art_method, uint32_t flags) {
    *reinterpret_cast<uint32_t *>(art_method + HookEnv.art_method_flags_offset) = flags;
    return true;
}

inline static bool AddAccessFlag(char *art_method, uint32_t flag) {
    uint32_t old_flag = GetAccessFlags(art_method);
    uint32_t new_flag = old_flag | flag;
    return new_flag != old_flag && SetAccessFlags(art_method, new_flag);
}

inline static bool ClearAccessFlag(char *art_method, uint32_t flag) {
    uint32_t old_flag = GetAccessFlags(art_method);
    uint32_t new_flag = old_flag & ~flag;
    return new_flag != old_flag && SetAccessFlags(art_method, new_flag);
}

inline static bool HasAccessFlag(char *art_method, uint32_t flag) {
    uint32_t flags = GetAccessFlags(art_method);
    return (flags & flag) == flag;
}

inline static bool ClearFastNativeFlag(char *art_method) {
    bool c1 = ClearAccessFlag(art_method, kAccFastNative);
    bool c2 = ClearAccessFlag(art_method, kAccCriticalNative);
    return c1 || c2;
}

static void *GetArtMethod(JNIEnv *env, jclass clazz, jmethodID methodId) {
    if (HookEnv.api_level >= __ANDROID_API_Q__) {
        jclass executable = env->FindClass("java/lang/reflect/Executable");
        jfieldID artId = env->GetFieldID(executable, "artMethod", "J");
        jobject method = env->ToReflectedMethod(clazz, methodId, true);
        return reinterpret_cast<void *>(env->GetLongField(method, artId));
    } else {
        return methodId;
    }
}

static void *GetFieldMethod(JNIEnv *env, jobject field) {
    if (HookEnv.api_level >= __ANDROID_API_Q__) {
        jclass fieldClass = env->FindClass("java/lang/reflect/Field");
        jmethodID getArtField = env->GetMethodID(fieldClass, "getArtField", "()J");
        return reinterpret_cast<void *>(env->CallLongMethod(field, getArtField));
    } else {
        return env->FromReflectedField(field);
    }
}

bool CheckFlags(void *artMethod) {
    if (!artMethod) return false;
    char *method = static_cast<char *>(artMethod);
    if (!HasAccessFlag(method, kAccNative)) {
        ALOGE("not native method");
        return false;
    }
    ClearFastNativeFlag(method);
    AddAccessFlag(method, kAccCompileDontBother);
    return true;
}

void JniHook::HookJniFun(JNIEnv *env, jobject java_method, void *new_fun,
                         void **orig_fun, bool is_static) {
    const char *class_name = GetMethodDeclaringClass(env, java_method);
    const char *method_name = GetMethodName(env, java_method);
    const char *sign = GetMethodDesc(env, java_method);
    if (class_name && method_name && sign) {
        HookJniFun(env, class_name, method_name, sign, new_fun, orig_fun, is_static);
    }
}

void
JniHook::HookJniFun(JNIEnv *env, const char *class_name, const char *method_name, const char *sign,
                    void *new_fun, void **orig_fun, bool is_static) {
    if (HookEnv.art_method_native_offset == 0 && HookEnv.api_level >= __ANDROID_API_P__) {
        ALOGE("art_method_native_offset not found, skipping HookJniFun for %s %s", class_name, method_name);
        return;
    }
    jclass clazz = env->FindClass(class_name);
    if (!clazz) {
        ALOGD("findClass fail: %s %s", class_name, method_name);
        env->ExceptionClear();
        return;
    }
    jmethodID method = nullptr;
    if (is_static) {
        method = env->GetStaticMethodID(clazz, method_name, sign);
    } else {
        method = env->GetMethodID(clazz, method_name, sign);
    }
    if (!method) {
        env->ExceptionClear();
        ALOGD("get method id fail: %s %s", class_name, method_name);
        return;
    }
    JNINativeMethod gMethods[] = {
            {method_name, sign, (void *) new_fun},
    };

    auto artMethod = reinterpret_cast<uintptr_t *>(GetArtMethod(env, clazz, method));
    if (!artMethod || !CheckFlags(artMethod)) {
        ALOGE("check flags error. class：%s, method：%s", class_name, method_name);
        // CheckFlags / GetArtMethod may leave pending exceptions on newer ART.
        if (env->ExceptionCheck()) {
            env->ExceptionClear();
        }
        return;
    }
    *orig_fun = reinterpret_cast<void *>(artMethod[HookEnv.art_method_native_offset]);
    if (env->RegisterNatives(clazz, gMethods, 1) < 0) {
        ALOGE("jni hook error. class：%s, method：%s", class_name, method_name);
        // RegisterNatives leaves NoSuchMethodError pending when method is not
        // actually JNI-native (common on Android 14+ / 16 for UnixFileSystem).
        // Must clear or later JNI calls abort the process.
        if (env->ExceptionCheck()) {
            env->ExceptionDescribe();
            env->ExceptionClear();
        }
        return;
    }
    ALOGD("register class：%s, method：%s success!", class_name, method_name);
}

__attribute__((section (".mytext")))  JNICALL void native_offset
        (JNIEnv *env, jclass obj) {
}

__attribute__((section (".mytext")))  JNICALL void native_offset2
        (JNIEnv *env, jclass obj) {
}

__attribute__((section (".mytext")))  JNICALL void set_method_accessible
        (JNIEnv *env, jclass obj, jclass clazz, jobject method) {
    jmethodID methodId = env->FromReflectedMethod(method);
    char *art_method = static_cast<char *>(GetArtMethod(env, clazz, methodId));
    if (art_method) {
        AddAccessFlag(art_method, kAccPublic);
        if (HookEnv.api_level >= __ANDROID_API_Q__) {
            AddAccessFlag(art_method, kAccPublicApi);
        }
    }
}

__attribute__((section (".mytext")))  JNICALL void set_field_accessible
        (JNIEnv *env, jclass obj, jclass clazz, jobject field) {
    char *artField = static_cast<char *>(GetFieldMethod(env, field));
    if (artField) {
        AddAccessFlag(artField, kAccPublic);
        if (HookEnv.api_level >= __ANDROID_API_Q__) {
            AddAccessFlag(artField, kAccPublicApi);
        }
        ClearAccessFlag(artField, kAccFinal);
    }
}

void registerNative(JNIEnv *env) {
    jclass clazz = env->FindClass("top/niunaijun/jnihook/jni/JniHook");
    if (!clazz) return;
    JNINativeMethod gMethods[] = {
            {"nativeOffset",  "()V",                                            (void *) native_offset},
            {"nativeOffset2", "()V",                                            (void *) native_offset2},
            {"setAccessible", "(Ljava/lang/Class;Ljava/lang/reflect/Method;)V", (void *) set_method_accessible},
            {"setAccessible", "(Ljava/lang/Class;Ljava/lang/reflect/Field;)V",  (void *) set_field_accessible},
    };
    if (env->RegisterNatives(clazz, gMethods, sizeof(gMethods) / sizeof(gMethods[0])) < 0) {
        ALOGE("jni register error.");
    }
}

void JniHook::InitJniHook(JNIEnv *env, int api_level) {
    registerNative(env);
    HookEnv.api_level = api_level;

    jclass clazz = env->FindClass("top/niunaijun/jnihook/jni/JniHook");
    if (!clazz) return;
    jmethodID nativeOffsetId = env->GetStaticMethodID(clazz, "nativeOffset", "()V");
    jmethodID nativeOffset2Id = env->GetStaticMethodID(clazz, "nativeOffset2", "()V");

    jfieldID nativeOffsetFieldId = env->GetStaticFieldID(clazz, "NATIVE_OFFSET", "I");
    jfieldID nativeOffsetField2Id = env->GetStaticFieldID(clazz, "NATIVE_OFFSET_2", "I");

    void *nativeOffsetField = GetFieldMethod(env, env->ToReflectedField(clazz, nativeOffsetFieldId, true));
    void *nativeOffsetField2 = GetFieldMethod(env, env->ToReflectedField(clazz, nativeOffsetField2Id, true));
    if (nativeOffsetField && nativeOffsetField2) {
        HookEnv.art_field_size = (size_t) nativeOffsetField2 - (size_t) nativeOffsetField;
    }

    void *nativeOffset = GetArtMethod(env, clazz, nativeOffsetId);
    void *nativeOffset2 = GetArtMethod(env, clazz, nativeOffset2Id);
    if (nativeOffset && nativeOffset2) {
        HookEnv.art_method_size = (size_t) nativeOffset2 - (size_t) nativeOffset;
    }

    // calc native offset safely
    if (nativeOffset && HookEnv.art_method_size > 0) {
        auto artMethod = reinterpret_cast<uintptr_t *>(nativeOffset);
        size_t max_words = HookEnv.art_method_size / sizeof(uintptr_t);
        for (size_t i = 0; i < max_words; ++i) {
            if (reinterpret_cast<void *>(artMethod[i]) == native_offset) {
                HookEnv.art_method_native_offset = (int) i;
                break;
            }
        }

        uint32_t flags = 0x0;
        flags = flags | kAccPublic;
        flags = flags | kAccStatic;
        flags = flags | kAccNative;
        flags = flags | kAccFinal;
        if (api_level >= __ANDROID_API_Q__) {
            flags = flags | kAccPublicApi;
        }

        char *start = reinterpret_cast<char *>(artMethod);
        size_t max_u32 = HookEnv.art_method_size / sizeof(uint32_t);
        for (size_t i = 1; i < max_u32; ++i) {
            auto value = *(uint32_t *) (start + i * sizeof(uint32_t));
            if (value == flags) {
                HookEnv.art_method_flags_offset = (int) (i * sizeof(uint32_t));
                break;
            }
        }
    }

    if (nativeOffsetField && HookEnv.art_field_size > 0) {
        uint32_t flags = 0x0;
        flags = flags | kAccPublic;
        flags = flags | kAccStatic;
        flags = flags | kAccFinal;
        if (api_level >= __ANDROID_API_Q__) {
            flags = flags | kAccPublicApi;
        }
        char *fieldStart = reinterpret_cast<char *>(nativeOffsetField);
        size_t max_i32 = HookEnv.art_field_size / sizeof(int32_t);
        for (size_t i = 1; i < max_i32; ++i) {
            auto value = *(int32_t *) (fieldStart + i * sizeof(int32_t));
            if (value == flags) {
                HookEnv.art_field_flags_offset = (int) (i * sizeof(int32_t));
                break;
            }
        }
    }

    HookEnv.method_utils_class = env->FindClass("top/niunaijun/jnihook/MethodUtils");
    if (HookEnv.method_utils_class) {
        HookEnv.method_utils_class = (jclass) env->NewGlobalRef(HookEnv.method_utils_class);
        HookEnv.get_method_desc_id = env->GetStaticMethodID(HookEnv.method_utils_class, "getDesc",
                                                            "(Ljava/lang/reflect/Method;)Ljava/lang/String;");
        HookEnv.get_method_declaring_class_id = env->GetStaticMethodID(HookEnv.method_utils_class,
                                                                       "getDeclaringClass",
                                                                       "(Ljava/lang/reflect/Method;)Ljava/lang/String;");
        HookEnv.get_method_name_id = env->GetStaticMethodID(HookEnv.method_utils_class, "getMethodName",
                                                            "(Ljava/lang/reflect/Method;)Ljava/lang/String;");
    }
}


