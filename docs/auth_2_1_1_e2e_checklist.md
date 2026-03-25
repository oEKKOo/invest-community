# 2.1.1 注册与认证联调清单

## 环境准备

- 后端配置 `.env`：
  - `WECHAT_APP_ID`、`WECHAT_APP_SECRET`、`WECHAT_REDIRECT_URI`
  - `WEIBO_CLIENT_ID`、`WEIBO_CLIENT_SECRET`、`WEIBO_REDIRECT_URI`
- 执行迁移：
  - `python manage.py migrate`
- 前端配置 `VITE_API_BASE_URL` 指向后端 `/api`。

### 邮件/短信验证码三方配置

- 邮件（QQ SMTP）：
  - `EMAIL_HOST=smtp.qq.com`
  - `EMAIL_PORT=465`
  - `EMAIL_USE_SSL=true`
  - `EMAIL_HOST_USER=你的QQ邮箱`
  - `EMAIL_HOST_PASSWORD=QQ邮箱SMTP授权码`
  - `EMAIL_FROM=InvestHub <你的QQ邮箱>`
- 短信：
  - `SMS_PROVIDER=TWILIO` 并配置 `TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_FROM_PHONE`
  - 或 `SMS_PROVIDER=HTTP` 并配置 `SMS_HTTP_URL/SMS_HTTP_TOKEN`
  - 开发联调可用 `SMS_PROVIDER=MOCK`（不真实发送）

## 用例 1：邮箱注册（基础认证）

1. 调 `POST /api/auth/verification/send/`，`channel=EMAIL,purpose=REGISTER`
2. 调 `POST /api/auth/register/email/`
3. 断言返回 `access/refresh/user`，且 `user.emailVerified=true`，`identityLevel=BASIC`

## 用例 2：手机号注册（基础认证）

1. 调 `POST /api/auth/verification/send/`，`channel=PHONE,purpose=REGISTER`
2. 调 `POST /api/auth/register/phone/`
3. 断言 `user.phoneVerified=true`，`identityLevel=BASIC`

## 用例 3：密码登录（多标识）

- 分别使用 `username/email/phone` 调 `POST /api/auth/login/password/`
- 断言均可登录并签发 JWT

## 用例 4：短信验证码登录

1. 调 `POST /api/auth/verification/send/`，`purpose=LOGIN`
2. 调 `POST /api/auth/login/sms/`
3. 断言登录成功

## 用例 5：微信/微博 OAuth 注册登录

1. 调 `GET /api/auth/oauth/{provider}/start/`
2. 浏览器完成授权，拿到 `code,state`
3. 调 `GET /api/auth/oauth/{provider}/callback/?code=...&state=...`
4. 断言首次创建用户，二次登录复用绑定账号

## 用例 6：实名认证

1. 登录用户调 `POST /api/auth/kyc/real-name/submit/`
2. 管理员调审核接口通过
3. 断言用户 `realNameStatus=APPROVED`，`identityLevel>=REAL_NAME`

## 用例 7：风险评估 + 专业认证

1. 调 `GET /api/auth/risk/questionnaire/` 获取问卷
2. 调 `POST /api/auth/risk/submit/` 提交
3. 调 `POST /api/auth/kyc/professional/submit/` 提交专业认证
4. 管理员审核通过
5. 断言用户 `professionalStatus=APPROVED`、`identityLevel=PROFESSIONAL`、`vBadge=true`

## 回归点

- `/api/auth/refresh/` 响应结构应为 `{code:0,data:{access}}`
- 前端 401 自动刷新成功后可重放原请求
- 路由守卫与认证中心页面可正常访问
