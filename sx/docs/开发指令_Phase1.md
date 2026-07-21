# 闪现 (sx) 开发指令 — Phase 1（BlackBox 多开）

**下发对象：** Android 开发  
**指令版本：** v1.0  
**前置：** Phase 0（Epic B）已完成并合入  
**目标里程碑：** M2 多开可用  
**工期参考：** 约 7–12 人日（视 BlackBox 适配难度）  

---

## 一、你要交付什么

| 交付 | 说明 |
|------|------|
| 真沙箱多开 | 导入本机 App → 启动分身 → 克隆 → 清数据 → 卸载 |
| 快捷方式 | 桌面图标打开对应 `pkg + userId` 分身 |
| 引擎封装 | `BlackBoxSandboxEngine implements SandboxEngine` |
| 可切换 | `BuildConfig.SANDBOX_ENGINE` = `fake` \| `blackbox` |
| 文档 | `docs/13_BlackBox集成笔记.md`（上游 URL、commit、映射表、问题） |

**本阶段不做：** 定位/设备/网络/相机真实 Hook、商业 VA、地图 SDK、加固。

---

## 二、开工必读（按序）

1. `sx/docs/09_开发者交接与开工指南.md`  
2. **`sx/docs/12_Phase1执行计划.md`（执行以本文 + 12 为准）**  
3. `sx/docs/05_沙箱引擎接口.md`  
4. `sx/docs/10_实现任务分解Backlog.md` → **Epic C（C-01～C-10）**  

冲突时：**12 > 本指令摘要 > 其它**。

---

## 三、硬性约束

1. UI **只**通过 `SandboxProvider.getEngine()` 访问沙箱。  
2. **禁止** Activity/Fragment 直接 import BlackBox 内部类。  
3. 继续使用 **`SandboxAppInfo`**，禁止再引入第二套模型。  
4. **禁止**未授权商业 VirtualApp 源码。  
5. 上游 BlackBox **钉死 commit**，写入集成笔记。  
6. 保留 `FakeSandboxEngine`，便于无引擎调试。

---

## 四、任务清单（按序执行）

| 顺序 | ID | 任务 | 完成标准 |
|------|-----|------|----------|
| 1 | **C-01** | 选定 BB 上游 + 可编 commit，写 `docs/13_BlackBox集成笔记.md` | Demo 能编，笔记含映射草稿 |
| 2 | **C-02** | 工程引入 `engine-bb`（或等价），Manifest/依赖合并 | `assembleDebug` 成功 |
| 3 | **C-03** | `BlackBoxSandboxEngine.initialize` + `SxApp`/Provider 初始化 | 日志 isReady |
| 4 | **C-09** | `BuildConfig.SANDBOX_ENGINE` 切换 fake/blackbox | 两种模式可编 |
| 5 | **C-04** | installFromHost + listInstalled | 真机导入 App 进列表 |
| 6 | **C-05** | launch / kill；ShortcutLaunch 接真实 launch | 分身能打开 |
| 7 | **C-06** | uninstall / clearData | 可感隔离与清理 |
| 8 | **C-07** | clone 多 userId | 双开数据独立 |
| 9 | **C-08** | createShortcut 桌面唤起 | 快捷方式闭环 |
| 10 | **C-10** | 兼容表 + 已知问题 + Backlog 勾选 | 笔记与 MR 完整 |

详细步骤与风险见 **`docs/12_Phase1执行计划.md` 第 6～8 节**。

---

## 五、验收标准（全过才算完成）

**环境：** 至少 1 台真机，Android **10 或 13** 优先。

- [ ] Debug 包 `blackbox` 模式可安装运行  
- [ ] 导入本机第三方 App 成功  
- [ ] 启动分身进入目标应用界面（非仅 Toast）  
- [ ] 克隆第二分身，数据/状态可区分  
- [ ] 清数据、卸载行为正确  
- [ ] 桌面快捷方式进入正确分身  
- [ ] UI 无直接依赖 BB 内部 API  
- [ ] `docs/13_BlackBox集成笔记.md` 含：URL、commit、方法映射、问题  
- [ ] `fake` 切换路径仍存在  
- [ ] **未**实现 Phase 2 Hook  

**不作为失败：** 强检测 App 打不开、Android 14/15 问题（记入兼容表）。

---

## 六、分支与交付物

| 项 | 要求 |
|----|------|
| 分支 | `feature/sx-phase1-blackbox` |
| 代码 | `sx/` 内引擎接入 + 必要 UI 文案/进度 |
| 文档 | `docs/13` + Epic C 状态更新 |
| 说明 | MR：如何切换引擎、测了哪些机型/App |

完成后 **暂停开发**，等待 Phase 2（环境伪装 Hook）指令。

---

## 七、一句话命令

> **读 `docs/09` 与 `docs/12`，按 Epic C（C-01→C-10）接入钉死 commit 的 BlackBox，实现 `BlackBoxSandboxEngine` 完成真机多开闭环；UI 只走 `SandboxEngine`；不写伪装 Hook；写好集成笔记后提 MR。**
