# 商业产品 V1.0 发布门禁检查表 (Release Gate Checklist)

> **关联**: [`COMMERCIAL_V1_PLAN.md`](./COMMERCIAL_V1_PLAN.md) §4 (阶段 E0)  
> **原则**: 履约优先于功能堆叠。在发布任何二进制发行包（`ResourceDownloader.exe`）或提交生产部署前，必须全量通过本门禁表。

---

## 一、 必勾自动化测试门禁

- [ ] **1. Unit & Integration Pytest 全绿**
  ```powershell
  $env:PYTHONPATH="server"
  python -m pytest server/tests -q
  ```
  - **验收**: 所有单元测试 (包含认证 `test_auth`, VIP/卡密 `test_auth_d2`, 配额 `test_quota`, 多租户隔离 `test_isolation_e1`, 签名池 `test_sign_pool` 及错误映射测试) `41+ passed` 零 FAIL。

- [ ] **2. 冒烟服务探活 (Smoke Health)**
  ```powershell
  python scripts/smoke_health.py
  ```
  - **验收**: 返回 HTTP `200 OK`，`status="ok"` 且平台列表包含 `hongguo` 与 `fanqie`。

- [ ] **3. 一键冒烟自动化**
  ```powershell
  powershell scripts/ci_smoke.ps1
  ```
  - **验收**: 汇总返回退出码 `0`，包含健康探针与无样例自动跳过/有样例跑通。

---

## 二、 履约与 E2E 双平台门禁

- [ ] **4. 番茄平台 E2E 验证**
  ```powershell
  python scripts/e2e_fanqie.py --id "<BOOK_ID_或_URL>" --range 1-2
  ```
  - **验收**: 任务转为 `success`，在 `data/e2e_downloads/` 下正确落盘文本产物。

- [ ] **5. 红果平台 E2E 验证**
  ```powershell
  python scripts/e2e_hongguo.py --id "<SERIES_ID>" --range 1-1
  ```
  - **验收**: 任务转为 `success`，在 `data/e2e_downloads/` 下正确落盘可播放的 `.mp4` 视频产物。

> *注：如因特定环境因素（如缺真机模拟器或特定 Vendor 账号）无法跑通真机，必须在发版记录中书面记录签字豁免原因。*

---

## 三、 生产安全与诚实错误校验

- [ ] **6. 生产安全默认设置检测**
  - 在生产环境开启 `AUTH_MODE=dual` 或 `jwt_only` 时，**禁止** 使用默认开发密钥 `dev-key-change-me` 与 `change-me-jwt-secret`。
  - 监听地址避免裸奔绑定开放网络。

- [ ] **7. 诚实错误文案（零假成功）**
  - 当签名池节点全挂或无可用节点时，确认识别并抛出标准的 **HTTP 503** 错误:
    `{"detail": "签名节点繁忙或不可用，请稍后重试"}`
  - 任务失败时，UI 与 API 返回的 `error` 字段必须包含可归类可读信息，无静默假成功现象。

---

## 四、 版本号与发行物一致性

- [ ] **8. 全链路版本号对齐**
  - 服务端 `server/app/__init__.py` 的 `__version__`
  - OpenAPI `/v1/version` 返回值
  - 桌面端 UI 标题栏版本号

- [ ] **9. 打包可执行文件校验**
  ```powershell
  python scripts/build_exe.py
  ```
  - 校验 `dist/ResourceDownloader.exe` 在干净无 Python 环境的干净虚拟机/机器上能够正常双击启动并拉起 UI 界面。
