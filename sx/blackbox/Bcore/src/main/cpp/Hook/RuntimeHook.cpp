//
// Created by Milk on 5/5/21.
//

#include "RuntimeHook.h"
#include "JniHook/JniHook.h"
#include "BoxCore.h"
#include <IO.h>

HOOK_JNI(jstring, nativeLoad, JNIEnv *env, jobject obj, jstring name, jobject class_loader) {
    jstring redirect = IO::redirectPath(env, name);
    const char *nameC = env->GetStringUTFChars(redirect, JNI_FALSE);
    if (nameC) {
        ALOGD("nativeLoad: %s", nameC);
    }
    jstring result = orig_nativeLoad(env, obj, redirect, class_loader);
    if (nameC) {
        env->ReleaseStringUTFChars(redirect, nameC);
    }
    if (redirect && redirect != name) {
        env->DeleteLocalRef(redirect);
    }
    return result;
}

HOOK_JNI(jstring, nativeLoad2, JNIEnv *env, jobject obj, jstring name, jobject class_loader,
         jobject caller) {
    jstring redirect = IO::redirectPath(env, name);
    const char *nameC = env->GetStringUTFChars(redirect, JNI_FALSE);
    if (nameC) {
        ALOGD("nativeLoad2: %s", nameC);
    }
    jstring result = orig_nativeLoad2(env, obj, redirect, class_loader, caller);
    if (nameC) {
        env->ReleaseStringUTFChars(redirect, nameC);
    }
    if (redirect && redirect != name) {
        env->DeleteLocalRef(redirect);
    }
    return result;
}

void RuntimeHook::init(JNIEnv *env) {
    const char *className = "java/lang/Runtime";
    if (BoxCore::getApiLevel() >= __ANDROID_API_Q__) {
        JniHook::HookJniFun(env, className, "nativeLoad",
                            "(Ljava/lang/String;Ljava/lang/ClassLoader;Ljava/lang/Class;)Ljava/lang/String;",
                            (void *) new_nativeLoad2,
                            (void **) (&orig_nativeLoad2), true);
        if (!orig_nativeLoad2) {
            JniHook::HookJniFun(env, className, "nativeLoad",
                                "(Ljava/lang/String;Ljava/lang/ClassLoader;Ljava/io/File;)Ljava/lang/String;",
                                (void *) new_nativeLoad2,
                                (void **) (&orig_nativeLoad2), true);
        }
        if (!orig_nativeLoad2) {
            JniHook::HookJniFun(env, className, "nativeLoad",
                                "(Ljava/lang/String;Ljava/lang/ClassLoader;)Ljava/lang/String;",
                                (void *) new_nativeLoad,
                                (void **) (&orig_nativeLoad), true);
        }
    } else {
        JniHook::HookJniFun(env, className, "nativeLoad",
                            "(Ljava/lang/String;Ljava/lang/ClassLoader;)Ljava/lang/String;",
                            (void *) new_nativeLoad,
                            (void **) (&orig_nativeLoad), true);
    }
}
