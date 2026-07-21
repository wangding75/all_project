# 【开发任务】Phase 2 环境伪装 Hook — 下发指令（执行版）

> **性质说明（必读）**  
> **这是开发实现任务，不是重新做规划。**  
> 不要重写 Phase 2 计划文档、不要另起架构评审、不要扩大到 Phase 3/商业化。  
> 按下文「已批准方案 + 修正项」直接编码、联调、验收。  
> 基准文档：`docs/16_Phase2执行计划.md`、`docs/06`、Epic D；本指令为**评审修正后的可执行约束**。

| 项 | 内容 |
|----|------|
| 指令版本 | v1.1 执行版 |
| 分支建议 | `feature/sx-phase2-spoof` |
| 工期参考 | 1.5–2.5 周 |
| 完成后 | 暂停，等 Phase 3 指令 |

---

## 0. 评审结论（一句话）

**有条件批准你提交的 Implementation Plan。**  
ConfigProvider、配置下沉 `sandbox-api`、`engine-bb` 内 Hook、分身生命周期注入、探针验收方向正确。  
按 **§1 修正项** 落实后即可开发，无需再交一版总计划。

---

## 1. 修正项（相对你原稿必须遵守）

| # | 修正 | 原因 |
|---|------|------|
| M1 | Hook 框架 **只用 BlackBox/Pine 在虚拟进程内提供的能力**，不要假设宿主装了 LSPosed | 分身内生效 |
| M2 | `ConfigProvider` 必须做 **调用方校验**（仅本应用 `applicationId` / 同签名），禁止任意 App 读配置 | 安全 |
| M3 | authority 使用 **`${applicationId}.config.provider`**（已含 `.debug`） | 与包名一致 |
| M4 | 配置 key 约定写死：`global` 与 `pkg + ":" + userId`（或等价并在代码常量统一） | 全局/分身不串 |
| M5 | **仅迁移** `LocationConfig` / `DeviceProfile` / `NetworkProfile` / `SxPrefs`（定位相关部分）/ `DeviceIdGenerator` 到 `sandbox-api`；**`CameraConfig`、`LicenseManager` 留在 app**（Phase 3 / 授权） | 降范围 |
| M6 | `SxPrefs` 迁走后：app 内 `License`/`Camera` 若仍用同一 SP 文件名，保持 **同一 `PREFS_NAME` + MODE_PRIVATE**，避免拆坏授权 | 兼容 |
| M7 | 探针验收优先：**将宿主 App 导入沙箱** 或「添加本应用」白名单；`HostAppScanner` **不得永久排除** `com.sx.app` / `com.sx.app.debug`（至少 Debug 可导入自己） | 否则无法在分身内开 Probe |
| M8 | `SpoofProbeActivity` 在 Manifest **exported 按需**：建议仅本应用可启；分身内靠沙箱启动组件 | 安全 |
| M9 | 保存配置后发广播 `UPDATE_CONFIG`：**包名限定** `hostPackage + ".action.UPDATE_CONFIG"`，分身内动态注册；Host 用 `setPackage(hostPackage)` 发送 | 避免误触其它 App |
| M10 | 定位周期更新：有配置间隔则用之，默认勿死锁主线程；失败降级为 getter 改写 | 稳定 |
| M11 | D-08 Host MockLocation 真服务 **可不做** | 非门禁 |
| M12 | 测试：**模拟器先过 → 再通用真机**；不做全品牌 ROM | 产品策略 |

其余按你的 Plan 执行即可（类清单、Hook API 列表、UI 改独立设置、Probe 页）。

---

## 2. 已批准的实现方案（直接照做）

### 2.1 配置通道

- Host：`ConfigProvider`，authority = `${applicationId}.config.provider`  
- 查询时 **Host 侧完成** global / pkg+userId merge（或 Provider 返回已 merge 结果）  
- 分身：`ProfileRepository` 经 ContentResolver 读 Provider；可缓存，收 `UPDATE_CONFIG` 后刷新  

### 2.2 模型迁移

