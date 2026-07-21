# Keep Xposed entry
-keep class com.sx.app.xposed.** { *; }
-keep class de.robv.android.xposed.** { *; }

# Keep Sandbox API & Engine implementation
-keep class com.sx.app.sandbox.** { *; }
-keep class com.sx.app.sandbox.api.** { *; }
-keep class com.sx.app.sandbox.bb.** { *; }

# Keep Data models and application components
-keep class com.sx.app.data.** { *; }
-keep class com.sx.app.SxApp { *; }
-keep class com.sx.app.service.** { *; }
-keep class com.sx.app.license.** { *; }

# Keep BlackBox & Pine engine classes (reflection & IPC bridge)
-keep class top.niunaijun.blackbox.** { *; }
-keep interface top.niunaijun.blackbox.** { *; }
-keep class top.niunaijun.pine.** { *; }

# Keep Parcelable & AIDL implementations
-keep class * implements android.os.Parcelable {
    public static final android.os.Parcelable$Creator *;
}
-keepclassmembers class * implements android.os.Parcelable {
    public <init>(android.os.Parcel);
}

# Keep ContentProviders, Services, Activities and Applications
-keep public class * extends android.app.Application
-keep public class * extends android.content.ContentProvider
-keep public class * extends android.app.Service
-keep public class * extends android.app.Activity

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Preserve annotations and attributes for reflection
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod,Exceptions
