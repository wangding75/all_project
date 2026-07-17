# Custom Spoofer Project (LSPosed & Services Boilerplate)

This is an Android Studio project boilerplate initialized for developing custom spoofing / virtualization capabilities (Mock Location, Device Parameter Spoofing, WIFI MAC Spoofing). It integrates code patterns reversed and cleaned from the `xh` application.

## Directory Structure

*   `app/src/main/AndroidManifest.xml`: Standard permissions and Xposed declarations.
*   `app/src/main/assets/xposed_init`: Hooks class declaration.
*   `app/src/main/java/com/custom/spoofer/`:
    *   `App.java`: Custom base application context class.
    *   `service/FackLocService.java`: Reusable mock location service (50ms thread injector).
    *   `utils/MyUtil.java`: Reusable AES-128-CBC encryption, base64 encoder, and device fingerprint logic.
    *   `xposed/SpooferModule.java`: LSPosed entrypoint class.

## Build and Run

1.  Open the `spoofer_project` folder in **Android Studio**.
2.  Ensure you have target SDK 34 configured.
3.  Compile and build the project to generate the APK.
4.  Install the APK on your rooted phone or emulator running LSPosed.
5.  Enable the module in LSPosed manager, select target App package, and restart the target App.
