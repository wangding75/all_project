#include "BoxCore.h"
#include "Log.h"
#include "IO.h"
#include <jni.h>
#include <pthread.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <dlfcn.h>
#include <JniHook/JniHook.h>
#include <Hook/VMClassLoaderHook.h>
#include <Hook/UnixFileSystemHook.h>
#include <Hook/BinderHook.h>
#include <Hook/RuntimeHook.h>
#include "Utils/HexDump.h"

extern "C" JNIEXPORT int kill(pid_t pid, int sig) {
    if (pid == getpid() && (sig == SIGSEGV || sig == SIGABRT || sig == SIGKILL || sig == SIGTERM)) {
        ALOGE("SX anti-suicide: blocked native kill(self, sig=%d)", sig);
        return 0;
    }
    typedef int (*kill_t)(pid_t, int);
    static kill_t orig_kill = (kill_t) dlsym(RTLD_NEXT, "kill");
    return orig_kill ? orig_kill(pid, sig) : 0;
}

extern "C" JNIEXPORT int tgkill(pid_t tgid, pid_t tid, int sig) {
    if (tgid == getpid() && (sig == SIGSEGV || sig == SIGABRT || sig == SIGKILL || sig == SIGTERM)) {
        ALOGE("SX anti-suicide: blocked native tgkill(self, tid=%d, sig=%d)", tid, sig);
        return 0;
    }
    typedef int (*tgkill_t)(pid_t, pid_t, int);
    static tgkill_t orig_tgkill = (tgkill_t) dlsym(RTLD_NEXT, "tgkill");
    return orig_tgkill ? orig_tgkill(tgid, tid, sig) : 0;
}

extern "C" JNIEXPORT void exit(int status) {
    ALOGE("SX anti-suicide: blocked native exit(status=%d)", status);
}

extern "C" JNIEXPORT void _exit(int status) {
    ALOGE("SX anti-suicide: blocked native _exit(status=%d)", status);
}

extern "C" JNIEXPORT void _Exit(int status) {
    ALOGE("SX anti-suicide: blocked native _Exit(status=%d)", status);
}

// DingTalk multi-open self-kill: kill(getpid(), SIGSEGV) with SI_USER (si_code<=0).
// Do NOT sigprocmask-block SIGSEGV: Linux treats a blocked *synchronous* SIGSEGV
// (true memory fault) as fatal and kills the process — that caused a restart loop.
// Strategy: SA_SIGINFO handler ignores SI_USER cleanly without limit.
static volatile int s_anti_suicide_installed = 0;
static volatile int s_ignored_suicides = 0;

static void sx_anti_suicide_handler(int sig, siginfo_t *info, void *ucontext) {
    if (info && info->si_code <= 0) {
        int n = __sync_add_and_fetch(&s_ignored_suicides, 1);
        if (n <= 10) {
            ALOGE("SX anti-suicide: ignore artificial sig=%d si_code=%d n=%d",
                  sig, info->si_code, n);
        }
        if (ucontext != nullptr) {
            ucontext_t *uc = (ucontext_t *) ucontext;
#if defined(__aarch64__)
            uc->uc_mcontext.regs[0] = 0;
            uint32_t *pc_ptr = (uint32_t *) uc->uc_mcontext.pc;
            if (pc_ptr && ((*pc_ptr & 0xfc000000) == 0x14000000 || (*pc_ptr & 0x7e000000) == 0x34000000)) {
                uc->uc_mcontext.pc += 4;
            }
#elif defined(__arm__)
            uc->uc_mcontext.arm_r0 = 0;
#elif defined(__x86_64__)
            uc->uc_mcontext.gregs[REG_RAX] = 0;
#elif defined(__i386__)
            uc->uc_mcontext.gregs[REG_EAX] = 0;
#endif
        }
        return; // Consumes ALL artificial SI_USER signals cleanly
    }
    // True fault (SEGV_MAPERR/SEGV_ACCERR etc.): restore default and re-raise.
    signal(sig, SIG_DFL);
    raise(sig);
}

static void sx_install_anti_suicide_handlers() {
    if (s_anti_suicide_installed) return;
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = sx_anti_suicide_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_SIGINFO;
    if (sigaction(SIGSEGV, &sa, nullptr) != 0) {
        ALOGE("sigaction(SIGSEGV) failed: %s", strerror(errno));
    }
    if (sigaction(SIGABRT, &sa, nullptr) != 0) {
        ALOGE("sigaction(SIGABRT) failed: %s", strerror(errno));
    }
    s_anti_suicide_installed = 1;
    ALOGD("SX anti-suicide handlers installed (pid=%d)", getpid());
}

