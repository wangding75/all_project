# 实现任务分解 Backlog

> 供排期、看板（可直接导入 Issue）。状态列由实现同学维护。  
> **S** 小 &lt;0.5d · **M** 0.5–2d · **L** 2–5d · **XL** &gt;5d  

**文档版本：** v1.0  

---

## Epic A — 文档与规范（已完成）

| ID | 任务 | 状态 | 规模 | 说明 |
|----|------|------|------|------|
| A-01 | 技术选型 ADR | done | S | docs/01 |
| A-02 | 架构 / PRD / UI 规格 | done | M | docs/02–04 |
| A-03 | 引擎接口与 Hook 设计 | done | M | docs/05–06 |
| A-04 | 开发计划与交接指南 | done | M | docs/07、09、本文 |
| A-05 | 工程规范 | done | S | docs/08 |

---

## Epic B — Phase 0：可运行 UI + Fake 引擎

| ID | 任务 | 状态 | 规模 | 依赖 | 验收要点 |
|----|------|------|------|------|----------|
| B-01 | 修复工程 Sync/编译；补 Application | done | M | — | debug APK 可装 |
| B-02 | SplashActivity 流程 | done | S | B-01 | 进 Main 或 License |
| B-03 | MainActivity + 底栏三 Tab | done | M | B-01 | 首页/应用/我的切换 |
| B-04 | HomeFragment 入口卡片 | done | S | B-03 | 跳转各模块 |
| B-05 | MeFragment 版本/设备/授权入口 | done | S | B-03 | 展示基本信息 |
| B-06 | SandboxEngine 接口落地 + Fake 实现 | done | M | B-01 | 内存增删改查 |
| B-07 | 应用列表 UI 绑定 Fake | done | M | B-06 | 空态/列表/点击 |
| B-08 | 应用选择器（本机包列表） | done | M | B-06 | 添加进 Fake |
| B-09 | 应用详情 + 菜单动作（模拟） | done | M | B-07 | 克隆/删除 Toast 或真改 Fake |
| B-10 | LocationSettings 绑定 LocationConfig | done | M | B-04 | 保存持久化 |
| B-11 | LocationPicker POI + 回传坐标 | done | M | B-10 | setResult |
| B-12 | DeviceSettings 绑定 DeviceProfile | done | M | B-04 | 随机/重置/保存 |
| B-13 | NetworkSettings 绑定 NetworkProfile | done | M | B-04 | 保存 |
| B-14 | CameraSettings 绑定 CameraConfig | done | S | B-04 | 路径选择可先 stub |
| B-15 | LicenseActivity + LicenseManager 串联 | done | M | B-02 | 开发卡密可激活 |
| B-16 | 权限申请封装（定位/通知/存储） | done | S | B-01 | 设置页调用 |
| B-17 | Phase 0 走查与修交互 | done | M | B-* | 对照 docs/04 |

**Epic B 完成定义 (DoD)：** 无 BlackBox 可演示全 UI；配置持久化；Fake 应用列表可增删。

---

## 产品级 Epic P（四阶段完成后启动）

> 战略见 `14_商业化路线图.md`，计划见 `15_产品级开发计划.md`。  
> **启动前状态：planned（blocked on Phase 0–4）。** 勿与功能四阶段抢主路径。

| Epic | 名称 | 状态 | 说明 |
|------|------|------|------|
| P-A | 商业授权（服务端+客户端） | planned | 四阶段后 |
| P-B | 安全加固 | planned | 四阶段后 |
| P-C | 质量 SLA / 矩阵 | planned | 四阶段后 |
| P-D | 合规分发 | planned | 四阶段后 |
| P-E | 观测与发版 | planned | 四阶段后 |
| P-F | 卖点增强 | planned | Go-Live 后或并行弱项 |

测试约束：**通用机型**；**模拟器通过后再真机**。

---

## Epic C — Phase 1：BlackBox 多开

