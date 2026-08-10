# vendor

## License Service Server SDK

`license_service_client-1.0.0rc3-py3-none-any.whl` is the fixed RD server
dependency from the License Service contract baseline.

SHA-256:

```text
30EC6E2FFA86627A7F1E6DD2E9AE7F2A07FE44161495AFD864D9090CBBF43A53
```

Install from the wheel; do not use editable installs from the adjacent
`license_service` repository and do not copy SDK source into RD.

第三方源码放置处。

## hongguo

```powershell
git clone --depth 1 https://github.com/zhangbaio/hongguo.git vendor/hongguo
```

- 将可用的 `config.json` 放到 `vendor/hongguo/config.json`（**不要提交**）。  
- 用法与签名环境见上游 README 与本仓 `docs/hongguo_reuse.md`。  
