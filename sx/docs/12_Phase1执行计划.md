# 闪现 (sx) Phase 1 — 执行计划（BlackBox 多开 · 可直接执行）

| 项 | 内容 |
|----|------|
| 文档版本 | v1.0 |
| 状态 | **批准执行** |
| 对应里程碑 | M2 多开可用 |
| 对应 Backlog | Epic C（C-01～C-10） |
| 前置条件 | Phase 0 已完成（Epic B done） |
| 入口 | 先读 `09`；**实现以本文为准** |

---

## 0. 范围与禁区

### 0.1 交付目标

在 **保留现有 UI** 的前提下，将 `SandboxEngine` 默认实现切换为 **BlackBox 封装**，实现真机：

1. 从本机已装应用 **导入** 到沙箱  
2. **启动** 分身（真实进程，非 Toast 模拟）  
3. **克隆** 多 userId，数据相互隔离  
4. **卸载 / 清数据**  
5. **桌面快捷方式** 可唤起对应分身  
6. **BuildConfig 可切换** `fake` / `blackbox`（调试用）

### 0.2 本阶段明确不做

| 禁止 / 延后 |
|-------------|
| 定位 / 设备 / WiFi / 相机 **真实 Hook**（属 Phase 2 Epic D） |
| 未授权商业 VA 源码 |
| 地图 SDK、商业加固 |
| 强检测 App 全量过检保证（微信等能开即可，过不了记兼容表） |
| 大改 UI 信息架构（仅适配引擎回调/进度） |

### 0.3 架构硬约束

```text
UI → SandboxProvider.getEngine() → SandboxEngine
                                      ├── FakeSandboxEngine      (保留)
                                      └── BlackBoxSandboxEngine  (本阶段新增)
```

- **禁止** Activity 直接 import BlackBox 内部包（如 `top.niunaijun.blackbox` 等，以实际上游为准）。  
- 仅 `engine-bb` / `BlackBoxSandboxEngine` 允许依赖 BB。  
- 模型继续使用 **`SandboxAppInfo`**（映射 BB 的 install/user 概念）。

---

## 1. 必读

| 顺序 | 文档 |
|------|------|
| 1 | `docs/09_开发者交接与开工指南.md` |
| 2 | **本文 `docs/12_Phase1执行计划.md`** |
| 3 | `docs/05_沙箱引擎接口.md`（接口语义） |
| 4 | `docs/10` Epic C 勾选 |
| 5 | `docs/03` PRD 中 F-1.1～1.5、1.7 |
| 6 | 参考：`xh` 多开行为（只对照，不拷贝引擎） |

---

## 2. 引擎上游选型（C-01）

### 2.1 要求

| 项 | 要求 |
|----|------|
| 来源 | 开源 BlackBox 系（如 FBlackBox/BlackBox 或仍可编译的活跃 fork） |
| 协议 | 记录 LICENSE，商用需自评合规 |
| 可编译 | 在本机 Android Studio / Gradle 能编过 **钉死 commit** |
| 记录 | 新建 `docs/13_BlackBox集成笔记.md` |

### 2.2 集成笔记必须包含

```markdown
# BlackBox 集成笔记
- 上游 URL：
- commit / tag：
- 支持系统（声称 / 实测）：
- 引入方式：submodule / 源码目录 / aar
- 与 SandboxEngine 方法映射表：
- 已知问题：
- 32/64 或插件位说明：
```

### 2.3 选型失败兜底

若首选仓 3 天内无法编过：换 fork 或降级 commit，**更新笔记**，勿强行半集成。

---

## 3. 工程结构（C-02）

推荐（可微调，但需文档化）：

```text
sx/
  app/                    # 现有 UI，依赖 sandbox 抽象
  sandbox-api/            # 可选：把 SandboxEngine 等挪出 app（非必须）
  engine-bb/              # BlackBox 源码或 wrapper 模块
    build.gradle
    src/.../BlackBoxSandboxEngine.java
  settings.gradle         # include ':engine-bb'（及 BB 子模块）
```

**最低要求：**

- `app` 的 `build.gradle`：`implementation project(':engine-bb')` 或等价  
- Debug 能 `assembleDebug`  
- Release 可不在本阶段强求  

### 3.1 权限与 Manifest

