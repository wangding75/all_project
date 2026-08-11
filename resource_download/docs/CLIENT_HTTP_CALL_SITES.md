# CLIENT_HTTP_CALL_SITES

当前 RD Desktop Client 的 HTTP 调用边界如下。页面不散装实现密码学；所有
Device Proof 都在桌面 Python bridge 的统一 HTTP 层生成。

| 调用点 | 责任 | 传输边界 |
|---|---|---|
| `client/ui/app.js:apiFetch` | 登录、注册、me、搜索、详情、普通查询、Job 查询、files、health | 普通浏览器 `fetch`；桌面模式仍只处理未保护请求 |
| `client/ui/app.js:apiFetch` | 所有普通业务 endpoint（search/detail/discover/jobs/files/automation） | 发现受保护 path 后只调用 `pywebview.api.api_request`；没有 bridge 时 `DESKTOP_DEVICE_IDENTITY_REQUIRED` |
| `client/ui/app.js` redeem handler | `POST /v1/auth/redeem` | 只调用 `pywebview.api.redeem_license`；浏览器不发送未签名 redeem |
| `client/desktop/main.py:WindowApi.api_request` | 统一桌面 JSON 请求 | 固定 raw body；调用 `DesktopHttpClient`；protected 请求每次生成 fresh Proof |
| `client/desktop/main.py:WindowApi.redeem_license` | Activation | 每次尝试重新生成 Activation Proof，序列化一次并发送同一 bytes |
| `client/desktop/main.py:WindowApi.download_file` | `GET /v1/files/{file_id}` 本地文件交付 | 使用现有凭证并生成 fresh Device Proof |
| `client/desktop/http_client.py:is_protected_endpoint` | 普通业务 Guard 清单 | jobs/files/search/detail/discover/batch/image/people/automation 均签名；login/health/admin 保留原边界 |
| `client/desktop/device_identity.py` | identity 生命周期 | Windows 用户级 DPAPI；不在项目目录或浏览器存储中保存 private key |
| `client/desktop/device_proof.py` | LS-DEVICE-V3 | 调用 rc4 wheel 官方 helper 生成 activation/request proof、timestamp、nonce、raw body hash |

受保护请求的最终 URL target 直接使用 UI 传入的 path + query；最终已序列化的
body text 直接转为 bytes 传给 `urllib.request.Request`。HTTP retry 在签名循环
内执行，因此不会复用 timestamp/nonce/signature。
