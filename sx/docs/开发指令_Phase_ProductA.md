# 开发指令 — Epic P-A 商业授权

> [!WARNING]
> **已归档，禁止按本文代码片段重新实现。** 本文是 P-A 开工时的历史执行
> 指令，其中 Kotlin、OkHttp、`EncryptedSharedPreferences` 与直接卡网适配器
> 等方案未成为当前实现。当前客户端为 Java，并只连接自建服务端；现状以
> [`29_商业授权技术方案.md`](./29_商业授权技术方案.md) 和源码为准。

| 项 | 内容 |
|----|------|
| 指令版本 | v1.0 |
| 日期 | 2026-07-21 |
| 依据 | [29_商业授权技术方案.md](./29_商业授权技术方案.md) |
| 基线 | main @ 699567c |

---

## 执行前必读

1. 通读 `docs/29_商业授权技术方案.md`
2. `LicenseServer` 是唯一对外契约，**不得在 UI / SplashActivity 直接 new CardNetLicenseServer**
3. DEV 卡密逻辑只在 `DevLicenseServer` 内，**LicenseManager 不得直接 hardcode DEV 逻辑**
4. 设备指纹 `DeviceFingerprint.get()` 只能在宿主主进程调用
5. 每个步骤完成后立即 commit，commit msg 格式：`feat(license): <描述>`

---

## Step 1 — 新增依赖与 BuildConfig 注入

**文件：** `app/build.gradle`

### 1.1 新增依赖

```groovy
dependencies {
    // 商业授权新增
    implementation "androidx.security:security-crypto:1.1.0-alpha06"
    implementation "com.squareup.okhttp3:okhttp:4.12.0"
    implementation "com.google.code.gson:gson:2.10.1"
    // kotlinx-coroutines 应已存在
}
```

### 1.2 BuildConfig 字段注入

在 `android { defaultConfig { } }` 内增加：

```groovy
// 从 local.properties 读取，不落明文
def localProps = new Properties()
def localFile = rootProject.file("local.properties")
if (localFile.exists()) localProps.load(localFile.newDataInputStream())

buildConfigField "String", "LICENSE_BASE_URL",
    "\"${localProps.getProperty('license.base_url', 'https://placeholder.example.com/api')}\""
buildConfigField "String", "LICENSE_APP_KEY",
    "\"${localProps.getProperty('license.app_key', 'dev_app_key')}\""
buildConfigField "String", "LICENSE_APP_SECRET",
    "\"${localProps.getProperty('license.app_secret', 'dev_secret')}\""
```

### 1.3 local.properties 追加（不提交 Git）

```properties
license.base_url=https://your-cardnet.com/api
license.app_key=YOUR_APP_KEY
license.app_secret=YOUR_APP_SECRET
```

### 1.4 .gitignore 核查

确认 `local.properties` 在 `.gitignore` 内，不在则追加：

```
local.properties
```

**验收：** `./gradlew :app:assembleDebug` 编译通过，`BuildConfig.LICENSE_BASE_URL` 可引用。

**Commit：** `feat(license): add security-crypto/okhttp deps and BuildConfig injection`

---

## Step 2 — 新建数据类与工具类

### 2.1 LicenseServer 接口

**新建：** `app/src/main/java/com/sx/app/license/LicenseServer.kt`

```kotlin
package com.sx.app.license

interface LicenseServer {
    /** 激活卡密，绑定设备 */
    suspend fun activate(cardKey: String, deviceId: String): LicenseResult

    /** 查询卡密状态（可选，返回 null 表示不支持） */
    suspend fun queryStatus(cardKey: String, deviceId: String): LicenseResult?
}

data class LicenseResult(
    val success: Boolean,
    val expireAt: Long,    // Unix ms；-1L = 永久
    val message: String
)
```

### 2.2 LicenseToken 数据类

**新建：** `app/src/main/java/com/sx/app/license/LicenseToken.kt`

```kotlin
package com.sx.app.license

data class LicenseToken(
    val cardKey: String,
    val deviceId: String,
    val expireAt: Long,
    val activatedAt: Long,
    val lastVerifiedAt: Long
)
```

### 2.3 DeviceFingerprint

**新建：** `app/src/main/java/com/sx/app/license/DeviceFingerprint.kt`

