下面按“**优先级 + 技术落地方式**”给你整理，尽量直接对应下一步可加到代码里的内容。

**P0 核心补齐**

- 现状：前端请求路径和后端实际路由不一致，导致关注流不可用，见 [users.ts:9](d:/invest/frontend/src/api/users.ts:9) 、[urls.py:16](d:/invest/background/accounts/urls.py:16)。
- 后端做法：把 `following_feed`、`following_portfolios_feed` 从 `auth` 路由迁到统一 `/api/feed/...`，或前端改请求路径，二选一但要统一。
- 前端做法：Dashboard 的 `follow`、`followPortfolios` Tab 加载成功后，要区分帖子卡片和组合卡片，不要混成一种 UI，见 [Dashboard.vue](d:/invest/frontend/src/views/Dashboard.vue)。
- 补充接口：建议加 `GET /api/feed/following/recommendations/`，返回“你可能感兴趣的用户/组合”。

2. 个人资料编辑闭环
- 现状：编辑资料只是本地改状态，没有真正持久化，见 [Profile.vue:810](d:/invest/frontend/src/views/Profile.vue:810)。
- 后端做法：直接复用现有 `PATCH /api/users/me/`，确保支持 `displayName/avatar/bio/phone` 字段，见 [views.py:94](d:/invest/background/accounts/views.py:94)。
- 前端做法：新增 `updateCurrentUser()` API，编辑成功后再调用 `fetchCurrentUser()` 刷新本地用户态。
- 顺手修复：`getCurrentUser()` 现在写成了 `POST`，应改成 `GET`，见 [auth.ts:38](d:/invest/frontend/src/api/auth.ts:38)。

3. 他人主页完整化
- 现状：他人主页帖子列表仍按当前登录用户过滤，见 [Profile.vue:793](d:/invest/frontend/src/views/Profile.vue:793)。
- 后端做法：继续使用 `GET /api/posts/?authorId=xxx`，但对未发布内容要严格限制仅作者本人和管理员可见，现有逻辑已接近可用，见 [views.py](d:/invest/background/content/views.py)。
- 前端做法：主页根据路由 `userId` 切换 `displayUser` 后，重新拉取该用户公开帖子、公开组合、关注状态。
- 建议补页签：`帖子`、`组合`、`收藏`、`互动记录`。其中“收藏/互动记录”只对本人可见。
4. 评论体系升级为完整讨论链
- 目标：让帖子下的讨论从“平铺列表”升级为**楼中楼 + 分页加载 + 可编辑/删除 + 点赞/举报 + 通知联动**的一整套闭环。
- 现状：
  - 模型侧已支持 `parent` / `reply_to_user` 等字段，见 [serializers.py:159](d:/invest/background/content/serializers.py:159)，接口文档已有基础 `GET/POST /api/posts/{id}/comments/`。
  - 前端 `PostDetail.vue` 仅按时间平铺展示评论，没有真正的“回复某人 + 展开更多回复”体验。
- 后端接口与权限（在 `content/views.py` / `urls.py` 中补齐）：
  - 保持现有：`GET /api/posts/{post_id}/comments/` 返回**一级评论 + 少量子回复预览**，按 `created_at` 倒序，支持 `page/pageSize`。
  - 新增：`GET /api/comments/{id}/replies/`
    - 用途：单独分页拉取某条评论下的二级/多级回复，避免帖子详情一次性拉太深。
    - 参数：`page`、`pageSize`，只返回 `parent_id = {id}` 的评论，按时间正序。
  - 新增/规范：`PATCH /api/comments/{id}/`
    - 只允许评论作者且评论处于“正常”状态；可选限制“创建后 10 分钟内可编辑”。
    - 入参只允许修改 `body`，服务端返回更新后的完整评论结构（含 `replies` 计数）。
  - 删除沿用：`DELETE /api/comments/{id}/`
    - 作者或管理员可调用；实现为软删除（status 标记），子回复可保留但前端标记“上级评论已删除”。
  - 点赞接口：
    - 继续使用通用 `POST /api/likes/` / `DELETE /api/likes/`，`targetType="COMMENT"`。
    - 可在路由层增加语义化别名 `POST /api/comments/{id}/like/`，内部转发到 likes 视图，方便前端调用。
