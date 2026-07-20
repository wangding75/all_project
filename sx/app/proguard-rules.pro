# Keep Xposed entry
-keep class com.sx.app.xposed.SxModule { *; }
-keep class de.robv.android.xposed.** { *; }

# Keep models used by GSON/JSON if added later
-keepclassmembers class com.sx.app.data.** { *; }
