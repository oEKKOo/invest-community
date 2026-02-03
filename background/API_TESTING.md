# 投研社区后端API测试指南

## 🔧 接口修复与完善总结

经过对比接口文档和代码实现，已完成以下修复：

### ✅ **路由映射修复**
- 用户相关接口统一到 `/api/users/` 路径下
- 评论创建接口合并到 `/api/posts/{id}/comments/`
- 添加了遗漏的logout接口

### ✅ **字段命名统一**
- `display_name` → `displayName`
- `avatar_url` → `avatar`
- `body` → `content`
- `tags_json` → `tags`
- `asset_ids` → `assetIds`
- `like_count` → `likes`
- `comment_count` → `comments`

### ✅ **新增接口**
- Dashboard概览接口
- 全局搜索接口
- 管理员帖子管理接口

## 🚀 Apifox测试配置

### 基础配置

**Base URL**: `http://127.0.0.1:8000`

**全局Headers**:
```json
{
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

## 📋 完整API接口清单

### 1. 认证接口 (Authentication)

#### 1.1 用户注册
- **URL**: `POST /api/auth/register/`
- **Body**:
```json
{
  "username": "testuser",
  "password": "testpass123",
  "password_confirm": "testpass123",
  "email": "test@example.com",
  "phone": "13888888888"
}
```
- **Response**:
```json
{
  "code": 0,
  "data": {
    "id": 1,
    "username": "testuser",
    "displayName": "testuser",
    "role": "USER",
    "access": "jwt-token",
    "refresh": "jwt-refresh-token"
  }
}
```

#### 1.2 用户登录
- **URL**: `POST /api/auth/login/`
- **Body**:
```json
{
  "username": "testuser",
  "password": "testpass123"
}
```

#### 1.3 刷新Token
- **URL**: `POST /api/auth/refresh/`
- **Body**:
```json
{
  "refresh": "jwt-refresh-token"
}
```

#### 1.4 用户登出
- **URL**: `POST /api/auth/logout/`
- **Headers**: `Authorization: Bearer {access_token}`

### 2. 用户管理 (Users)

#### 2.1 获取当前用户信息
- **URL**: `GET /api/users/me/`
- **Headers**: `Authorization: Bearer {access_token}`

#### 2.2 更新用户资料
- **URL**: `PATCH /api/users/me/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Body**:
```json
{
  "displayName": "New Name",
  "bio": "My bio",
  "avatar": "https://example.com/avatar.jpg"
}
```

#### 2.3 获取用户主页
- **URL**: `GET /api/users/{user_id}/`

#### 2.4 关注用户
- **URL**: `POST /api/users/{user_id}/follow/`
- **Headers**: `Authorization: Bearer {access_token}`

#### 2.5 取消关注
- **URL**: `DELETE /api/users/{user_id}/follow/`
- **Headers**: `Authorization: Bearer {access_token}`

#### 2.6 用户投资偏好
- **URL**: `GET/PUT /api/users/me/invest-profile/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Body (PUT)**:
```json
{
  "riskLevel": 2,
  "horizon": 3,
  "focusMarket": ["A", "US"],
  "preferredAssets": ["stock", "etf"]
}
```

### 3. 内容管理 (Posts)

#### 3.1 获取帖子列表
- **URL**: `GET /api/posts/`
- **Query参数**:
  - `status`: 状态过滤
  - `authorId`: 作者ID
  - `tag`: 标签过滤
  - `q`: 搜索关键词
  - `sort`: `new|hot`
  - `page`, `pageSize`: 分页

#### 3.2 创建帖子
- **URL**: `POST /api/posts/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Body**:
```json
{
  "title": "测试帖子",
  "content": "帖子内容",
  "tags": ["ETF", "策略"],
  "status": "DRAFT",
  "assetIds": [1, 2]
}
```

#### 3.3 获取帖子详情
- **URL**: `GET /api/posts/{post_id}/`

#### 3.4 更新帖子
- **URL**: `PATCH /api/posts/{post_id}/`
- **Headers**: `Authorization: Bearer {access_token}`

#### 3.5 删除帖子
- **URL**: `DELETE /api/posts/{post_id}/`
- **Headers**: `Authorization: Bearer {access_token}`

#### 3.6 收藏帖子
- **URL**: `POST /api/posts/{post_id}/favorite/`
- **Headers**: `Authorization: Bearer {access_token}`

#### 3.7 取消收藏
- **URL**: `DELETE /api/posts/{post_id}/favorite/`
- **Headers**: `Authorization: Bearer {access_token}`

### 4. 评论功能 (Comments)

#### 4.1 获取评论列表
- **URL**: `GET /api/posts/{post_id}/comments/`

