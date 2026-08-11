# T22 功能阻塞修复报告

## 结论

**PASS**。本次仅修复 FUNC-001/002/003/004/006；UI-001/UI-002 不在范围内，FUNC-005 按“不属于缺陷”保留原有 License cache 语义。

验收模拟器固定使用 **RD测试**：`127.0.0.1:7555`。未使用 SX测试模拟器 `127.0.0.1:16384`。

## 修复摘要

- FUNC-001：Desktop 默认 `AUTH_MODE=dual`，支持本地 API Key/JWT 登录链路；非法模式继续启动失败。
- FUNC-002：番茄官方搜索使用真实关键词，解析官方 `book_data`，结果显示真实书名；红果搜索返回稳定的平台状态，不再把上游不可用伪装成空结果。
- FUNC-003：红果 Frida 预检固定 Python `frida==16.7.19`、`frida-tools==14.10.4`，记录目标版本、架构、ADB 设备和 bridge 结果；不兼容时返回 `RUNTIME_INCOMPATIBLE`。
- FUNC-004：Fanqie cookie 仅以内存运行时标记进入 Job，任务 JSON/日志不保存明文；重启后明确返回 `COOKIE_REQUIRED/REAUTH_REQUIRED`。
- FUNC-006：客户端提交期间禁用按钮；服务端以 `Idempotency-Key` 绑定用户、平台和请求体，支持重放、冲突 `409`、并发单 Job、不同 key 新 Job。
- `tools/setup/push_frida.ps1` 和安装说明已改为 RD测试默认端口；未触碰 SX 目录。

## RD 实机验收证据

### Frida 预检

RD `127.0.0.1:7555`：Python Frida `16.7.19`、frida-tools `14.10.4`、目标 server `16.7.19`、目标架构 `x86_64`、bridge `PASS`。

### 番茄

- 官方搜索关键词：`特工易冷`。
- HTTP 200；UI 显示 20 条番茄结果，首条真实书名为“这个大叔不正经（原名特工易冷）”。
- 进入详情“特工易冷”，显示 373 章，并可看到章节列表。

### 红果

- 搜索关键词：`皇后`。
- UI 显示红果 20 条结果；详情“抱歉本宫是皇后”显示 70 集。
- 两个并发 Job 隔离完成，输出文件非空：`抱歉本宫是皇后_第001集.mp4`（13,325,092 bytes）和 `哎呀！皇后娘娘来打工_第001集.mp4`（9,354,743 bytes）。
- Fanqie cookie Job 成功；模拟重启后明确失败为 `COOKIE_REQUIRED`，任务持久化文件未发现 cookie 明文。

## 自动化与构建

- `python -m pytest server/tests client/tests -q`：**151 passed**，13 warnings。
- `python scripts/quality_gate.py`：**PASS**（Python compile、版本检查、WORKERS=1、依赖检查、全量测试均通过；141 collected，140 passed，1 skipped）。
- `python scripts/build_exe.py`：**PASS**，生成 `dist/ResourceDownloader.exe`（约 28.90 MB）。
- `python scripts/smoke_health.py`：**OK**，health/platform readiness 通过，设备为 RD `127.0.0.1:7555`。
- License E2E：**PASS**。覆盖激活、证明/绑定、重放、body/query 绑定、API Key/VIP/CardKey bypass、租户隔离、缓存命中、服务下线/恢复、后台 revoked/expired/device revoked、quota 和 legacy re-auth。
- 额外检查：`node --check client/ui/app.js`、`python -m compileall -q server client`、`git diff --check` 均通过。

## 保护目录检查

- `D:\github\license_service` 未修改，HEAD 保持 `046dc8e2f621bfa434e8cc4ba88920b431207487`。
- `D:\github\all_project\sx` 未修改；本次变更仅位于 `resource_download`。
