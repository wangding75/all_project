推荐模型：GPT-5.6 Sol
推理等级：high
是否新窗口：继续当前窗口

```text
本任务为执行任务，直接执行当前任务。

禁止：
1. 重新制定计划；
2. 修改任何诊断脚本；
3. 修改 SX 业务代码、Hook 代码或授权逻辑；
4. 重新打包夸克；
5. 人工点击代替脚本启动；
6. 人工填写 PID、UID、Flags、存活时间或崩溃结果；
7. 复用历史 tombstone、历史 logcat 或历史 result.json；
8. 在脚本或 Validator 返回非零后继续执行；
9. 在证据不足时写“根因已确认”；
10. amend、rebase、squash、force push；
11. 合并当前分支到 main。

# 任务名称

SX-QK-01：执行夸克模拟器自动化崩溃定位

# 已知事实

1. MuMu 模拟器中，系统直接启动夸克正常；
2. SX 已通过 Hello World Self-Aware、Markor、Tasks.org 基础兼容验证；
3. 当前问题是夸克在 SX 内的专项兼容失败；
4. 本轮只执行自动化证据采集和分析，不开发修复；
5. 四个底层诊断脚本此前已在 Windows PowerShell 完成 Parser 与 19 个 Fixture 实跑；
6. 本轮新增 Quark 驱动和汇总脚本必须先通过包内 Parser 门禁。

# 工作目录

D:\github\all_project\sx

# 脚本目录

tools\quark-automation\

必须存在：
- collect-native-crash.ps1
- run-native-ab-matrix.ps1
- validate-native-diagnostics.ps1
- test-gate1-fixtures.ps1
- test-quark-automation-scripts.ps1
- run-quark-diagnostics.ps1
- summarize-quark-diagnostics.ps1

# 一、执行前检查

执行：

git branch --show-current
git status --short --untracked-files=all
git log -5 --oneline

要求：
- 当前分支必须是 feature/sx-native-crash-diagnostics；
- 不修改、删除或格式化脚本；
- 若存在未知工作区修改，先报告并停止；
- 记录开始 HEAD。

# 二、脚本完整性和语法门禁

执行：

powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\quark-automation\test-quark-automation-scripts.ps1

必须同时出现：
- PowerShell parser preflight passed；
- All 19 fixture cases passed；
- Quark automation script gate passed。

任一失败，立即停止，不连接设备，不修改脚本。

# 三、构建 SX

执行：

.\gradlew.bat :app:assembleDebug

记录：
- 构建结果；
- APK 绝对路径；
- APK SHA-256；
- 当前 Git HEAD。

禁止修改 LicenseManager。当前测试阶段的授权跳过状态保持现状，不在本任务处理。

# 四、连接正在运行的 MuMu 模拟器

执行：

adb devices -l

只使用实际显示为 device 的 serial。
禁止猜测端口。

记录：
- serial；
- Android 版本；
- API Level；
- ro.product.cpu.abilist；
- ro.dalvik.vm.native.bridge；
- SX 包版本；
- 夸克包版本；
- SX UID；
- 系统夸克 UID。

若无在线模拟器，状态标记 WAITING_FOR_EMULATOR，停止，不伪造结果。

# 五、执行完整自动化

使用 adb devices 返回的真实 serial：

powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\quark-automation\run-quark-diagnostics.ps1 `
  -DeviceSerial "<真实 serial>" `
  -HostPackage "com.sx.app.debug" `
  -TargetPackage "com.quark.browser" `
  -VirtualUserId 0 `
  -ObservationSeconds 180 `
  -SandboxRuns 3

自动化包含：
- Q0/A7：系统直接启动夸克 1 次；
- Q1/A1：SX 默认 Flags=63 启动 3 次；
- Q2/A6：SX Flags=47 启动 3 次；
- Q3：自动提取 Service 路由、进程、UC Renderer、Native Bridge、mmap/ashmem 和崩溃证据。

禁止增加、删除或替换测试组合。

# 六、自动化失败规则

以下任一情况必须立即停止：
- Parser 或 Fixture 失败；
- adb 设备不在线；
- APK 安装失败；
- target_started=false；
- SX_TARGET_BOUND 缺失；
- PID/UID/cmdline/starttime 不匹配；
- requestedFlags 与 appliedFlags 不一致；
- Collector 返回非零；
- Validator 返回非零；
- result.json 缺失；
- status=INVALID_EVIDENCE；
- 同一 tombstone 被重复使用。

不得为了跑完矩阵而绕过失败。

# 七、产物检查

定位最新目录：

artifacts\quark-automation\quark-session-<timestamp>\

必须检查：
- session-manifest.json；
- quark-diagnostic-summary.json；
- quark-diagnostic-summary.md；
- Q0、Q1、Q2 每轮 result.json；
- logcat-all.txt；
- logcat-crash.txt；
- process-before.txt；
- process-after.txt；
- maps-after.txt；
- fd-list.txt；
- mountinfo.txt；
- tombstone-before.json；
- tombstone-after.json；
- quark-route-evidence.txt。

# 八、分析要求

只根据本轮产物回答：
1. Q0 系统夸克是否完整存活 180 秒；
2. Q1 三轮最先失败的进程分别是什么；
3. Q2 三轮关闭 Native Master 后结果是否变化；
4. 每轮目标 PID、UID、cmdline、starttime；
5. 每轮 requestedFlags/appliedFlags；
6. 主进程、Renderer、sandboxed process、SX Stub 中谁先消失或崩溃；
7. 第一个有效 Java/Native/Binder/linker 异常；
8. Guest ARM64 与 Host x86_64 frame；
9. libndk_translation 是否出现在实际崩溃证据；
10. libwebviewuc.so 是否出现在实际崩溃 frame；
11. SX_SERVICE_ROUTE 是否存在；
12. Renderer Service 最终 PID、UID、进程名；
13. 是否存在真实夸克 UID 的进程被错误启动；
14. Flags=63 与 Flags=47 是否改变崩溃时间、进程或 frame。

禁止把关键词出现当成因果关系。

# 九、结论等级

只允许：
- CONFIRMED_BY_RUNTIME_EVIDENCE；
- STRONGLY_SUPPORTED；
- HYPOTHESIS_ONLY；
- INSUFFICIENT_EVIDENCE。

只有进程、路由和崩溃证据闭环一致时，才能使用 CONFIRMED_BY_RUNTIME_EVIDENCE。
自动生成的 EVIDENCE_ONLY_ROOT_CAUSE_NOT_AUTO_CONFIRMED 不得被手工删除。

# 十、Git

本任务原则上不修改代码，不提交大型产物。
禁止提交：
- APK；
- logcat；
- tombstone；
- bugreport；
- artifacts/quark-automation 全量目录。

如仅新增一份小型 Markdown 分析报告，可提交：

git add docs/crash-analysis/<报告文件>
git commit -m "diagnose(sx): capture verified quark emulator evidence"
git push

提交前执行：

git diff --name-status
git diff --stat
git status --short --untracked-files=all

# 十一、最终回执

必须包含：
1. 当前分支；
2. 开始 HEAD；
3. Parser 结果；
4. 19 个 Fixture 结果；
5. Build 结果和 APK SHA-256；
6. 模拟器 serial、Android、ABI、Native Bridge；
7. Q0 原始结果；
8. Q1 三轮原始结果；
9. Q2 三轮原始结果；
10. 每轮 PID、UID、cmdline、starttime；
11. 每轮 requestedFlags/appliedFlags；
12. 每轮崩溃状态和存活时间；
13. 每轮 crash PID 与目标 PID 的关系；
14. Guest/Host frame；
15. Renderer/Sandboxed Service 的 PID、UID；
16. SX_SERVICE_ROUTE 原始关键行；
17. Flags 63/47 对比；
18. 根因结论等级；
19. 尚未确认的问题；
20. 证据包目录；
21. quark-diagnostic-summary.json 路径；
22. Git 状态；
23. 实际开始、结束与耗时。

本任务完成后停止，不实施修复。
```