- 前端改动（`PostDetail.vue` 为主）：
  - 结构：
    - 顶层使用“评论列表组件 + 单条评论组件”的拆分，便于复用和递归展示二级评论。
    - 单条评论展示：头像、昵称、时间、内容、`replyToUserName`（如“回复 @xxx”）、点赞数、回复数、操作入口（回复/编辑/删除/举报）。
  - 交互：
    - 一级评论下方提供“回复”按钮，点击后出现内联回复输入框，提交走 `POST /api/posts/{post_id}/comments/`，带上 `parentId`、`replyToUserId`。
    - 当某条评论 `replyCount` 大于预览数量时，展示“展开更多回复 (N)”按钮，点击调用 `GET /api/comments/{id}/replies/` 分页追加。
    - 支持当前用户对自己评论的“编辑/删除”操作，编辑成功后在 UI 中标记“已编辑”。
    - 点赞/取消点赞直接调用评论点赞接口，局部刷新这条评论的 `likeCount` 与 `isLiked`。
  - API 封装：
    - 在 `frontend/src/api/posts.ts` 或单独 `comments.ts` 中新增：`fetchPostComments`、`fetchCommentReplies`、`createComment`、`updateComment`、`deleteComment`、`likeComment`、`unlikeComment`、`reportComment` 等函数。
- 通知联动（`notifications/events.py`）：
  - 评论相关事件：
    - 用户在你的帖子下发表评论 → 发送 `COMMENT` 通知给帖子作者。
    - 用户回复你的评论 → 发送 `COMMENT_REPLY` 通知给被回复用户。
  - 点赞相关事件：
    - 用户点赞你的评论（`targetType=COMMENT`）→ 发送 `LIKE` 通知，文案中指出“点赞了你的评论”。
  - 评论删除/屏蔽时可选发送系统通知，说明被处理原因，方便在论文中描述“社区治理反馈机制”。

5. 举报闭环
- 目标：让“举报”从单一接口变成完整闭环——**用户侧有统一入口 + 管理侧有列表/详情/处置动作 + 与内容状态、用户治理、通知打通**。
- 现状：`reports` 模块已能创建举报记录，但：
  - 前端没有明显的举报入口，用户很难实际使用。
  - 管理员端只有简单统计卡片，没有“举报处理中心”，见 [reports/views.py](d:/invest/background/reports/views.py)、[AdminPanel.vue](d:/invest/frontend/src/views/AdminPanel.vue)。
- 后端模型与字段（`reports/models.py`）：
  - 在现有 `Report` 模型基础上补充：
    - `report_type_detail`：细化举报类型，如“广告/辱骂/虚假收益/诱导荐股/违规私信/违法违规”等，枚举 + 文本描述皆可。
    - `evidence_json`：JSON，存放截图 URL 列表、补充说明等证据字段。
    - `priority`：整型或枚举，默认 0，可按“多次被举报/涉及资金安全”等情况提升优先级，用于后台排序。
    - `handled_by`、`handled_at`、`handle_result`：记录哪位管理员在何时做了怎样的处理，方便“留痕”和审计。
- 后端接口层改动：
  - 用户侧（保持接口文档兼容）：
    - `POST /api/reports/`：请求体中增加 `reportTypeDetail`、`evidence`（前端可传结构化 JSON），服务端写入 `report_type_detail`、`evidence_json`。
    - `GET /api/users/me/reports/`：在列表中返回处理状态、结果、被举报对象的简要信息（帖子标题/评论内容片段/用户名），便于用户查看进展。
  - 管理员侧：
    - `GET /api/admin/reports/`：
      - 支持按 `status`（PENDING/RESOLVED）、`targetType`、`priority`、`created_at` 过滤和排序。
      - 列表项包含举报次数聚合信息（同一帖子/评论被多次举报可合并统计）。
    - `GET /api/admin/reports/{id}/`：返回单条举报详情，包括证据、历史处理记录、关联帖子/评论/用户的基础信息。
    - `PATCH /api/admin/reports/{id}/`：
      - 入参：`status`（如 PENDING/VALID/INVALID）、`handleResult` 文本说明，可选联动动作字段（如 `takeDownContent=true`、`hideComment=true`、`muteUserDays=7`）。
      - 处理逻辑：根据联动动作更新 `content` / `comment` / `user` 表状态（下架帖子、隐藏评论、禁言用户），并记录到治理/审核日志表。
