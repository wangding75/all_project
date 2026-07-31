# 闪现授权服务端

Python FastAPI + SQLite 实现的商业授权服务。

## 快速启动

```powershell
cd server
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # 编辑 .env，修改所有 CHANGE_ME 字段
uvicorn main:app --reload --port 8000
```

## API 文档

启动后访问：http://localhost:8000/docs

## 接口一览

| 接口 | 调用方 | 说明 |
|------|--------|------|
| POST /api/license/activate | 客户端 Android | 激活卡密，绑定设备，返回 Token |
| GET  /api/license/verify   | 客户端 Android | 校验 Token 是否有效 |
| POST /api/license/unbind   | 管理员 | 解绑设备，允许换机重新激活 |
| POST /api/cards/deliver    | 三方卡网 Webhook | 用户付款后获取卡密（自动发货）|
| POST /api/cards/generate   | 管理员 | 手动批量生成卡密 |
| GET  /api/cards/status/:key | 管理员 | 查询卡密状态 |
| GET  /health               | 任意 | 健康检查 |

## 三实体流程

```
三方卡网 ──(付款后 Webhook)──► 本服务端 /api/cards/deliver（取卡密）
                               ─────────── 卡密返回给卡网 ──────────► 卡网发给用户

客户端 ──(用户输入卡密)──► 本服务端 /api/license/activate（激活绑定）
                           ──── Token + expire_at 返回 ──────────► 客户端本地存储

客户端 ──(App 启动后台)──► 本服务端 /api/license/verify（刷新有效期）
```

## 签名规则（客户端调激活接口时）

```
sign = MD5(card_key + device_id + CLIENT_SIGN_SECRET).upper()
```

`CLIENT_SIGN_SECRET` 只保护激活请求。授权 Token 使用服务端 RSA 私钥签名，
Android 客户端仅内置对应公钥，因此客户端不能自行伪造 Token。

## 环境变量说明

| 变量 | 说明 |
|------|------|
| CLIENT_SIGN_SECRET | 客户端激活请求密钥；需与 Android `license.app_secret` 一致 |
| TOKEN_PRIVATE_KEY_PEM | RSA PKCS#8 私钥，仅保存在服务端 |
| CARDNET_WEBHOOK_SECRET | 三方卡网 Webhook 鉴权密钥 |
| ADMIN_API_KEY | 管理员接口密钥 |
| DATABASE_URL | SQLite 数据库文件路径 |
| PORT | 监听端口，默认 8000 |
| ALLOW_LEGACY_TOKEN_MIGRATION | 是否临时接受旧 HMAC Token，生产默认关闭 |
| LEGACY_TOKEN_SECRET | 仅用于旧 Token 迁移，不得与客户端密钥相同 |

生产环境还需把 RSA 公钥 DER 的 Base64 值写入 Android
`local.properties` 的 `license.token_public_key`。管理员状态查询优先通过
`X-Admin-Api-Key` 请求头传递密钥，旧查询参数暂时保留兼容。
可复制仓库根目录的 `local.properties.example` 作为配置模板；Release
服务地址必须使用 HTTPS，HTTP 仅由 Debug 构建允许。
