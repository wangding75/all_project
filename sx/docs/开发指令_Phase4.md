# 【开发任务】Phase 4 — 发布准备（功能 RC）

> **这是开发任务，不是重做规划。**  
> **角色：** 执行 Agent 只负责实现 + **在 main 上 commit**；Review 由规划角色基于 **commit hash** 进行。  
> **不要**进入产品级商业中台（docs/15），除非另有指令。

| 项 | 内容 |
|----|------|
| 指令版本 | v1.0 |
| 前置 | Phase 3 PASS @ `bdc8c2f`；当前在 **main** |
| 对应 | Epic F（F-01～F-05） |
| 细则 | `docs/20_Phase4执行计划.md` |
| 工期 | 约 3–5 人日 |

---

## 一、你要交付什么

| ID | 交付 | 完成标准 |
|----|------|----------|
| **F-01** | 回归 | 模拟器冒烟全过 → **≥1 台通用真机**（建议 2 台）关键路径无阻断崩溃；写 `docs/21_回归记录.md` |
| **F-02** | 协议/隐私 | 用户协议、隐私政策可从 App 内打开（关于/我的/首次启动其一即可） |
| **F-03** | Release | `assembleRelease` 成功可装；开启 minify 时 keep 不炸 BB/Hook；主路径可启动 |
| **F-04** | 说明文档 | 更新 README：如何编译、激活卡密、多开、伪装、相机限制；或 `docs/22_已知问题.md` |
| **F-05** | RC 清单 | `docs/23_功能RC清单.md`：对照 PRD/MVP 与 Phase0–3 DoD 勾选，例外写明 |

**本阶段结束标志：** 功能四阶段 **内测/RC 基线**，**不是**商业 Go-Live。

---

## 二、硬性约束

1. **在 `main` 上开发**；做完 **必须 `git commit`**，回报 **hash**。  
2. Review **只认已提交代码**；未 commit 不得宣称完成。  
3. 测试：**模拟器通过后再真机**；机型 **通用优先**。  
4. 范围：**不要**做服务端卡密、商业 VMP、地图、Camera2/Surface 全量、14/15 保证。  
5. 已知限制（相机 Surface、DEV 卡密等）写进已知问题，勿写成已支持。  

---

## 三、任务顺序

| 序 | 任务 |
|----|------|
| 1 | 列回归用例，**模拟器**跑 F-01 清单 |
| 2 | **通用真机**回归，填 `docs/21_回归记录.md` |
| 3 | F-02 协议/隐私页 + 入口 |
| 4 | F-03 R8/proguard + `assembleRelease` 验证 |
| 5 | F-04 README / 已知问题 |
| 6 | F-05 RC 清单；`docs/10` Epic F 勾 done |
| 7 | **commit**，消息示例见下；申请 Review |

---

## 四、回归最低路径（F-01）

1. 安装 → Splash → `SX-DEV-20991231` 激活 → 三 Tab  
2. 导入应用 → 启动 / 克隆 / 清数据 / 卸载  
3. 定位+设备+网络开启 → 分身 Probe（能测则测）  
4. 相机开启+图片 → 文档约定的 PreviewCallback 验证方式  
5. 无卡密/过期时启动分身失败且有提示  

---

## 五、验收（Review 门禁）

- [ ] 存在 commit，且包含 F-01～F-05 产出  
- [ ] `assembleDebug` + `assembleRelease` 成功（或书面豁免）  
- [ ] `docs/21` 有模拟器+真机记录  
- [ ] 协议页可打开  
- [ ] README/已知问题可读  
- [ ] `docs/23` RC 清单完整  
- [ ] 未宣称商业可售  

---

## 六、提交与回报

```text
git checkout main
# ... 开发 ...
./gradlew :app:assembleDebug :app:assembleRelease
git add sx/
git commit -m "feat(phase4): release prep - regression, legal pages, R8, RC checklist"
# 回报: commit hash + 构建结果 + 回归机型列表
```

---

## 七、一句话任务令

> **在 main 上完成 Epic F：回归（模拟器→通用真机）、协议隐私页、Release/R8、使用说明与 RC 清单；做完必须 commit 并报 hash；不做商业中台。**
