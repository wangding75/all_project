# 闪现 (sx) 开发指令 — Phase 0

**下发对象：** Android 开发  
**指令版本：** v1.0  
**下发日期：** 2026-07-20  
**目标里程碑：** M1 — UI Demo（Fake 引擎可演示）  
**预计工期：** 约 5～7 人日（1 名中级 Android）  

---

## 一、你要交付什么

在 **不接入 BlackBox、不写系统 Hook** 的前提下，交付一个 **可安装的 Debug APK**，满足：

1. 能启动，完成 Splash → 主界面；
2. 底部三个 Tab（首页 / 应用 / 我的）可切换；
3. 首页入口可进入：应用列表、虚拟定位、设备伪装、网络伪装、虚拟相机、授权管理；
4. 应用列表由 **Fake 沙箱引擎** 驱动：可从本机已装应用「添加」、克隆、删除；
5. 定位 / 设备 / 网络 / 相机设置可保存，杀进程后配置仍在；
6. 授权页可展示设备 ID，开发卡密可激活（见下文）。

**本阶段不做：** BlackBox 集成、定位/设备 Hook、虚拟相机解码、地图 SDK、代码加固。

---

## 二、开工前必读（按顺序，勿跳过）

| 顺序 | 路径 | 要求 |
|------|------|------|
| 1 | `sx/docs/09_开发者交接与开工指南.md` | **总入口，全文阅读** |
| 2 | `sx/docs/01_技术决策ADR.md` | 知晓选型，不得擅自更改 |
| 3 | `sx/docs/04_UI交互规格.md` | UI 与交互以本文为准（对照星盒 xh） |
| 4 | `sx/docs/10_实现任务分解Backlog.md` 中 **Epic B** | 任务清单与验收 |
| 5 | `sx/docs/05_沙箱引擎接口.md` | 实现 Fake 引擎时查阅 |
| 6 | `sx/docs/07_开发计划与里程碑.md` | 了解后续阶段，本阶段只做 Phase 0 |

参考（只读对照，禁止拷贝其引擎/so）：`D:\github\all_project\xh`（尤其 `docs/`、`src_restore/`）。

产品与规范冲突时：**以 `sx/docs/` 为准**；09 与其它文档冲突时 **以 09、10 为准**。

---

## 三、工程与分支

| 项 | 说明 |
|----|------|
| 仓库 | monorepo：`D:\github\all_project`，工程目录 **`sx/`** |
| 包名 | `com.sx.app` |
| 分支建议 | 从 `main` 拉 `feature/sx-phase0-ui-fake` |
| 提交 | 中文或英文完整句；只提交 `sx/` 相关改动 |

本地编译（示例）：

```powershell
cd D:\github\all_project\sx
# 推荐用 Android Studio 打开 sx 目录并 Sync
.\gradlew.bat :app:assembleDebug
```

---

## 四、硬性约束

1. **UI 与业务只依赖** `SandboxEngine` 接口；禁止 Activity 直接依赖 BlackBox 或其它引擎实现类。  
2. 默认引擎实现为 **`FakeSandboxEngine`**（内存列表即可）。  
3. 优先复用仓库内已有 **layout XML**、`data/*` Config、`LicenseManager` 等草稿；可改，但主路径页面不能缺。  
4. 品牌与文案使用「**闪现**」，不要出现「星盒」产品名。  
5. **禁止**引入未授权商业 VirtualApp 源码或他人脱壳引擎。  
6. 变更技术选型须先更新 `docs/01_技术决策ADR.md` 并评审，不得静默改口。

---

## 五、执行任务清单（严格按序）

对应 Backlog **Epic B**。完成一项勾一项。

### 5.1 工程可运行

- [ ] **B-01** 工程 Sync/编译通过；补齐 `SxApp`、Manifest 中声明但缺失的类；Debug 包可安装启动。

### 5.2 导航骨架

- [ ] **B-02** `SplashActivity`：启动页展示后跳转 `MainActivity`（若做强制激活：未激活跳 `LicenseActivity`，策略可配置）。  
- [ ] **B-03** `MainActivity` + 底部导航：首页 / 应用 / 我的。  
- [ ] **B-04** `HomeFragment`：功能入口卡片，跳转各模块。  
- [ ] **B-05** 我的页：版本号、设备 ID、进入授权。

### 5.3 Fake 沙箱

