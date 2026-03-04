这个项目当前已经不是“从 0 到 1”的阶段了，而是一个很典型的“核心能力已成型，但有不少预埋能力还没产品化”的阶段。

**现状判断**
从代码结构看，它已经具备了 4 条主线能力：

- 投资社区：帖子、评论、点赞、收藏、举报、审核都已经有完整模型和接口。
- 投资组合：公开组合、组合资产、组合详情、点赞、排行榜都已打通。
- 行情数据：`A 股(Tushare) + 美股/港股(Finnhub)` 双数据源，支持最新价、K 线、分时、SSE 推送、数据任务监控。
- 个人持仓：有持仓录入、每日快照、浮盈亏/日收益/收益曲线，已经从“纯展示”进入“轻投顾工具”阶段。

关键文件能说明这一点：

- 关注关系和投资偏好模型已经存在：[D:\invest\background\accounts\models.py:81](D:\invest\background\accounts\models.py:81) [D:\invest\background\accounts\models.py:113](D:\invest\background\accounts\models.py:113)
- 全局搜索接口已经存在：[D:\invest\background\content\views.py:698](D:\invest\background\content\views.py:698)
- 通知 API 已存在：[D:\invest\background\notifications\views.py:12](D:\invest\background\notifications\views.py:12)
- 持仓收益计算已成型：[D:\invest\background\portfolios\views.py:250](D:\invest\background\portfolios\views.py:250)
- 行情任务监控与触发已成型：[D:\invest\background\market_data\views.py:506](D:\invest\background\market_data\views.py:506) [D:\invest\background\market_data\views.py:545](D:\invest\background\market_data\views.py:545)

所以，接下来最值得做的，不是盲目加新模块，而是优先把“已经有后端能力、但前端或业务流程没接完”的部分补齐。这类扩展性价比最高。

**最值得优先扩展的功能**
建议按下面顺序做。

1. 通知中心
这是最应该先补的。

原因很直接：
- 通知模型和 API 已经有了：[D:\invest\background\notifications\models.py:8](D:\invest\background\notifications\models.py:8) [D:\invest\background\notifications\views.py:12](D:\invest\background\notifications\views.py:12)
- 但前端通知按钮还是空壳：[D:\invest\frontend\src\components\layout\MainLayout.vue:185](D:\invest\frontend\src\components\layout\MainLayout.vue:185)
- 代码里没有发现任何 `Notification.objects.create(...)`，说明“通知生产”还没接上

可扩展内容：
- 点赞通知
- 评论通知
- 关注通知
- 帖子审核结果通知
- 系统公告通知
- 未读数、批量已读、通知抽屉/通知页

这会立刻把社区互动体验补完整，而且改动风险低。

2. 关注流 / 社交 Feed
这是第二优先级。

因为：
- 后端已有关注关系和关注/取关接口：[D:\invest\background\accounts\views.py:153](D:\invest\background\accounts\views.py:153)
- 但前端 Dashboard 明确写了“关注 feed 后端暂无实现，fallback 为 new”：[D:\invest\frontend\src\views\Dashboard.vue:584](D:\invest\frontend\src\views\Dashboard.vue:584)

可扩展内容：
- “关注的人发了什么”时间流
- 关注用户的公开组合更新流
- 用户主页（查看他人主页、关注/取消关注）
- 粉丝/关注列表页

这会把项目从“内容站”升级成“投资社交网络”。

3. 全局搜索落地
这也是低成本高收益项。

因为：
- 后端搜索接口已存在：[D:\invest\background\content\views.py:698](D:\invest\background\content\views.py:698)
- 顶部搜索框已有 UI，但没接行为：[D:\invest\frontend\src\components\layout\MainLayout.vue:84](D:\invest\frontend\src\components\layout\MainLayout.vue:84)

可扩展内容：
- 搜帖子 / 资产 / 组合
- 搜索建议（输入联想）
- 热门搜索
- 搜索结果页（按类型切换）

这能明显提升信息获取效率，而且复用现有接口。

4. 投资档案（用户偏好）产品化
这块数据模型已有，但基本还没进入主流程。

因为：
- `UserInvestProfile` 已有：[D:\invest\background\accounts\models.py:81](D:\invest\background\accounts\models.py:81)
- 获取/更新接口已有：[D:\invest\background\accounts\views.py:125](D:\invest\background\accounts\views.py:125)
- 前端当前更偏“个人资料展示”，不是“投资偏好驱动”

可扩展内容：
- 风险偏好问卷
- 关注市场/偏好资产类型设置
- 基于偏好的首页推荐（内容、组合、资产）
- “适合你”的组合推荐

这是后续做个性化推荐的基础。

**中期最有价值的功能**
这些不是“补洞”，而是把项目从社区工具升级成真正的投资产品。

5. 交易流水（Trade Record）与真实收益体系
这是最关键的“专业化升级”。

目前的持仓只有：
- `quantity`
- `cost_price`

这意味着：
- 能算浮盈亏
- 但不能算已实现收益
- 不能算现金流
- 不能还原历史仓位变化

项目文档本身也已经把这件事列为二期方向：[D:\invest\docs\holding_profit_calculation.md](D:\invest\docs\holding_profit_calculation.md)

建议扩展：
- 买入/卖出记录
- 分红、拆股、送股
- 已实现收益 / 未实现收益 / 总收益拆分
- 按时间维度的资金曲线
- 持仓变动历史

这是后续做“组合回测、账户分析、交易复盘”的前提。