struct {
    JavaVM *vm;
    jclass NativeCoreClass;
    jmethodID getCallingUidId;
    jmethodID redirectPathString;
    jmethodID redirectPathFile;
    jmethodID loadEmptyDex;
    jmethodID loadEmptyDexL;
    int api_level;
    int hook_flags;
} VMEnv;

static pthread_key_t s_thread_key;
static pthread_once_t s_key_once = PTHREAD_ONCE_INIT;

static void detach_thread_destructor(void *value) {
    JNIEnv *env = static_cast<JNIEnv *>(value);
    if (env && VMEnv.vm) {
        VMEnv.vm->DetachCurrentThread();
    }
}

static void make_thread_key() {
    pthread_key_create(&s_thread_key, detach_thread_destructor);
}

JNIEnv *getEnv() {
    JNIEnv *env = nullptr;
    if (!VMEnv.vm) return nullptr;
    jint res = VMEnv.vm->GetEnv(reinterpret_cast<void **>(&env), JNI_VERSION_1_6);
    if (res == JNI_OK) {
        return env;
    }
    return nullptr;
}

JNIEnv *ensureEnvCreated() {
    JNIEnv *env = nullptr;
    if (!VMEnv.vm) return nullptr;
    jint res = VMEnv.vm->GetEnv(reinterpret_cast<void **>(&env), JNI_VERSION_1_6);
    if (res == JNI_OK) {
        return env;
    }
    return nullptr;
}

int BoxCore::getCallingUid(JNIEnv *env, int orig) {
    JNIEnv *current_env = ensureEnvCreated();
    if (!current_env || !VMEnv.NativeCoreClass || !VMEnv.getCallingUidId) return orig;
    jint res = current_env->CallStaticIntMethod(VMEnv.NativeCoreClass, VMEnv.getCallingUidId, orig);
    if (current_env->ExceptionCheck()) {
        current_env->ExceptionDescribe();
        current_env->ExceptionClear();
        return orig;
    }
    return res;
}

jstring BoxCore::redirectPathString(JNIEnv *env, jstring path) {
    JNIEnv *current_env = ensureEnvCreated();
    if (!current_env || !VMEnv.NativeCoreClass || !VMEnv.redirectPathString) return path;
    auto res = (jstring) current_env->CallStaticObjectMethod(VMEnv.NativeCoreClass, VMEnv.redirectPathString, path);
    if (current_env->ExceptionCheck() || !res) {
        if (current_env->ExceptionCheck()) {
            current_env->ExceptionDescribe();
            current_env->ExceptionClear();
        }
        return path;
    }
    return res;
}

jobject BoxCore::redirectPathFile(JNIEnv *env, jobject path) {
    JNIEnv *current_env = ensureEnvCreated();
    if (!current_env || !VMEnv.NativeCoreClass || !VMEnv.redirectPathFile) return path;
    auto res = current_env->CallStaticObjectMethod(VMEnv.NativeCoreClass, VMEnv.redirectPathFile, path);
    if (current_env->ExceptionCheck() || !res) {
        if (current_env->ExceptionCheck()) {
            current_env->ExceptionDescribe();
            current_env->ExceptionClear();
        }
        return path;
    }
    return res;
}

jlongArray BoxCore::loadEmptyDex(JNIEnv *env) {
    JNIEnv *current_env = ensureEnvCreated();
    if (!current_env || !VMEnv.NativeCoreClass || !VMEnv.loadEmptyDex) return nullptr;
    auto res = (jlongArray) current_env->CallStaticObjectMethod(VMEnv.NativeCoreClass, VMEnv.loadEmptyDex);
    if (current_env->ExceptionCheck()) {
        current_env->ExceptionDescribe();
        current_env->ExceptionClear();
        return nullptr;
    }
    return res;
}

int BoxCore::getApiLevel() {
    return VMEnv.api_level;
}

JavaVM *BoxCore::getJavaVM() {
    return VMEnv.vm;
}

