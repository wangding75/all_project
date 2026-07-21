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
sign = MD5(card_key + device_id + SERVER_SECRET).upper()
```

## 环境变量说明

| 变量 | 说明 |
|------|------|
| SERVER_SECRET | 服务端核心密钥，用于 Token 签发和客户端签名校验 |
| CARDNET_WEBHOOK_SECRET | 三方卡网 Webhook 鉴权密钥 |
| ADMIN_API_KEY | 管理员接口密钥 |
| DATABASE_URL | SQLite 数据库文件路径 |
| PORT | 监听端口，默认 8000 |