按 BB 官方 Demo **合并** 所需 permission / query / Application 配置到 `app`（或 engine 的 manifest merge）。  
保留闪现现有 Activity；BB 的 stub/进程组件按引擎要求注册。

### 3.2 冲突处理

- `minSdk` / `compileSdk` / Java 版本与 BB 对齐（以能编为准，记录差异）。  
- 包名仍为 `com.sx.app`（debug 可带 `.debug`）。  

---

## 4. SandboxProvider 与切换（C-03 / C-09）

### 4.1 BuildConfig

```gradle
// app/build.gradle defaultConfig 或 buildTypes
buildConfigField "String", "SANDBOX_ENGINE", "\"blackbox\""
// debug 可另设 "fake" 便于无引擎机调试
```

### 4.2 Provider 逻辑

```text
init(app):
  if ("fake".equals(BuildConfig.SANDBOX_ENGINE))
      engine = new FakeSandboxEngine()
  else
      engine = new BlackBoxSandboxEngine()
  engine.initialize(app)
```

- `isReady()` 在 BB 初始化完成前 UI 应禁用「启动」或显示加载。  
- 初始化失败：Toast + 可选回退 fake（需在笔记说明是否允许）。

### 4.3 Application

`SxApp`：继续只调 `SandboxProvider.init`；BB 要求的 `attachBaseContext` 等放在 `BlackBoxSandboxEngine.initialize` 或 `SxApp` 中由引擎回调处理（**优先引擎内聚**）。

若 BB 强制自定义 Application 基类：  
用 **委托/组合** 或闪现 `SxApp` 继承 BB Application（记录在笔记），避免两套 Application 冲突。

---

## 5. BlackBoxSandboxEngine 方法映射（C-04～C-08）

实现 `com.sx.app.sandbox.SandboxEngine` 全部方法。语义对齐 docs/05 + Phase 0 Fake 行为，**结果改为真实**。

| SandboxEngine | BlackBox 侧（名称因上游而异，需在笔记写死） | 验收 |
|---------------|---------------------------------------------|------|
| `initialize` | 启动 BB 核心 / 服务 | isReady=true |
| `installFromHost` | 安装本机包进虚拟空间 | 列表出现 |
| `installFromApk` | 若 BB 支持则实现；否则明确错误信息 | 可选 |
| `listInstalled` | 查询已安装虚拟应用 → `List<SandboxAppInfo>` | 与 UI 一致 |
| `get` / `isInstalled` | 按 pkg + userId | |
| `launch` | 启动虚拟应用 | **真打开目标 UI** |
| `kill` / `killAll` | 停止虚拟进程 | |
| `uninstall` | 卸载虚拟包 | 列表移除 |
| `clearData` | 清除虚拟数据 | 再进需重登/重初始化 |
| `clone` | 多开 / 新 user | 两实例独立 |
| `createShortcut` | 固定快捷方式到 `ShortcutLaunchActivity` 或 BB 推荐方式 | 桌面可点进分身 |
| `setDisplayName` | 有则实现，无则仅本地 SP 标签 | |

### 5.1 userId 映射

- 闪现 UI 使用 `userId` 0,1,2…  
- 若 BB 用 space/user 其它 ID，在 Engine 内做 **双向映射**，UI 不感知。  
- `SandboxAppInfo.displayName()` 继续展示 `#2` 等。

### 5.2 列表持久化

- **以 BB 为权威数据源**；不要与 Fake 的 SP 列表双写打架。  
- 显示名等 UI 扩展字段可另存 SP，key 带 pkg+userId。

### 5.3 ShortcutLaunchActivity

```text
onCreate:
  读 package_name, user_id
  SandboxProvider.getEngine().launch(pkg, userId)
  finish()
```

不再仅 Toast（blackbox 模式）。

### 5.4 UI 小改（允许）

| 点 | 改动 |
|----|------|
| 导入中 | 显示 ProgressDialog / 禁用按钮 |
| launch 失败 | Toast 引擎返回 message |
| AppDetail「启动」 | 去掉「模拟」文案，改为真实启动 |
| 空引擎 | isReady 前给提示 |

---

## 6. 执行步骤（严格顺序）

### Step 1 — C-01 选型与笔记（0.5–2d）

1. 选定上游 + commit  
2. 本地编过 BB Demo  
3. 写 `docs/13_BlackBox集成笔记.md`  