void nativeHook(JNIEnv *env, int hookFlags) {
    ALOGD("SX Native Hook Switches: hookFlags=0x%x (UnixFS=%d, VMClassLoader=%d, Binder=%d, SpoofRuntime=%d, NativeMaster=%d, IORedirect=%d)",
          hookFlags,
          (hookFlags & 1) != 0,
          (hookFlags & 2) != 0,
          (hookFlags & 4) != 0,
          (hookFlags & 8) != 0,
          (hookFlags & 16) != 0,
          (hookFlags & 32) != 0);

    if (!(hookFlags & 16)) {
        ALOGD("All Native Hooks disabled by HOOK_ALL_NATIVE master switch.");
        return;
    }

    BaseHook::init(env);
    if (hookFlags & 1) UnixFileSystemHook::init(env);
    if (hookFlags & 2) VMClassLoaderHook::init(env);
    if (hookFlags & 8) RuntimeHook::init(env);
    if (hookFlags & 4) BinderHook::init(env);
}

void hideXposed(JNIEnv *env, jclass clazz) {
    ALOGD("set hideXposed");
    VMClassLoaderHook::hideXposed();
}

void init(JNIEnv *env, jobject clazz, jint api_level, jint hook_flags) {
    ALOGD("NativeCore init with api_level=%d, hook_flags=0x%x", api_level, hook_flags);
    VMEnv.api_level = api_level;
    VMEnv.hook_flags = hook_flags;

    IO::setEnableRedirect((hook_flags & 32) != 0);

    jclass localClass = env->FindClass(VMCORE_CLASS);
    if (localClass) {
        VMEnv.NativeCoreClass = (jclass) env->NewGlobalRef(localClass);
        env->DeleteLocalRef(localClass);
    }
    if (VMEnv.NativeCoreClass) {
        VMEnv.getCallingUidId = env->GetStaticMethodID(VMEnv.NativeCoreClass, "getCallingUid", "(I)I");
        VMEnv.redirectPathString = env->GetStaticMethodID(VMEnv.NativeCoreClass, "redirectPath",
                                                          "(Ljava/lang/String;)Ljava/lang/String;");
        VMEnv.redirectPathFile = env->GetStaticMethodID(VMEnv.NativeCoreClass, "redirectPath",
                                                        "(Ljava/io/File;)Ljava/io/File;");
        VMEnv.loadEmptyDex = env->GetStaticMethodID(VMEnv.NativeCoreClass, "loadEmptyDex",
                                                    "()[J");
    }

    JniHook::InitJniHook(env, api_level);
}

void addIORule(JNIEnv *env, jclass clazz, jstring target_path, jstring relocate_path) {
    if (!target_path || !relocate_path) return;
    const char *target = env->GetStringUTFChars(target_path, JNI_FALSE);
    const char *relocate = env->GetStringUTFChars(relocate_path, JNI_FALSE);
    if (target && relocate) {
        IO::addRule(target, relocate);
    }
    if (target) env->ReleaseStringUTFChars(target_path, target);
    if (relocate) env->ReleaseStringUTFChars(relocate_path, relocate);
}

void enableIO(JNIEnv *env, jclass clazz) {
    IO::init(env);
    // Install before other hooks so guest suicide (DingTalk SI_USER SIGSEGV) is absorbed.
    sx_install_anti_suicide_handlers();
    nativeHook(env, VMEnv.hook_flags);
}

static JNINativeMethod gMethods[] = {
        {"hideXposed", "()V",                                     (void *) hideXposed},
        {"addIORule",  "(Ljava/lang/String;Ljava/lang/String;)V", (void *) addIORule},
        {"enableIO",   "()V",                                     (void *) enableIO},
        {"init",       "(II)V",                                   (void *) init},
};

int registerNativeMethods(JNIEnv *env, const char *className,
                          JNINativeMethod *gMethods, int numMethods) {
    jclass clazz = env->FindClass(className);
    if (clazz == nullptr) {
        return JNI_FALSE;
    }
    if (env->RegisterNatives(clazz, gMethods, numMethods) < 0) {
        return JNI_FALSE;
    }
    return JNI_TRUE;
}

int registerNatives(JNIEnv *env) {
    if (!registerNativeMethods(env, VMCORE_CLASS, gMethods,
                               sizeof(gMethods) / sizeof(gMethods[0])))
        return JNI_FALSE;
    return JNI_TRUE;
}

void registerMethod(JNIEnv *jenv) {
    registerNatives(jenv);
}

JNIEXPORT jint JNI_OnLoad(JavaVM *vm, void *reserved) {
    JNIEnv *env = nullptr;
    VMEnv.vm = vm;
    if (vm->GetEnv(reinterpret_cast<void **>(&env), JNI_VERSION_1_6) != JNI_OK) {
        return JNI_EVERSION;
    }
    registerMethod(env);
    sx_install_anti_suicide_handlers();
    return JNI_VERSION_1_6;
}