| ID | 任务 | 状态 | 规模 | 依赖 | 验收要点 |
|----|------|------|------|------|----------|
| C-01 | 选定 BB 上游与可编 commit，写集成笔记 | done | M | — | docs/10 或新建 引擎笔记 |
| C-02 | 工程引入 engine-bb 模块 | done | L | C-01 | 编译通过 |
| C-03 | Application 初始化引擎 | done | M | C-02 | isReady |
| C-04 | BlackBoxSandboxEngine.install/list | done | L | C-03 | 真机导入 App |
| C-05 | launch / kill | done | L | C-04 | 分身能打开 |
| C-06 | uninstall / clearData | done | M | C-04 | 数据隔离可感 |
| C-07 | clone 多 userId | done | L | C-05 | 双开数据独立 |
| C-08 | 桌面快捷方式 | done | M | C-05 | 点击进对应分身 |
| C-09 | ENGINE 切换 fake/blackbox | done | S | C-03 | BuildConfig |
| C-10 | 兼容问题登记（机型/架构） | done | S | C-05 | 兼容表 |

**DoD：** PRD F-1.1～1.5、1.7；Android 10 或 13 真机通过。

---

## Epic D — Phase 2：定位 / 设备 / 网络伪装

| ID | 任务 | 状态 | 规模 | 依赖 | 验收要点 |
|----|------|------|------|------|----------|
| D-01 | 虚拟进程启动回调 SpoofRuntime | done | L | C-05 | 日志可见 |
| D-02 | ProfileRepository 全局/分身 merge | done | M | B-10+ | resolve 正确 |
| D-03 | Location Hook + 时间戳更新 | done | L | D-01 | Probe 坐标对 |
| D-04 | 反 Mock 检测 | done | M | D-03 | isFromMock=false |
| D-05 | Device Hook 全字段 | done | L | D-01 | Probe 通过 |
| D-06 | WiFi Hook | done | M | D-01 | SSID/BSSID |
| D-07 | Cell Hook | done | M | D-01 | 伪造或屏蔽 |
| D-08 | （可选）MockLocationService | done | M | B-10 | 辅助通道 |
| D-09 | SpoofProbe 测试包或调试页 | done | M | D-03 | 可重复验收 |
| D-10 | 独立设置作用域联调 | done | M | D-02 | 仅单分身生效 |

**DoD：** docs/06 测试矩阵 P0 项通过。

---

## Epic E — Phase 3：相机 + 授权强化

| ID | 任务 | 状态 | 规模 | 依赖 | 验收要点 |
|----|------|------|------|------|----------|
| E-01 | 图片虚拟预览（单 API 路径） | done | L | D-01 | 预览可见假图 / PreviewCallback 数据替换 |
| E-02 | 视频解码循环预览 | deferred | XL | E-01 | P1 可选扩展，标定于 docs/18 |
| E-03 | Camera1/2 覆盖策略文档化 | done | S | E-01 | docs/18 已记录覆盖策略与限制 |
| E-04 | 授权拦截启动/核心功能 | done | M | B-15 | BlackBoxSandboxEngine.launch + UI 均双向拦截 Toast |
| E-05 | TimeGuard 网络授时 | done | M | E-04 | SxApp 异步授时，LicenseManager 可信时间校验防回拨 |
| E-06 | 微漂移/扫描列表完善 | done | M | D-03/D-06 | Location/NetworkHook 已接入微漂移与扫描列表 |

**DoD：** 相机至少一路可用；授权与防回拨可用。

---

## Epic F — Phase 4：发布准备

| ID | 任务 | 状态 | 规模 | 依赖 | 验收要点 |
|----|------|------|------|------|----------|
| F-01 | ≥2 机型回归 | todo | M | E | 无阻断崩溃 |
| F-02 | 协议/隐私页 | todo | S | B-03 | 可打开 |
| F-03 | R8 与 keep 规则 | todo | M | C | release 可装 |
| F-04 | 使用说明与已知问题 | todo | S | — | README 更新 |
| F-05 | v1.0 RC 清单勾选 | todo | S | F-01 | PRD MVP 全过 |

---

## Epic G — 延后（v1.1+，不进 v1.0 必做）

| ID | 任务 | 说明 |
|----|------|------|
| G-01 | 高德/百度地图选点 | 替换 POI |
| G-02 | 轨迹模拟 | 路径点 |
| G-03 | 蓝牙伪装页 | 对齐 xh |
| G-04 | Android 14/15 专项 | 引擎适配 |
| G-05 | LSPosed 旁路模块 | 可选 |
| G-06 | 商业加固 / VMP | 按渠道 |

---

## 看板建议列

`Backlog` → `Ready` → `In Progress` → `Review` → `Done`

每次只允许 **1 个 L/XL** 任务处于 In Progress（单人时）。

---

## 优先级一句话

```
B (UI Fake) → C (多开) → D (伪装) → E (相机/授权) → F (发布)
G 全部后置
```
