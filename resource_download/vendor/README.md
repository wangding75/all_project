# vendor

## License Service Server SDK

`license_service_client-1.0.0rc2-py3-none-any.whl` is the fixed RD server
dependency from the License Service contract baseline.

SHA-256:

```text
21FB18CB36A040AEDDF4C946112346BD4F94FDA950BAAAA3A45277C05385E138
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