#### 4.2 发表评论
- **URL**: `POST /api/posts/{post_id}/comments/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Body**:
```json
{
  "text": "评论内容",
  "parentId": null,
  "replyToUserId": null
}
```

#### 4.3 删除评论
- **URL**: `DELETE /api/comments/{comment_id}/`
- **Headers**: `Authorization: Bearer {access_token}`

### 5. 点赞功能 (Likes)

#### 5.1 点赞
- **URL**: `POST /api/likes/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Body**:
```json
{
  "targetType": "POST",
  "targetId": 1
}
```

#### 5.2 取消点赞
- **URL**: `DELETE /api/likes/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Body**:
```json
{
  "targetType": "POST",
  "targetId": 1
}
```

### 6. 资产管理 (Assets)

#### 6.1 搜索资产
- **URL**: `GET /api/assets/`
- **Query参数**:
  - `type`: `STOCK|FUND|ETF`
  - `q`: 搜索关键词

#### 6.2 资产详情
- **URL**: `GET /api/assets/{asset_id}/`

#### 6.3 资产相关帖子
- **URL**: `GET /api/assets/{asset_id}/posts/`

### 7. 投资组合 (Portfolios)

#### 7.1 获取组合列表
- **URL**: `GET /api/portfolios/`
- **Query参数**:
  - `userId`: 用户ID
  - `isPublic`: 是否公开
  - `sortBy`: `returnsYTD|new`

#### 7.2 获取热门组合
- **URL**: `GET /api/portfolios/top/`
- **Query参数**: `limit=5`

#### 7.3 创建组合
- **URL**: `POST /api/portfolios/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Body**:
```json
{
  "title": "我的组合",
  "description": "描述",
  "riskLevel": "Medium",
  "isPublic": true,
  "assets": [
    {
      "symbol": "QQQ",
      "name": "Invesco QQQ",
      "allocation": 40
    },
    {
      "symbol": "SPY",
      "name": "SPDR S&P 500",
      "allocation": 60
    }
  ]
}
```

### 8. 举报功能 (Reports)

#### 8.1 发起举报
- **URL**: `POST /api/reports/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Body**:
```json
{
  "targetType": "POST",
  "targetId": 1,
  "reason": "疑似广告信息"
}
```

### 9. 通知系统 (Notifications)

#### 9.1 获取通知列表
- **URL**: `GET /api/notifications/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Query参数**: `unreadOnly=true`

#### 9.2 标记通知已读
- **URL**: `POST /api/notifications/{notification_id}/read/`
- **Headers**: `Authorization: Bearer {access_token}`

### 10. Dashboard (数据概览)

#### 10.1 概览数据
- **URL**: `GET /api/dashboard/overview/`

### 11. 全局搜索

#### 11.1 搜索
- **URL**: `GET /api/search/`
- **Query参数**:
  - `q`: 搜索关键词
  - `type`: `all|post|asset|portfolio`

### 12. 管理员功能 (Admin)

#### 12.1 获取待审核帖子
- **URL**: `GET /api/admin/posts/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Query参数**: `status=PENDING_REVIEW`

#### 12.2 审核帖子
- **URL**: `PATCH /api/admin/posts/{post_id}/status/`
- **Headers**: `Authorization: Bearer {access_token}`
- **Body**:
```json
{
  "status": "PUBLISHED"
}
```

#### 12.3 管理统计
- **URL**: `GET /api/admin/stats/`
- **Headers**: `Authorization: Bearer {access_token}`

## 🧪 测试步骤建议

### Step 1: 基础认证测试
1. 先测试用户注册接口
2. 使用返回的token测试登录用户的接口
3. 测试token刷新功能

### Step 2: 内容管理测试
1. 创建测试帖子
2. 测试帖子列表获取
3. 测试点赞、收藏功能
4. 测试评论功能

### Step 3: 组合功能测试
1. 创建投资组合
2. 测试组合列表
3. 测试组合点赞

### Step 4: 管理功能测试
1. 使用管理员账号测试审核功能
2. 测试举报处理
3. 测试统计数据接口

## ❗ 注意事项

1. **认证Token**: 大部分接口需要在Header中添加 `Authorization: Bearer {access_token}`
2. **权限控制**: 管理员接口需要MODERATOR或ADMIN角色
3. **数据格式**: 所有POST/PATCH请求使用JSON格式
4. **错误码**: 返回格式统一为 `{"code": 0, "message": "ok", "data": ...}`
5. **分页**: 列表接口支持 `page` 和 `pageSize` 参数

## 🐛 已知问题

1. UserFavoritesView 需要从 content.views 移动到 accounts.views（已修复）
2. 字段命名需要与接口文档保持一致（已修复）
3. 部分管理员接口的URL路径需要调整（已修复）

现在所有接口都已按照接口文档规范实现，可以在Apifox中进行完整的接口测试！