- 移至 `sandbox-api`：`LocationConfig`、`DeviceProfile`、`NetworkProfile`、`SxPrefs`、`DeviceIdGenerator`  
- 增加 `load/save(Context, pkg, userId)`；无 pkg 时走全局  
- 包名 **保持** `com.sx.app.data` / `com.sx.app.util`，减少 import 大改  

### 2.3 engine-bb

- `SpoofRuntime`、`ProfileRepository`、`LocationHook`、`DeviceHook`、`NetworkHook`、`CellHook`  
- `BlackBoxSandboxEngine`：注册 BB `AppLifecycleCallback`（或等价），在 `beforeCreateApplication(packageName, processName, context, userId)`（名称以实际上游为准）调用  
  `SpoofRuntime.onVirtualClientStart(packageName, userId, context)`  
- **仅在虚拟客户端进程**装 Hook，勿在 Host UI 进程装业务伪装  

### 2.4 app UI

- Manifest：注册 `ConfigProvider`、`SpoofProbeActivity`  
- 定位/设备/网络设置页：读 `package_name` + `user_id` extras；分身作用域标题；保存后广播  
- `AppDetailActivity`：独立设置入口覆盖 **定位 + 设备 + 网络**  
- `SpoofProbeActivity`：读系统 API 展示定位/设备/WiFi/基站（便于肉眼对比）  

---

## 3. 开发任务清单（按序勾选，勿重排阶段）

- [ ] **T1** 迁移模型到 `sandbox-api`，app/engine-bb 编译通过  
- [ ] **T2** 实现 `ConfigProvider`（含权限校验）+ 全局/分身 load/save  
- [ ] **T3** 设置页支持 extras 作用域 + 保存广播  
- [ ] **T4** `AppDetail` 三入口独立设置  
- [ ] **T5** BB 生命周期注入 `SpoofRuntime`（D-01）  
- [ ] **T6** `ProfileRepository` 读 Provider（D-02）  
- [ ] **T7** `LocationHook` + 反 Mock（D-03/D-04）  
- [ ] **T8** `DeviceHook`（D-05）  
- [ ] **T9** `NetworkHook` + `CellHook`（D-06/D-07）  
- [ ] **T10** `SpoofProbeActivity` + 允许导入自身到沙箱（D-09）  
- [ ] **T11** 分身 A/B 配置不串（D-10）  
- [ ] **T12** `assembleDebug`；**模拟器**验收；**通用真机**验收；Epic D 勾选  

---

## 4. 验收标准（全过即交付）

| # | 项 |
|---|-----|
| 1 | `assembleDebug` 成功 |
| 2 | 分身启动 log 可见 spoof 挂载 |
| 3 | 全局配置开启后，沙箱内 Probe 读数与配置一致 |
| 4 | 反 Mock：`isFromMockProvider`/`isMock` 为 false（在伪装开启时） |
| 5 | 设备 / WiFi / 基站关键字段与配置一致 |
| 6 | 分身 A、B 不同配置，Probe 互不串 |
| 7 | 保存后广播可触发分身内刷新（或杀进程再进必生效） |
| 8 | **模拟器通过后再真机通过** |
| 9 | **无** 相机流替换、**无** 商业服务端授权、**无** 重写总计划文档 |

---

## 5. 明确不要做

- 不要重做 Phase 0/1  
- 不要实现 Phase 3 虚拟相机解码  
- 不要做产品级 P-A～P-E  
- 不要引入未授权商业 VA  
- 不要把 Hook 实现写进 Activity  

---

## 6. 交付物

1. 代码提交（建议分支 `feature/sx-phase2-spoof`）  
2. MR 说明：注入点 API 名、Provider authority、模拟器/真机各测了什么  
3. `docs/10` Epic D 状态更新为 done（通过后）  
4. （可选）在 `docs/13` 附录 3 行：配置通道与生命周期回调类名  

---

## 7. 一句话任务令

> **这是开发任务：按已批准的 Phase 2 方案（ConfigProvider + sandbox-api 配置模型 + engine-bb 内 SpoofRuntime/Hooks）直接实现 Epic D；遵守本指令 §1 修正项；模拟器→通用真机验收通过后暂停，等 Phase 3。不要重做计划。**