6. 组合收益自动化
现在 `returns_ytd` 是一个存储字段，不是自动计算引擎驱动：[D:\invest\background\portfolios\models.py:21](D:\invest\background\portfolios\models.py:21)

这意味着当前组合更像“静态分享卡片”，不是“动态组合产品”。

建议扩展：
- 根据组合内资产的最新行情自动算收益
- 组合净值曲线
- 组合回撤、波动率、胜率
- 与指数基准对比（沪深 300、标普 500 等）
- 再平衡建议

这是把“投资组合”从内容模块变成核心产品模块的关键一步。

7. 自选股 / 价格预警
这和通知中心能天然联动。

现有基础：
- 资产体系成熟
- 行情快照成熟
- 通知体系已存在
- `Alert` 模型存在，但当前偏风控告警，不是面向投资者的提醒：[D:\invest\background\reports\models.py:50](D:\invest\background\reports\models.py:50)

建议扩展：
- 自选股列表
- 涨跌幅提醒
- 价格到位提醒
- 成交量异常提醒
- 开盘/收盘提醒
- 财报日历提醒

这类功能用户粘性很强。

8. 更丰富的内容类型
当前 `Content` 本质还是统一“帖子”模型。
代码里已经预留了按 `content_type` 过滤的扩展位，但还没落地：[D:\invest\background\market_data\views.py:459](D:\invest\background\market_data\views.py:459) [D:\invest\background\market_data\views.py:470](D:\invest\background\market_data\views.py:470)

建议扩展：
- 观点帖
- 研报/长文
- 快讯
- 资产分析卡片
- 组合调仓日志

这样可以把社区内容从“论坛”升级成“研究内容平台”。

**更长期、拉开差距的功能**
如果你想把它做成更强的产品，可以往这几条走。

9. 模拟盘 / 纸面交易
你已经有：
- 资产
- 行情
- 持仓
- 收益曲线

因此很适合扩展为：
- 虚拟资金账户
- 模拟买卖
- 排行榜
- 跟单观察
- 模拟赛

这是最自然的“重产品”方向。

10. 策略回测 / 历史验证
已有 K 线和组合框架，继续向上可以做：
- 资产筛选器
- 简单因子回测
- 定投回测
- 调仓频率回测
- 组合历史净值重建

这会让项目从“社区 + 数据展示”升级到“策略研究工具”。

11. 个性化推荐系统
基于现有的：
- 用户关注
- 点赞
- 收藏
- 投资偏好
- 资产关联帖子
- 热门资产

可以做：
- 首页个性化 feed
- 推荐资产
- 推荐组合
- 推荐作者

这会显著提高留存。

**先别急着加功能，建议同步做的前置基础建设**
如果不先做，后续扩展会越来越慢。

1. 事件化通知机制
现在很多用户行为（点赞、评论、关注、审核）没有统一事件出口。
建议抽一层：
- 业务动作 -> 事件
- 事件 -> 通知 / 积分 / 审计 / 推荐特征更新

这样后面加新互动功能就不会到处埋逻辑。

2. 定时任务体系正式化
现在数据任务虽然有接口和命令，但更像“人工触发 + 命令驱动”。
建议补：
- Celery / 定时调度
- 失败重试
- 任务幂等
- 任务告警

这样行情同步、自选提醒、每日快照都能自动跑。

3. 类型和可维护性治理
前端很多核心页面都用了 `@ts-nocheck`，会直接拉低后续扩展速度。
而且还存在明显占位代码：
- 评论处有 TODO：[D:\invest\frontend\src\views\PostDetail.vue:218](D:\invest\frontend\src\views\PostDetail.vue:218)
- 内容列表里还有调试 `print`：[D:\invest\background\content\views.py:71](D:\invest\background\content\views.py:71)

建议在扩展前做一轮：
- 去掉关键页面的 `@ts-nocheck`
- 把通用分页/响应结构抽象
- 清理调试输出
- 把前端 placeholder 行为补齐

4. 配置安全与部署能力
如果要继续扩展成可长期运行的系统，这块要尽早处理：
- `DEBUG = True`：[D:\invest\background\invest_backend\settings.py:47](D:\invest\background\invest_backend\settings.py:47)
- `ALLOWED_HOSTS = ['*']`：[D:\invest\background\invest_backend\settings.py:49](D:\invest\background\invest_backend\settings.py:49)

这不是新功能，但它决定你后面能不能稳定上线。

**最推荐的三阶段路线**
如果目标是“扩展但不失控”，建议这样排：

1. 第一阶段（最快见效）
通知中心、关注流、全局搜索、投资偏好设置页  
这阶段主要是把“已有后端能力”产品化，投入小，收益大。

2. 第二阶段（建立产品护城河）
交易流水、组合收益自动计算、自选股/预警、内容类型升级  
这阶段会把项目从“投资社区”推到“投资工具平台”。

3. 第三阶段（拉开差距）
模拟盘、回测、推荐系统、跟单/订阅  
这阶段才是差异化和长期价值。

**一句话结论**
接下来最值得扩展的，不是再加一个孤立模块，而是优先把“通知、关注流、搜索、投资偏好”这些已预埋能力补全；然后再进入“交易流水 + 组合收益自动化 + 自选预警”这条专业化路线。这样扩展最稳，产品价值也增长最快。

如果你要，我下一步可以直接给你一份更具体的扩展清单，按这三种方式之一输出：

1. 按“产品价值 / 开发成本”做优先级矩阵  
2. 按“数据库设计 + API + 前端页面”拆成实施方案  
3. 直接给出一个 4 到 8 周的迭代排期表