- 前端用户侧改动：
  - 入口布局（对应 `PostDetail.vue`、评论组件、用户主页、`PortfolioDetail.vue` 等）：
    - 帖子卡片/详情：在操作区增加“举报”按钮。
    - 评论项：在更多操作中增加“举报评论”。
    - 用户主页：在用户信息卡中增加“举报用户”入口（针对严重骚扰/违规头像昵称等）。
    - 组合详情：在组合卡或详情页增加“举报组合”（虚假收益、违规荐股）。
  - 举报弹窗表单：
    - 字段：举报对象类型/标题只读展示、`reportType`（下拉）、`reportTypeDetail`（可选补充）、`description`、图片/链接证据上传（存为 `evidence_json`）。
    - 提交成功后提示“已提交审核”，并可引导到“我的举报记录”（复用 `GET /api/users/me/reports/`）。
- 前端管理侧改动（“举报处理中心”）：
  - 在 `AdminPanel.vue` 新增“举报处理”页签或独立路由组件：
    - 列表：支持按状态、目标类型、优先级筛选；表格列包含举报对象摘要、举报类型、优先级、次数、最新时间。
    - 详情：点击一条举报进入详情侧边弹窗或独立页面，展示举报理由、证据图片、原帖/评论/用户信息，并提供处理按钮。
    - 处理动作：在前端提供快捷按钮组合，如“判定有效并下架帖子”“判定有效并隐藏评论+禁言 7 天”“判定无效”，对应调用 `PATCH /api/admin/reports/{id}/`。
- 通知与用户反馈：
  - 当管理员处理举报时：
    - 向举报人发送 `REVIEW_RESULT` 或 `REPORT_RESULT` 通知，说明“举报是否成立 + 采取了什么措施”。
    - 向被处理用户发送系统通知，说明被下架/禁言的原因与时长（可附带申诉引导）。
  - 这些都可通过 `notifications/events.py` 的事件封装，方便在论文中描述“举报处理的闭环和可追溯性”。

**P1 社区治理增强**
6. 用户治理后台
- 现状：模型已有 `MUTED/BANNED`，但没有治理界面和操作接口，见 [models.py](d:/invest/background/accounts/models.py)。
- 建议新增模型：
- `UserModerationLog`：`user_id`、`action`、`reason`、`expire_at`、`operator_id`、`created_at`。
- 建议新增接口：
- `PATCH /api/admin/users/{id}/status/`
- `POST /api/admin/users/{id}/mute/`
- `POST /api/admin/users/{id}/ban/`
- `POST /api/admin/users/{id}/unmute/`
- `POST /api/admin/users/{id}/unban/`
- 技术要点：
- `MUTED` 只限制发帖、评论、私信。
- `BANNED` 限制登录与社区访问。
- 所有动作写入日志，便于论文里写“社区治理留痕”。

7. 告警中心从静态改真实
- 现状：管理员告警区是写死的占位内容，见 [AdminPanel.vue:194](d:/invest/frontend/src/views/AdminPanel.vue:194)。
- 后端做法：复用已有 `Alert` 模型，见 [models.py](d:/invest/background/reports/models.py)。
- 告警来源建议：
- 高频举报自动聚合。
- 某用户短时间大量发帖/评论。
- 帖子命中敏感词或“保本收益”“带单”关键词。
- 同一 IP/账号短时异常操作。
- 前端做法：
- 告警列表页、告警详情弹窗、处理状态筛选、处理备注、跳转到原内容。

