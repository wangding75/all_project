# 【开发任务】Phase 4 Review 遗留 — **仅代码/文档修复**

> **这是开发任务，不是重做规划，也不做模拟器/真机测试。**  
> **本轮不做：** `docs/27` 点按、设备回归、钉钉实测。  
> **本轮只做：** Phase 4 Review 指出的、可在仓库内落地的 **代码 + 文档一致性** 修复。  
> **分支：** `main` · 做完 **必须 commit** · 报 hash · Review 只认提交。

| 项 | 内容 |
|----|------|
| 指令版本 | v1.0 |
| 前置 Review | Phase 4：F-02/03/04 代码可接受；**F-01 实测后置**；文档与 proguard/安全债待修 |
| 关联 | `docs/开发指令_Phase4_复审修复.md`（其中设备测试部分 **本轮跳过**） |

---

## 0. 范围切分

| 类别 | 本轮 |
|------|------|
| 模拟器/真机点按、填 PASS | **不做**（统一测试波次再做） |
| 文档状态自相矛盾 | **做** |
| Proguard keep 错误/不全 | **做** |
| `get_camera_bytes` 任意路径读取 | **做** |
| CameraHook hostPkg 写法 | **做** |
| README 口径（非商业/钉钉未完成） | **做** |

---

## 1. 必须修复（Must）

### M1. 文档状态一致（消灭「假 done」）

| 文件 | 修改要求 |
|------|----------|
| `docs/10_实现任务分解Backlog.md` | **F-01** 改为 `todo` 或 `in_progress`，验收说明改为「构建/文档就绪；**设备点按后置**」。**禁止**在未测时保持 `done` 且写「无阻断崩溃」 |
| `docs/21_回归记录.md` | 保持/强化：**仅代码走查+构建 PASS，点按待测**；删除任何仍残留的「模拟器 7/7 PASS / 真机 PASS」表述 |
| `docs/23_功能RC清单.md` | F-01 与 21 一致（进行中/待测）；**删除或改写**文末「Phase0–4 均已验证通过 / 达 RC 基线」等夸大结论 → 改为「**代码与构建就绪；设备回归待统一测试波次**」 |
| `docs/22_已知问题.md` | 增加一条：功能 RC **未含**完整模拟器/真机点按验收（若尚未写） |

### M2. Proguard / R8 keep 补全

文件：`app/proguard-rules.pro`

1. 增加（或修正）与实际依赖一致的 keep，例如：

```proguard
-keep class top.canyie.pine.** { *; }
-keep class top.niunaijun.blackbox.** { *; }
-keep class com.sx.app.sandbox.spoof.** { *; }
```

2. 原有 `top.niunaijun.pine.**` 可保留但**不能只靠它**（Pine 实际包名多为 `top.canyie.pine`）。  
3. 本地执行：`.\gradlew.bat :app:assembleRelease` 必须 SUCCESS（**只验证编译打包，不要求装机点按**）。

### M3. `get_camera_bytes` 路径白名单

文件：`app/.../ConfigProvider.java` 的 `get_camera_bytes` 分支

**要求：** 只允许读取宿主应用相机目录下的文件，拒绝任意路径。

建议逻辑：

```text
allowedRoots = [
  context.getExternalFilesDir("camera"),
  new File(context.getFilesDir(), "camera"),
  context.getExternalCacheDir() // 若 VirtualCamera 会写到 cache，可纳入
]
canonicalPath 必须 startsWith 某一 allowedRoot 的 canonicalPath
否则不读文件、打日志、返回空
```

防止 Provider 被滥用来读任意可读文件。

### M4. `CameraHook` hostPkg 简化

文件：`engine-bb/.../CameraHook.java` 的 `prepareFakeMediaData`

**现状问题：** 用 `resolveCamera(...) != null ? getHostPkg() : getPackageName()` 绕弯，易误解。

**改为：**

```java
String hostPkg = top.niunaijun.blackbox.BlackBoxCore.getHostPkg();
// 若 getHostPkg 为空再 fallback context.getPackageName()
```

---

## 2. 建议修复（Should，本轮尽量做）

| ID | 任务 |
|----|------|
| S1 | README 显著位置：当前为 **功能内测基线**；**非商业可售**；**钉钉专项未完成、未测不得宣称可用** |
| S2 | `docs/22` 同步相机路径白名单、Surface 限制、F-01 后置 |
| S3 | 确认 `PrivacyPolicyActivity` 仅在 Manifest 注册且 Me 可进（代码已有则只核对，不重写） |

---

## 3. 明确不做

- ❌ 模拟器/真机功能点按、填写设备 PASS  
- ❌ 钉钉 Wave 0/1 大功能（另有专项指令）  
- ❌ 产品级商业中台  
- ❌ 重写 Phase 0–3 业务  

---

## 4. 完成标准（本轮 Review 门禁）

- [ ] `docs/10` F-01 **不是**未测却 `done`+「无崩溃」  
- [ ] `docs/21` / `23` / `10` 对 F-01 **表述一致**，无「全验证通过」夸大  
- [ ] `ConfigProvider.get_camera_bytes` 有路径白名单  
- [ ] `CameraHook` hostPkg 使用 `BlackBoxCore.getHostPkg()`  
- [ ] proguard 含 `top.canyie.pine`（或等价正确包名）  
- [ ] `assembleDebug` + `assembleRelease` **编译成功**  
- [ ] **main 上 commit**，回报 hash  

**本轮 PASS 含义：** Phase 4 **代码/文档债收口**（不含设备回归）。  
**设备回归：** 仍按 `docs/27` 另场执行，不得在本轮假填。

---

## 5. 提交与回报

```powershell
cd D:\github\all_project\sx
.\gradlew.bat :app:assembleDebug :app:assembleRelease
cd D:\github\all_project
git add sx/
git commit -m "fix(phase4): harden camera provider path, proguard keep, sync F-01 docs"
```

回报模板：

```text
Commit: <hash>
assembleDebug: SUCCESS/FAIL
assembleRelease: SUCCESS/FAIL
已改文件: 10/21/23/22, ConfigProvider, CameraHook, proguard, README...
未做: 模拟器/真机点按（按指令跳过）
```

---

## 6. 一句话任务令

> **先不做模拟器测试：只修 Phase 4 Review 遗留的文档假 done、proguard keep、get_camera_bytes 路径限制、CameraHook hostPkg；编译通过后 commit 报 hash。**