**出口：** 笔记合并进仓库；commit 钉死。

---

### Step 2 — C-02 接入工程（1–3d）

1. `settings.gradle` include  
2. 依赖与 Manifest 合并  
3. `assembleDebug` 成功（可先不调 UI 引擎）  

**出口：** 安装包能启动闪现 UI（仍可用 fake 启动）。

---

### Step 3 — C-03 / C-09 Provider 切换（0.5–1d）

1. `BlackBoxSandboxEngine` 骨架 + initialize  
2. BuildConfig 切换  
3. 默认 debug 可先 `blackbox`  

**出口：** 日志可见 BB 初始化成功 / 失败原因。

---

### Step 4 — C-04 安装与列表（1–2d）

1. installFromHost + listInstalled  
2. App 列表 UI 显示真实虚拟包  
3. 安装失败错误信息可读  

**出口：** 导入 1 个普通工具 App（如系统计算器/浏览器/简单三方）成功。

---

### Step 5 — C-05 启动与停止（1–2d）

1. launch 真启动  
2. kill / killAll  
3. ShortcutLaunchActivity 接 launch  

**出口：** 分身可打开、可返回闪现。

---

### Step 6 — C-06 / C-07 清数据、卸载、克隆（1–2d）

1. clearData 后状态重置可感  
2. uninstall 干净  
3. clone 出第二实例，数据互不影响（用可写本地数据的 App 验证）  

**出口：** PRD 多开隔离基本成立。

---

### Step 7 — C-08 快捷方式（0.5–1d）

1. createShortcut 可用  
2. 桌面点击进入正确 userId  

**出口：** 快捷方式闭环。

---

### Step 8 — C-10 兼容与收尾（0.5–1d）

1. 填写兼容表（机型、系统、App、结果）  
2. 已知问题列表  
3. Backlog Epic C 勾选  
4. MR / 进度说明  

**出口：** 下文验收清单通过。

---

## 7. 验收清单（全部勾选才算 Phase 1 完成）

### 7.1 构建

- [ ] `assembleDebug` 成功  
- [ ] `SANDBOX_ENGINE=blackbox` 可运行  

### 7.2 多开核心（真机，建议 Android 10 或 13）

- [ ] 导入本机第三方 App 成功  
- [ ] 列表与引擎一致  
- [ ] 启动分身进入目标 App 界面  
- [ ] 克隆第二分身，两边数据/登录态可区分  
- [ ] 清数据后该分身状态重置  
- [ ] 卸载后列表消失且不可再 launch  
- [ ] 桌面快捷方式进入对应分身  

### 7.3 架构

- [ ] UI 无直接依赖 BB 内部 API  
- [ ] `fake` 模式仍可切换用于无引擎调试（至少代码路径存在）  
- [ ] `docs/13_BlackBox集成笔记.md` 完整  

### 7.4 不测 / 不作为失败

- [ ] 钉钉/银行等强检测 App  
- [ ] 虚拟定位/改机生效（Phase 2）  
- [ ] 全机型 14/15  

---

## 8. 风险与应对

| 风险 | 应对 |
|------|------|
| BB 编不过 | 换 commit/fork，记笔记 |
| 64 位 only App | 按 BB 文档装 64 插件或记兼容表 |
| 后台启动限制 | 前台启动、引导解锁电池优化 |
| 初始化慢 | 启动页或首次进入应用 Tab 显示 loading |
| 与现有 Service/权限冲突 | 合并 Manifest，冲突项写笔记 |

---

## 9. 分支与交付

| 项 | 要求 |
|----|------|
| 分支 | `feature/sx-phase1-blackbox` |
| 提交 | 引擎接入与 UI 适配分开 commit 更佳 |
| 交付 | APK + 集成笔记 + 兼容表 + Epic C 勾选 |
| 完成后 | **停止**，等 Phase 2（伪装 Hook）指令 |

---

## 10. 一句话执行令

> 在 Phase 0 UI 之上，接入钉死 commit 的 BlackBox，实现 `BlackBoxSandboxEngine` 完整实现 `SandboxEngine`，默认 `blackbox` 模式真机完成导入/启动/克隆/清数据/卸载/快捷方式；UI 不直接依赖 BB；写好 `docs/13`；不做 Hook 伪装。
