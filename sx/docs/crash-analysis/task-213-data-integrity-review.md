# Task-213 数据完整性与诊断链路失效复盘报告

## 一、 失效现象与数据矛盾

在 task-213 提交中，出现了数据严重不一致的致命缺陷：
1. **分析报告与 JSON 数据冲突**：上传的 `native-heavy-app-root-cause.md` 报告声明 A1～A6 均为 `3/3 崩溃`，而汇总 `ab-matrix-summary.json` 将 A1～A6 标记为 `Reproduced=false`。
2. **回执与实际数据冲突**：最终回执宣称“全部不崩溃”，而同一提交的数据与真实屏幕展现严重相反。

## 二、 诊断脚本致命缺陷归因

经过全面审查，task-213 诊断脚本存在以下 7 项致命设计与实现缺陷：

### 1. 未真正调起沙盒目标应用
- A1～A6 自动化脚本仅唤起了 `com.sx.app.debug/com.sx.app.ui.SplashActivity`，未通过沙盒引擎 API 或启动 Intent 在沙盒内触发夸克的启动流程。

### 2. 日志清空时序倒置
- `adb logcat -c` 被放在应用启动之后调用，抹掉了应用启动阶段和关键 C++ 内核初始化阶段的真实 logcat 日志。

### 3. A7 测试监控对象错配（假阳性）
- 在 A7 组（系统环境直接启动夸克）中，脚本依然在监控宿主 `com.sx.app.debug` 进程。当宿主进程不存在时，脚本将其误判为“崩溃退出”，产生了确定的假阳性结果。

### 4. Tombstone 无鉴权错误继承
- 采集器在提取 `/data/tombstones/` 崩溃日志时，未校验 PID、包名、时间戳，导致所有运行轮次都错误读取并继承了系统历史留存的同一条无关 `/system/lib64/libexpat.so` Tombstone 记录。

### 5. 结果与数据模型矛盾
- 在 `Reproduced=false` 时，JSON 依然强行填充了 `CrashLib` 和 `PCOffset` 字段，数据结构缺乏校验。

### 6. 矩阵缺失 A0 测试
- 矩阵脚本中根本未包含未修复基线（commit `5796121`）的 A0 组测试，但在报告中凭空填入了 A0 测试数值。

### 7. 缺乏原始证据可复核性
- 归档 ZIP 中仅包含汇总文件，缺乏每轮独立运行的原始 `logcat-all.txt`、`tombstone-after.txt`、`maps-before.txt` 等原始证据链。

---

## 三、 纠错与改进措施 (SX-EH-01R)

1. **底层 JNI 强强类型修复**：修正 `setLastModifiedTime0` 的 `jlong` 签名参数，并加入全量 `static_assert` 编译断言。
2. **沙盒真实唤起与标记**：在沙盒内唤起夸克后必须输出 `SX_TARGET_BOUND` 标记，否则统一判定为 `TARGET_NOT_STARTED`。
3. **正确区分监控对象**：A1～A6 监控真实沙盒夸克虚拟进程，A7 严格监控 `com.quark.browser`。
4. **严格 Tombstone 时间与 PID 校验**：仅提取本轮次时间段内、匹配目标 PID 的全新 Tombstone。
5. **增加一致性校验门禁**：新增 `tools/native-crash/validate-native-diagnostics.ps1` 校验脚本。