```kotlin
package com.sx.app.license

import android.content.Context
import android.os.Build
import android.provider.Settings
import java.security.MessageDigest

object DeviceFingerprint {
    /**
     * 获取宿主真实设备标识（SHA-256 of AndroidID）
     * 必须在宿主主进程调用，禁止从沙箱进程调用
     */
    fun get(context: Context): String {
        val raw = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ANDROID_ID
        )?.takeIf { it.isNotBlank() } ?: Build.SERIAL.takeIf { it.isNotBlank() } ?: "unknown"
        return sha256(raw).take(32)
    }

    private fun sha256(input: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(input.toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
```

### 2.4 LicenseConfig

**新建：** `app/src/main/java/com/sx/app/license/LicenseConfig.kt`

```kotlin
package com.sx.app.license

import com.sx.app.BuildConfig

object LicenseConfig {
    val BASE_URL: String get() = BuildConfig.LICENSE_BASE_URL
    val APP_KEY: String  get() = BuildConfig.LICENSE_APP_KEY
    val APP_SECRET: String get() = BuildConfig.LICENSE_APP_SECRET
    const val TIMEOUT_MS = 10_000L
    const val DEV_KEY_PREFIX = "SX-DEV-"
}
```

**Commit：** `feat(license): add LicenseServer interface, LicenseToken, DeviceFingerprint, LicenseConfig`

---

## Step 3 — 实现 LicenseServer

### 3.1 DevLicenseServer（debug only 旁路）

**新建：** `app/src/main/java/com/sx/app/license/DevLicenseServer.kt`

```kotlin
package com.sx.app.license

import com.sx.app.BuildConfig

/**
 * Debug 专用：本地校验 DEV 卡密，不请求网络
 * 仅在 BuildConfig.DEBUG = true 时使用
 */
class DevLicenseServer : LicenseServer {

    override suspend fun activate(cardKey: String, deviceId: String): LicenseResult {
        if (!BuildConfig.DEBUG) {
            return LicenseResult(false, 0L, "DevLicenseServer 仅允许 debug 包使用")
        }
        return if (cardKey.startsWith(LicenseConfig.DEV_KEY_PREFIX)) {
            // 格式 SX-DEV-YYYYMMDD，取日期作为到期时间
            val expireAt = parseDevKeyExpire(cardKey)
            LicenseResult(true, expireAt, "DEV 卡密激活成功（debug 模式）")
        } else {
            LicenseResult(false, 0L, "非 DEV 格式卡密，请使用正式卡网")
        }
    }

    override suspend fun queryStatus(cardKey: String, deviceId: String): LicenseResult? = null

    private fun parseDevKeyExpire(cardKey: String): Long {
        return try {
            // SX-DEV-YYYYMMDD → 解析 YYYYMMDD
            val dateStr = cardKey.removePrefix(LicenseConfig.DEV_KEY_PREFIX)
            val year  = dateStr.substring(0, 4).toInt()
            val month = dateStr.substring(4, 6).toInt()
            val day   = dateStr.substring(6, 8).toInt()
            java.util.Calendar.getInstance().apply {
                set(year, month - 1, day, 23, 59, 59)
            }.timeInMillis
        } catch (e: Exception) {
            System.currentTimeMillis() + 365L * 24 * 3600 * 1000 // 解析失败给1年
        }
    }
}
```

### 3.2 CardNetLicenseServer（通用卡网 HTTP 适配器）

**新建：** `app/src/main/java/com/sx/app/license/CardNetLicenseServer.kt`

