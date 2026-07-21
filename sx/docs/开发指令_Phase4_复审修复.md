# 【开发任务】Phase 4 Review 修复指令（基于当前 main 提交）

> **这是开发任务，不是重做规划。**  
> **角色：** 执行 Agent = 实现 + **main 上 commit**；规划 = Review 已提交代码。  
> **基线：** 当前 main 含 `5806e98`（Phase4 代码）+ `435f37a`（F-01 纠偏）+ `be7c20f`（模拟器手册）等。  
> **前次 Review 结论：** Phase 4 **未收口**——F-02/F-03/F-04 代码可接受；**F-01 实机/模拟器点按未完成**；文档状态不一致。

| 项 | 内容 |
|----|------|
| 指令版本 | v1.0（复审修复） |
| 工作分支 | **main** |
| 测试手册 | `docs/27_模拟器测试验收手册.md`（下午模拟器优先） |
| 策略 | docs/24：未测不得写 PASS；钉钉为首发卖点但 **本修复不强制钉钉全过** |

---

## 0. 问题回顾（为何要修）

| 问题 | 说明 |
|------|------|
| **虚假回归** | `5806e98` 的 `docs/21` 曾写模拟器+真机全 PASS，**未真实点按**（已部分纠偏为待测） |
| **F-01 未完成** | 门禁要求设备路径点按；当前仅为构建+代码走查 |
| **文档打架** | `docs/21`/`23` 写 F-01 待测，但 **`docs/10` 仍 F-01=done**；`docs/23` 文末仍可能夸大「全验证通过」 |
| **Proguard 包名** | keep 含 `top.niunaijun.pine`，实际 Pine 多为 `top.canyie.pine`（建议修） |

---

## 1. 必须完成的修复项（Must）

### M1. 按手册完成 **模拟器** 点按，并如实填表

1. 打开并严格执行：`docs/27_模拟器测试验收手册.md`  
2. 打包安装：

```powershell
cd D:\github\all_project\sx
.\gradlew.bat :app:assembleDebug
adb install -r app\build\outputs\apk\debug\app-debug.apk
```

3. 卡密：`SX-DEV-20991231`；包名：`com.sx.app.debug`  
4. 将 **真实** PASS/FAIL 写入：  
   - 手册内表格（可复制）  
   - 同步更新 **`docs/21_回归记录.md`**（标题写清「模拟器实测」；禁止再抄模板全绿）  
5. **禁止**未点按填 PASS。

**模拟器最低必过路径（与 27 一致）：**

- 激活 → 三 Tab  
- 导入轻量 App → 启动 / 克隆 / 清数据 / 卸载  
- 定位·设备·网络保存；分身内探针或可读场景（能测则测，测不到写 SKIP+原因）  
- 未激活启动分身有拦截提示  
- 相机：仅记 PreviewCallback 范围；Surface 真画面记已知问题即可  

### M2. 统一文档状态（与实测一致）

| 文件 | 要求 |
|------|------|
| `docs/10_实现任务分解Backlog.md` | F-01：模拟器实测完成前用 **`todo` 或 `in_progress`**；模拟器通过后可 `done` **并注明「仅模拟器」**；真机未做不得暗示全 RC |
| `docs/21_回归记录.md` | 以 **27 手册实测** 为准重写结论区 |
| `docs/23_功能RC清单.md` | F-01 与 21 一致；**删除**「Phase0–4 均已验证通过 / 达 RC 基线」等夸大句；改为「代码与构建就绪；模拟器实测结果见 21；真机待统一测试波次」 |
| `docs/22_已知问题.md` | 补充本场 FAIL/SKIP（若有） |

### M3. 构建再确认

```powershell
cd D:\github\all_project\sx
.\gradlew.bat :app:assembleDebug :app:assembleRelease
```

两者均 SUCCESS；release 安装后至少 **冷启动进主界面**（模拟器上点一次）。

### M4. Commit（强制）

在 **main** 上提交，回报 hash：

```text
test(phase4): emulator regression results and sync F-01 docs

# 或分两笔：先 test 文档，再 fix backlog
```

工作区保持干净后再申请 Review。

---

## 2. 强烈建议（Should，本轮尽量做）

| ID | 任务 |
|----|------|
| S1 | `proguard-rules.pro` 增加 `-keep class top.canyie.pine.** { *; }`（及实际用到的包），release 再启一次分身冒烟 |
| S2 | `get_camera_bytes` 限制只读 host `…/camera/` 目录（安全债，可本轮或单开 commit） |
| S3 | README 明确：当前 **非商业可售**；钉钉 **专项未完成** |

### 真机

- **本修复指令不强制今天下午真机**（与产品「统一测试后置」一致）。  
- 真机列入后续「统一测试波次」；本轮 F-01 以 **模拟器实测 + 文档诚实** 为收口条件。  
- 若下午有真机：按 27 手册加一节真机表，仍禁止假 PASS。

---

## 3. 明确不要做

- 不要重做 Phase 0–3 功能  
- 不要宣称钉钉换图可用  
- 不要进入产品级商业中台  
- 不要再提交「未测全绿」的回归表  

---

## 4. 验收门禁（复审时）

规划 Review **只认 commit**，并检查：

- [ ] 存在含 **真实模拟器结果** 的 `docs/21`（非「仅走查」）  
- [ ] `docs/10` / `21` / `23` 对 F-01 描述 **一致**  
- [ ] `docs/23` 无夸大「全验证通过」  
- [ ] `assembleDebug` + `assembleRelease` 在说明中有结果  
- [ ] commit message 与内容匹配  

**PASS 含义：** Phase 4 **模拟器侧收口**（功能 RC 文档 + 构建 + 模拟器点按）。  
**仍须后置：** 通用真机全量、钉钉专项 Wave 2。

---

## 5. 回报模板（执行方提交后粘贴）

```text
Commit: <hash>
assembleDebug: SUCCESS/FAIL
assembleRelease: SUCCESS/FAIL
模拟器: <AVD 名称 / API>
27 手册结论: PASS(仅模拟器) / 有缺陷 / 阻断
docs/10 F-01 状态: 
docs/21 是否含真实点按: 是/否
已知 FAIL 列表:
```

---

## 6. 一句话任务令

> **在 main 上按 docs/27 完成模拟器真实点按，重写 21/10/23 使 F-01 状态一致且不夸大，确认 debug/release 可构建，commit 后报 hash 复审；真机与钉钉统一测试后置。**
