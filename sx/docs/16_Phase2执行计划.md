# 闪现 (sx) Phase 2 — 执行计划（环境伪装 Hook）

| 项 | 内容 |
|----|------|
| 文档版本 | v1.0 |
| 状态 | **批准执行** |
| 对应里程碑 | M3 伪装可用 |
| 对应 Backlog | Epic D（D-01～D-10） |
| 前置 | Phase 1 通过（BlackBox 多开可编可跑） |
| 机型/测试 | **通用机型**；**模拟器通过 → 再真机**（见 docs/14） |

---

## 0. 范围

### 0.1 交付目标

在 **沙箱分身进程内**（非仅 Host UI）使配置生效：

1. **虚拟定位**：坐标/精度/时间戳更新；反 `isFromMockProvider`（及约定 mock 标志）  
2. **设备指纹**：IMEI/AndroidId/Build/SIM 等按 `DeviceProfile`  
3. **网络/基站**：SSID/BSSID、扫描列表、Cell 标识按 `NetworkProfile`  
4. **全局 / 分身配置合并**：`ProfileRepository.resolve(pkg, userId)`  
5. **探针验收**：自研或调试页 `SpoofProbe` 在分身内读 API 与配置一致  

### 0.2 明确不做

| 禁止 |
|------|
| 虚拟相机完整解码（Phase 3） |
| 地图 SDK、轨迹完整产品化（可后置字段） |
| 商业授权服务端（产品级 P-A） |
| 未授权 VA 源码 |
| 以强检测 App 唯一验收（可抽检记兼容表） |

### 0.3 架构硬约束

```text
分身启动
  → SpoofRuntime.onVirtualClientStart(pkg, userId)
  → ProfileRepository.resolve(pkg, userId)
  → Location / Device / Network Hook 安装
```

- Hook **只装在虚拟客户端进程**（或 BB 官方推荐的注入点），Host UI 进程可不装业务伪装 Hook。  
- 配置读取：Host 写入 `MODE_PRIVATE`；跨进程用 BB 提供的配置通道 / 文件 / ContentProvider **择一并写进集成笔记附录**，禁止再引入 WORLD_READABLE 作为主方案（除非文档论证必要且仅 debug）。  
- UI 仍只通过现有设置页写 Config；**不**在 Activity 里直接调 Pine/BB Hook API。

---

## 1. 必读

1. `docs/09`  
2. **本文 `docs/16`**  
3. `docs/06_Hook与伪装设计.md`  
4. `docs/05` + Phase 1 `docs/13`（引擎注入点）  
5. `docs/10` Epic D  
6. `docs/14` 机型与模拟器→真机  

---

## 2. 模块与类（建议）

```text
app 或 spoof 模块:
  com.sx.app.spoof.SpoofRuntime
  com.sx.app.spoof.ProfileRepository
  com.sx.app.spoof.hook.LocationHook
  com.sx.app.spoof.hook.DeviceHook
  com.sx.app.spoof.hook.NetworkHook
  com.sx.app.spoof.hook.CellHook
  com.sx.app.ui.probe.SpoofProbeActivity   # 可装入沙箱的探针，或独立 probe 模块

engine-bb:
  在虚拟进程启动回调中调用 SpoofRuntime（唯一允许依赖 BB 回调的粘合层）
```

粘合优先放在 `engine-bb` 的 Client 生命周期回调；若 BB 提供 Xposed/Pine 模块入口，在笔记中写明注册方式。

---

## 3. 任务拆分（Epic D）

| ID | 任务 | 完成标准 |
|----|------|----------|
| **D-01** | 虚拟进程启动挂载 `SpoofRuntime` | 分身启动日志可见 `spoof installed pkg=.. user=` |
| **D-02** | `ProfileRepository` 全局/分身 merge | 独立设置 extras 可覆盖全局 |
| **D-03** | Location Hook + 时间戳周期更新 | 探针 lat/lng/accuracy 与配置一致；time/elapsed 变化 |
| **D-04** | 反 Mock 检测 | `isFromMockProvider`/`isMock` 对目标为 false |
| **D-05** | Device Hook 全字段 | 探针读到 brand/model/androidId 等 |
| **D-06** | WiFi Hook | SSID/BSSID（及约定 MAC） |
| **D-07** | Cell Hook | MCC/MNC/LAC/CID 或等效屏蔽真实基站 |
| **D-08** | （可选）Host `MockLocationService` 真注入 | 非必须；沙箱内 Hook 为主 |
| **D-09** | SpoofProbe 测试包或沙箱内调试页 | 可重复验收 |
| **D-10** | 独立设置作用域联调 | 仅该分身坐标/设备不同 |

---

## 4. 执行步骤

### Step 1 — 注入点打通（D-01）

1. 在 BB 虚拟客户端启动路径调用 `SpoofRuntime.onVirtualClientStart`。  
2. 打日志；失败不影响进程崩溃（可降级 no-op + error log）。  

**出口：** 启动任一分身 logcat 可见挂载日志。

### Step 2 — 配置合并与跨进程读（D-02）

1. `resolve`：instance 覆盖 global（location/device/network 各模块 `enabled` 与字段）。  
2. 实现虚拟进程可读配置（方案写入 `docs/13` 附录或新建 `docs/17_Spoof配置通道.md`）。  

**出口：** 改 Host 配置 → 杀分身再开 → 探针读到新值。

### Step 3 — 定位（D-03/D-04）

按 `docs/06` Hook 点实现；默认 50ms 级时间戳更新（可配置间隔，注意耗电）。  

**出口：** 探针 + 可选系统地图类 App 抽检。

### Step 4 — 设备（D-05）

Build 字段 + Telephony + Android ID；高版本 IMEI 空为可接受并文档说明。  

### Step 5 — 网络/基站（D-06/D-07）

WiFi 连接信息 + 扫描列表；Cell 伪造或清空。  

### Step 6 — 探针与分身作用域（D-09/D-10）

1. 探针 APK 导入沙箱或内置 Debug Activity。  
2. 分身 A/B 不同配置互不串。  

### Step 7 — 测试与勾选

1. **模拟器** 冒烟全过。  
2. **通用真机** 再过一遍。  
3. Epic D 勾选；兼容问题记表。  

---

## 5. 验收清单

### 5.1 构建

- [ ] `assembleDebug` 成功  

### 5.2 功能（模拟器 → 通用真机）

- [ ] 分身启动有 Spoof 挂载日志  
- [ ] 定位：配置开 → 探针坐标一致且时间在变；反 Mock 通过  
- [ ] 设备：关键字段与配置一致  
- [ ] WiFi/基站：与配置一致或真实基站被屏蔽  
- [ ] 全局/分身覆盖正确  
- [ ] 配置关闭后行为恢复或不再覆盖（约定一种并写清）  

### 5.3 不测

- 钉钉/银行强检全过  
- 虚拟相机预览替换  
- 商业服务端授权  

---

## 6. 分支与交付

| 项 | 要求 |
|----|------|
| 分支 | `feature/sx-phase2-spoof`（自 Phase1 分支或 main 合入后拉出） |
| 文档 | Hook 注入点与配置通道补充进 `13` 或 `17` |
| 交付 | 探针使用说明 + 模拟器/真机结果 |

完成后暂停，等待 Phase 3（虚拟相机）指令。

---

## 7. 一句话

> 在 BlackBox 分身进程启动时挂载 SpoofRuntime，按 Profile 合并结果安装定位/设备/网络/基站 Hook；用探针在模拟器再真机验收；不做相机与商业中台。