```kotlin
package com.sx.app.license

import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.FormBody
import okhttp3.OkHttpClient
import okhttp3.Request
import java.security.MessageDigest
import java.util.concurrent.TimeUnit

/**
 * 通用卡网 HTTP 适配器
 * 支持大多数卡网的标准 POST activate / GET status 接口
 * 如需适配具体卡网差异，子类 override parseActivateResponse / parseStatusResponse
 */
open class CardNetLicenseServer(
    private val baseUrl: String = LicenseConfig.BASE_URL,
    private val appKey: String  = LicenseConfig.APP_KEY,
    private val appSecret: String = LicenseConfig.APP_SECRET
) : LicenseServer {

    private val client = OkHttpClient.Builder()
        .connectTimeout(LicenseConfig.TIMEOUT_MS, TimeUnit.MILLISECONDS)
        .readTimeout(LicenseConfig.TIMEOUT_MS, TimeUnit.MILLISECONDS)
        .build()

    private val gson = Gson()

    override suspend fun activate(cardKey: String, deviceId: String): LicenseResult =
        withContext(Dispatchers.IO) {
            try {
                val sign = sign(cardKey, deviceId)
                val body = FormBody.Builder()
                    .add("card_key", cardKey)
                    .add("device_id", deviceId)
                    .add("app_key", appKey)
                    .add("sign", sign)
                    .build()
                val request = Request.Builder()
                    .url("$baseUrl/activate")
                    .post(body)
                    .build()
                val response = client.newCall(request).execute()
                val json = gson.fromJson(response.body?.string(), JsonObject::class.java)
                parseActivateResponse(json)
            } catch (e: Exception) {
                LicenseResult(false, 0L, "网络请求失败：${e.message}")
            }
        }

    override suspend fun queryStatus(cardKey: String, deviceId: String): LicenseResult? =
        withContext(Dispatchers.IO) {
            try {
                val sign = sign(cardKey, deviceId)
                val request = Request.Builder()
                    .url("$baseUrl/status?card_key=$cardKey&device_id=$deviceId&app_key=$appKey&sign=$sign")
                    .get()
                    .build()
                val response = client.newCall(request).execute()
                val json = gson.fromJson(response.body?.string(), JsonObject::class.java)
                parseStatusResponse(json)
            } catch (e: Exception) {
                null // 查询失败不影响本地 Token
            }
        }

    /** 可被子类 override 以适配不同卡网的响应格式 */
    protected open fun parseActivateResponse(json: JsonObject): LicenseResult {
        val code = json.get("code")?.asInt ?: -1
        val msg  = json.get("msg")?.asString ?: "未知错误"
        return if (code == 200) {
            val data = json.getAsJsonObject("data")
            val expireAt = data?.get("expire_at")?.asLong ?: 0L
            LicenseResult(true, expireAt, msg)
        } else {
            LicenseResult(false, 0L, msg)
        }
    }

    protected open fun parseStatusResponse(json: JsonObject): LicenseResult? {
        return parseActivateResponse(json).takeIf { it.success }
    }

    private fun sign(cardKey: String, deviceId: String): String {
        val raw = cardKey + deviceId + appKey + appSecret
        val bytes = MessageDigest.getInstance("MD5").digest(raw.toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }.uppercase()
    }
}
```

**Commit：** `feat(license): implement DevLicenseServer and CardNetLicenseServer`

---

## Step 4 — 改造 LicenseManager

**文件：** `app/src/main/java/com/sx/app/license/LicenseManager.kt`

在现有 `LicenseManager` 基础上做以下改造（**保留现有方法签名，内部替换实现**）：

1. **新增字段：**

```kotlin
private val server: LicenseServer = if (BuildConfig.DEBUG) DevLicenseServer()
                                     else CardNetLicenseServer()
private val deviceId: String by lazy { DeviceFingerprint.get(context) }
private val encryptedPrefs: SharedPreferences = createEncryptedPrefs(context)
private val gson = Gson()
```

2. **新增方法 `activateWithServer()`**（suspend，供 LicenseActivity 调用）：

```kotlin
suspend fun activateWithServer(cardKey: String): LicenseResult {
    val result = server.activate(cardKey.trim(), deviceId)
    if (result.success) {
        val token = LicenseToken(
            cardKey = cardKey.trim(),
            deviceId = deviceId,
            expireAt = result.expireAt,
            activatedAt = TimeGuard.now(),
            lastVerifiedAt = TimeGuard.now()
        )
        saveToken(token)
    }
    return result
}
```

3. **改造 `isLicenseValid()` / `isActivated()`**（保持方法名兼容，内部使用 Token）：

```kotlin
fun isLicenseValid(): Boolean {
    if (BuildConfig.DEBUG && hasDevToken()) return true
    val token = loadToken() ?: return false
    if (token.expireAt == -1L) return true
    return TimeGuard.now() < token.expireAt
}
```

4. **新增 Token 读写私有方法：**