- [ ] **B-06** 定义/落地 `SandboxEngine` + `FakeSandboxEngine`（对齐 `docs/05`：install 模拟、list、launch 可 Toast、clone、uninstall、clearData 等核心方法）。  
- [ ] **B-07** 应用列表绑定 Fake 数据；空状态文案。  
- [ ] **B-08** 应用选择器：列出本机可导入应用，选中后加入 Fake 列表。  
- [ ] **B-09** 应用详情：启动（模拟）、克隆、删除；必要时接「独立设置」入口（可先跳转全局设置并带 pkg 参数）。

### 5.4 设置与授权

- [ ] **B-10** 虚拟定位设置页 ↔ `LocationConfig` 持久化。  
- [ ] **B-11** 地点选择（内置 POI 或手动坐标）回传 lat/lng。  
- [ ] **B-12** 设备伪装页 ↔ `DeviceProfile`（随机/重置/保存）。  
- [ ] **B-13** 网络伪装页 ↔ `NetworkProfile`。  
- [ ] **B-14** 虚拟相机设置页 ↔ `CameraConfig`（选文件可先 stub 路径）。  
- [ ] **B-15** 授权页串联 `LicenseManager`；开发卡密格式：`SX-DEV-YYYYMMDD`（例：`SX-DEV-20991231`）。  
- [ ] **B-16** 基础权限申请封装（按需：定位、通知、存储/媒体、查询应用列表）。  
- [ ] **B-17** 对照 `docs/04` 走查主路径，修阻断性问题。

### 建议类放置（可微调）

```text
com.sx.app.SxApp
com.sx.app.ui.SplashActivity / MainActivity / LicenseActivity
com.sx.app.ui.home.HomeFragment
com.sx.app.ui.me.MeFragment
com.sx.app.ui.sandbox.*
com.sx.app.ui.location.* / device.* / network.* / camera.*
com.sx.app.sandbox.SandboxEngine
com.sx.app.sandbox.FakeSandboxEngine
com.sx.app.sandbox.SandboxProvider   // 提供 Engine 单例
```

---

## 六、验收标准（全部满足才算完成本指令）

| # | 验收项 | 通过标准 |
|---|--------|----------|
| 1 | 安装启动 | Debug APK 安装后可进入主界面 |
| 2 | 三 Tab | 首页 / 应用 / 我的切换正常 |
| 3 | 首页入口 | 可进入定位、设备、网络、相机、授权、应用相关页 |
| 4 | Fake 应用流 | 添加本机应用 → 列表可见 → 可克隆 → 可删除 |
| 5 | 配置持久化 | 改定位/设备等保存后，强杀进程再进仍在 |
| 6 | 授权 | 输入合法开发卡密显示已激活；设备 ID 可展示 |
| 7 | 依赖边界 | 工程中 **无** BlackBox 依赖也能完整运行上述路径 |
| 8 | 文档一致 | 主路径与 `docs/04` 无阻断性缺失页面 |

**不通过示例：** 仅有 layout 无法点；Activity 缺失导致闪退；未实现 Fake 引擎用写死假数据且无法「添加应用」。

---

## 七、交付物

1. 合并请求 / 提交：分支 `feature/sx-phase0-ui-fake`（或等价命名）。  
2. 简短说明（MR 描述或 `sx/docs/进度记录.md`）：  
   - 完成了哪些 B-xx；  
   - 已知问题；  
   - 如何编译安装。  
3. （可选）Demo 录屏或 3～5 张截图：启动、首页、应用列表、某一设置页、授权页。

---

## 八、完成后下阶段预告（本指令范围外）

Phase 0 验收通过后，**另发指令** 启动 **Epic C（BlackBox 多开）**。  
在收到下一指令前，不要擅自大范围接入引擎或写 Hook。

---

## 九、问题升级

| 情况 | 处理 |
|------|------|
| 文档矛盾 | 以 `docs/09`、`docs/10` 为准，并在进度里备注 |
| 编译环境/SDK 问题 | 先自行排查，阻塞 &gt; 1 天书面同步 |
| 希望改选型（如改用 VA） | 停止实现，先走 ADR 变更，勿直接改代码方向 |

---

## 十、一句话命令

> **阅读 `sx/docs/09_开发者交接与开工指南.md`，严格按 `docs/10` Epic B（B-01～B-17）完成 Phase 0：可安装 UI + FakeSandboxEngine；对照本文第六节验收通过后提交付。**
