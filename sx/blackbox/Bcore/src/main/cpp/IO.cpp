#include "IO.h"
#include "Log.h"
#include <cstring>

static jmethodID getAbsolutePathMethodId = nullptr;
static std::vector<IO::RelocateInfo> s_relocate_rules;
static std::mutex s_rule_mutex;
static bool s_enable_redirect = true;

void IO::setEnableRedirect(bool enable) {
    s_enable_redirect = enable;
}

bool IO::isEnableRedirect() {
    return s_enable_redirect;
}

std::string IO::redirectPath(const std::string &path) {
    if (!s_enable_redirect || path.empty()) {
        return path;
    }

    std::lock_guard<std::mutex> lock(s_rule_mutex);
    for (const auto &info : s_relocate_rules) {
        if (info.targetPath.empty()) continue;
        const size_t targetLen = info.targetPath.length();
        if (path.compare(0, targetLen, info.targetPath) == 0) {
            if (path.length() == targetLen || path[targetLen] == '/') {
                if (path.find("/blackbox/") != std::string::npos) {
                    continue;
                }
                return info.relocatePath + path.substr(targetLen);
            }
        }
    }
    return path;
}

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

jobject IO::redirectPath(JNIEnv *env, jobject path) {
    if (!path || !s_enable_redirect) return path;
    return BoxCore::redirectPathFile(env, path);
}

void IO::addRule(const char *targetPath, const char *relocatePath) {
    if (!targetPath || !relocatePath) return;
    std::lock_guard<std::mutex> lock(s_rule_mutex);
    s_relocate_rules.push_back({std::string(targetPath), std::string(relocatePath)});
}

void IO::init(JNIEnv *env) {
    jclass tmpFile = env->FindClass("java/io/File");
    if (tmpFile) {
        getAbsolutePathMethodId = env->GetMethodID(tmpFile, "getAbsolutePath", "()Ljava/lang/String;");
    }
}