```kotlin
private fun saveToken(token: LicenseToken) {
    encryptedPrefs.edit().putString("token", gson.toJson(token)).apply()
}

private fun loadToken(): LicenseToken? {
    val json = encryptedPrefs.getString("token", null) ?: return null
    return try { gson.fromJson(json, LicenseToken::class.java) } catch (e: Exception) { null }
}

private fun hasDevToken(): Boolean {
    return loadToken()?.cardKey?.startsWith(LicenseConfig.DEV_KEY_PREFIX) == true
}

private fun createEncryptedPrefs(context: Context): SharedPreferences {
    val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
    return EncryptedSharedPreferences.create(
        context, "sx_license_store", masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
}
```

5. **异步刷新（可选，后台调用）：**

```kotlin
fun refreshInBackground(scope: CoroutineScope) {
    val token = loadToken() ?: return
    scope.launch(Dispatchers.IO) {
        val result = server.queryStatus(token.cardKey, deviceId) ?: return@launch
        if (result.success) {
            saveToken(token.copy(expireAt = result.expireAt, lastVerifiedAt = TimeGuard.now()))
        }
    }
}
```

**Commit：** `feat(license): refactor LicenseManager to use LicenseServer and EncryptedSharedPreferences`

---

## Step 5 — 改造 LicenseActivity

**文件：** `app/src/main/java/com/sx/app/ui/LicenseActivity.kt`

将激活按钮点击逻辑改为调用 `activateWithServer()`：

```kotlin
// 在激活按钮点击事件中
binding.btnActivate.setOnClickListener {
    val cardKey = binding.etCardKey.text.toString().trim()
    if (cardKey.isEmpty()) {
        Toast.makeText(this, "请输入卡密", Toast.LENGTH_SHORT).show()
        return@setOnClickListener
    }
    binding.btnActivate.isEnabled = false
    binding.progressBar.visibility = View.VISIBLE

    lifecycleScope.launch {
        val result = licenseManager.activateWithServer(cardKey)
        binding.btnActivate.isEnabled = true
        binding.progressBar.visibility = View.GONE

        if (result.success) {
            Toast.makeText(this@LicenseActivity, "激活成功", Toast.LENGTH_SHORT).show()
            startActivity(Intent(this@LicenseActivity, MainActivity::class.java))
            finish()
        } else {
            Toast.makeText(this@LicenseActivity, result.message, Toast.LENGTH_LONG).show()
        }
    }
}
```

**Commit：** `feat(license): LicenseActivity uses async activateWithServer`

---

## Step 6 — 改造 SplashActivity

**文件：** `app/src/main/java/com/sx/app/ui/SplashActivity.kt`

在现有启动校验后，追加后台异步刷新（**不阻塞启动流程**）：

```kotlin
// 现有：判断 isLicenseValid()，跳转保持不变

// 新增：有效时后台刷新
if (licenseManager.isLicenseValid()) {
    licenseManager.refreshInBackground(lifecycleScope)  // 异步，不阻塞
    // 原有跳转主界面逻辑
}
```

**Commit：** `feat(license): SplashActivity triggers background token refresh`

---

## Step 7 — 验收与测试

### 7.1 debug 包验收

```powershell
.\gradlew.bat :app:assembleDebug
adb install -r app\build\outputs\apk\debug\app-debug.apk
```

| 测试场景 | 步骤 | 期望 |
|---------|------|------|
| DEV 卡密 | 输入 `SX-DEV-20991231` | 激活成功，不请求网络 |
| 非 DEV 卡密（debug） | 输入任意非 DEV 格式 | 请求配置的卡网 URL |
| Token 持久化 | 激活后杀进程重启 | 直接进主界面，不需重新激活 |
| Token 过期模拟 | 输入 `SX-DEV-20200101`（已过期） | 跳激活页 |

### 7.2 release 包验收

```powershell
.\gradlew.bat :app:assembleRelease
adb install -r app\build\outputs\apk\release\app-release.apk
```

| 测试场景 | 期望 |
|---------|------|
| 输入 DEV 卡密 | 拒绝（非 debug 包） |
| 输入真实卡网卡密 | 成功激活 |

**最终 Commit：**
```
test(license): P-A commercial auth emulator validation pass
```

---

## 完成后同步文档

1. `docs/10_实现任务分解Backlog.md`：P-A01～P-A03 改为 `done`
2. `docs/15_产品级开发计划.md`：P-A 对应任务更新状态
3. `docs/00_项目总览.md`：工程状态更新为「产品级开发 P-A 进行中」
