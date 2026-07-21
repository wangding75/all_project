//
// Created by Milk on 4/10/21.
//

#ifndef VIRTUALM_IO_H
#define VIRTUALM_IO_H

#include <jni.h>
#include <string>
#include <vector>
#include <mutex>
#include "BoxCore.h"

class IO {
public:
    struct RelocateInfo {
        std::string targetPath;
        std::string relocatePath;
    };

    static void init(JNIEnv *env);
    static void addRule(const char *targetPath, const char *relocatePath);
    static jstring redirectPath(JNIEnv *env, jstring path);
    static jobject redirectPath(JNIEnv *env, jobject path);
    static std::string redirectPath(const std::string &path);
    static void setEnableRedirect(bool enable);
    static bool isEnableRedirect();
};

#endif //VIRTUALM_IO_H