8. 内容审核细化
- 现状：只有 `PENDING_REVIEW/PUBLISHED/REJECTED/TAKEN_DOWN`，基础够用但不细。
- 建议新增：
- 审核标签：`涉嫌广告`、`高风险荐股`、`收益截图存疑`。
- 内容操作日志表：记录谁在何时做了通过/驳回/下架。
- 风险词库配置表：管理员可维护敏感词。
- 技术实现：
- 发帖时先做关键词命中，命中则自动进入待审。
- 管理员审核时填写原因模板，前端作者可见。

**P1 互动增强**
9. 通知系统实时化
- 现状：通知是拉取式，不算真正实时互动，见 [notifications/views.py](d:/invest/background/notifications/views.py)。
- 建议方案：
- 先上通知 SSE，比 WebSocket 简单，和行情 SSE 保持一致风格。
- 接口：`GET /api/notifications/stream/`
- 触发源：点赞、评论、回复、关注、审核结果、举报处理结果、私信。
- 前端做法：
- 在主布局里长连接，收到通知后刷新未读数和抽屉列表，见 [MainLayout.vue](d:/invest/frontend/src/components/layout/MainLayout.vue)。

10. 私信/会话系统
- 这项很适合“实时互动”答辩口径。
- 建议新增模型：
- `Conversation`
- `ConversationParticipant`
- `Message`
- `MessageReadLog`
- 最小接口集：
- `GET /api/messages/conversations/`
- `POST /api/messages/conversations/`
- `GET /api/messages/conversations/{id}/messages/`
- `POST /api/messages/conversations/{id}/messages/`
- `POST /api/messages/{id}/read/`
- 权限：
- 仅会话参与者可读写。
- 被禁言用户不能发私信。
- 实时方式：
- 有精力就 WebSocket。
- 时间紧就消息发送走 HTTP，未读提醒走 SSE。

11. 组合讨论区
- 现状：组合能展示但不能深入交流，见 [PortfolioDetail.vue](d:/invest/frontend/src/views/PortfolioDetail.vue)。
- 建议新增：
- 组合评论表，结构可复用帖子评论模型。
- 组合收藏/订阅。
- 组合更新日志：记录调仓说明、收益复盘、策略变更。
- 接口建议：
- `GET /api/portfolios/{id}/comments/`
- `POST /api/portfolios/{id}/comments/`
- `POST /api/portfolios/{id}/subscribe/`
- `GET /api/portfolios/{id}/updates/`

**P2 体验与推荐**
12. 搜索与推荐从静态变真实
- 现状：热门搜索和推荐入口是静态数据，见 [Search.vue:196](d:/invest/frontend/src/views/Search.vue:196) 和 [Dashboard.vue:742](d:/invest/frontend/src/views/Dashboard.vue:742)。
- 建议新增表：
- `SearchKeywordStat`
- `UserBehaviorEvent`
- 推荐逻辑第一版：
- 基于关注关系、浏览帖子、点赞资产、收藏帖子、查看组合。
- 不必上复杂算法，规则推荐即可。
- 推荐接口：
- `GET /api/recommend/posts/`
- `GET /api/recommend/portfolios/`
- `GET /api/recommend/users/`

13. 用户行为埋点
- 用于推荐、热榜、论文中的“社区活跃度分析”。
- 建议记录：
- 浏览帖子
- 点赞
- 收藏
- 评论
- 关注
- 查看资产
- 查看组合
- 表结构：
- `UserBehaviorEvent(user_id, event_type, target_type, target_id, extra_json, created_at)`

14. 反垃圾与限流
- 这是社区系统常见加分项。
- 后端建议：
- 对发帖、评论、私信、举报做频率限制。
- 短时间重复内容检测。
- 敏感词和外链白名单。
- 图片/链接数量限制。
- 可直接放在 DRF 权限或自定义中间件里。

**推荐开发顺序**
1. 修路由和资料编辑闭环。
2. 修他人主页和关注流。
3. 做评论回复、举报入口、管理员举报处理页。
4. 做用户禁言/封禁后台。
5. 做通知 SSE。
6. 做组合评论和组合订阅。
7. 再做私信、推荐、行为埋点。

如果你要，我下一步可以继续把这些补充点整理成一份“**数据库表设计 + REST API 清单 + 前端页面清单**”的实现文档版本。