# Asset 强外键关联升级开发记录

> **记录日期**：2026-02-26  
> **涉及模块**：`portfolios`（后端）、`frontend/src/views`、`frontend/src/api`  
> **核心目标**：将"股票"从字符串/虚拟数据，升级为与 `Asset` 表强外键关联的真实资产，使社区讨论、投资组合、个人持仓三个域都能关联到具体的数据库股票记录

---

## 一、背景与问题

### 升级前的状态

`PortfolioAsset` 表使用 `symbol`（CharField）和 `name`（CharField）存储资产信息，没有真实外键：

```python
# 升级前
class PortfolioAsset(models.Model):
    portfolio = models.ForeignKey(Portfolio, ...)
    symbol = models.CharField(max_length=20)   # 纯字符串，无法关联行情
    name = models.CharField(max_length=100)    # 纯字符串，无法追溯
    allocation = models.DecimalField(...)
    unique_together = ['portfolio', 'symbol']
```

### 问题

| 问题 | 影响 |
|------|------|
| 无法关联到真实行情数据 | 组合内资产看不到价格/涨跌幅 |
| 无法聚合讨论 | 不知道帖子讨论的是哪个 `asset_id` 对应的资产 |
| 无法验证资产是否存在 | 用户可随意填入不存在的代码 |
| 无个人持仓功能 | 没有模型记录用户的个人股票仓位 |

---

## 二、修改文件清单

### 后端

| 文件路径 | 变更类型 | 说明 |
|---------|---------|------|
| `portfolios/models.py` | **修改** | `PortfolioAsset` 增加 `asset` FK；新增 `UserHolding` 模型 |
| `portfolios/serializers.py` | **修改** | 升级资产序列化器，新增持仓序列化器 |
| `portfolios/views.py` | **修改** | 升级组合视图，新增持仓 CRUD 视图 |
| `portfolios/urls.py` | **修改** | 注册 `/api/holdings/` 路由 |
| `portfolios/migrations/0002_*.py` | **新建** | 数据库迁移文件 |

### 前端

| 文件路径 | 变更类型 | 说明 |
|---------|---------|------|
| `src/types/index.ts` | **修改** | `PortfolioAsset` 增加 `assetId` 等字段；新增 `UserHolding` 类型 |
| `src/api/holdings.ts` | **新建** | 个人持仓 API 封装 |
| `src/views/Portfolios.vue` | **修改** | 资产输入框升级为数据库远程搜索选择器 |
| `src/views/MyHoldings.vue` | **新建** | 个人持仓管理页面 |
| `src/router/index.ts` | **修改** | 注册 `/holdings` 路由 |
| `src/components/layout/MainLayout.vue` | **修改** | 侧边栏增加「我的持仓」入口 |

---

## 三、核心设计

### 3.1 "真实 code 贯穿全系统" 原则

```
asset.code + asset.market  →  用户展示层（如 "000001 · A股·深交所"）
asset.finnhub_symbol       →  第三方 API 调用层
asset.tushare_ts_code      →  Tushare Pro 调用层
asset_id (FK)              →  业务层引用（portfolio / holding / content 关联键）
```

### 3.2 PortfolioAsset 模型升级

```python
class PortfolioAsset(models.Model):
    portfolio = models.ForeignKey(Portfolio, ...)
    # ---- 新增：强外键关联 ----
    asset = models.ForeignKey(
        'content.Asset',
        on_delete=models.PROTECT,
        null=True, blank=True,     # null=True 保证历史数据兼容
        related_name='portfolio_assets'
    )
    # ---- 保留：冗余展示字段，由 asset 自动同步 ----
    symbol = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=100, blank=True)
    allocation = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ['portfolio', 'asset']   # 由 symbol 改为 asset

    def save(self, *args, **kwargs):
        # 关联资产时，自动同步冗余字段
        if self.asset_id and self.asset:
            self.symbol = self.asset.code
            self.name = self.asset.name
        super().save(*args, **kwargs)
```

**设计要点：**
- `asset` FK 设为 `null=True`，存量无 FK 的历史数据不会报错
- 冗余字段 `symbol`/`name` 保留，序列化时优先从 `asset` 读取，降级时读冗余字段
- `unique_together` 从 `['portfolio', 'symbol']` 改为 `['portfolio', 'asset']`，防止同一组合内同一资产重复

### 3.3 新增 UserHolding 模型

```python
class UserHolding(models.Model):
    """个人持仓表：记录用户持有的具体资产仓位"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='holdings')
    asset = models.ForeignKey('content.Asset', on_delete=models.PROTECT, related_name='user_holdings')
    quantity = models.DecimalField('持有数量', max_digits=18, decimal_places=4)
    cost_price = models.DecimalField('成本均价', max_digits=12, decimal_places=4)
    notes = models.TextField('备注', blank=True)
    created_at / updated_at ...

    class Meta:
        unique_together = ['user', 'asset']   # 同一用户同一资产只有一条持仓记录
```

---

## 四、API 接口设计

### 4.1 组合相关（已有接口升级）

#### 创建组合 `POST /api/portfolios/`

**升级点：** `assets` 数组中新增 `assetId` 字段，优先用 FK 关联，保留 `symbol` 作为旧接口兜底。

请求体：
```json
{
  "title": "科技赛道组合",
  "riskLevel": "High",
  "isPublic": true,
  "assets": [
    { "assetId": 1234, "allocation": 60 },
    { "assetId": 5678, "allocation": 40 }
  ]
}
```

响应 `assets` 字段（新增字段）：
```json
"assets": [
  {
    "assetId": 1234,
    "symbol": "600519",
    "name": "贵州茅台",
    "market": "SH",
    "assetType": "STOCK",
    "displayMarket": "A股·上交所",
    "allocation": 60
  }
]
```

### 4.2 个人持仓（全新接口）

#### 获取我的持仓列表 `GET /api/holdings/`

- **权限**：需要登录
- **响应**：

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 1,
        "assetId": 1234,
        "code": "600519",
        "name": "贵州茅台",
        "market": "SH",
        "assetType": "STOCK",
        "displayMarket": "A股·上交所",
        "quantity": "100",
        "costPrice": "1800.00",
        "notes": "长期持有",
        "createdAt": "2026-02-26T10:00:00Z",
        "updatedAt": "2026-02-26T10:00:00Z"
      }
    ],
    "total": 1
  }
}
```

#### 新增或更新持仓 `POST /api/holdings/`

- **权限**：需要登录
- **逻辑**：按 `(user, assetId)` 做 upsert（已有则更新，没有则新建）
- **请求体**：

```json
{
  "assetId": 1234,
  "quantity": 100,
  "costPrice": 1800.00,
  "notes": "长期持有"
}
```

#### 更新持仓 `PATCH /api/holdings/{id}/`

- **权限**：需要登录（且必须是本人）
- **请求体**：同上（部分字段可选）

#### 删除持仓 `DELETE /api/holdings/{id}/`

- **权限**：需要登录（且必须是本人）
- **响应**：`{ "code": 0, "message": "持仓已删除" }`

---

## 五、序列化器设计

### 5.1 读写分离

```
PortfolioAssetSerializer       → 读取（含 assetId/market/displayMarket 等嵌套字段）
PortfolioAssetCreateSerializer → 写入（接受 assetId 或 symbol，校验资产存在性）

UserHoldingSerializer          → 读取（含资产完整信息）
UserHoldingCreateSerializer    → 写入（接受 assetId，执行 upsert）
```

### 5.2 AssetBriefSerializer（嵌套复用）

```python
class AssetBriefSerializer(serializers.ModelSerializer):
    assetType = serializers.CharField(source='asset_type', read_only=True)
    displayMarket = serializers.CharField(source='display_market', read_only=True)

    class Meta:
        model = Asset
        fields = ['id', 'code', 'name', 'assetType', 'market', 'displayMarket']
```

### 5.3 兼容策略

`PortfolioAssetSerializer` 读取时的降级逻辑：

```python
def get_symbol(self, obj):
    return obj.asset.code if obj.asset else obj.symbol  # 优先 FK，降级冗余字段

def get_market(self, obj):
    return obj.asset.market if obj.asset else ''        # 无 FK 历史数据返回空字符串
```

---

## 六、前端升级说明

### 6.1 Portfolios.vue - 资产输入框升级

**升级前：** 手动填写代码 + 名称（无验证，任意字符串）

**升级后：** `el-select` 远程搜索组件，调用 `GET /api/assets/?q=关键词`，下拉展示真实资产

```
搜索框输入 "茅台"
        ↓ 调用 getAssetsWithQuote({ q: '茅台' })
        ↓ 展示下拉：[ 600519 贵州茅台 · A股 ]
选中后   → 自动填充 assetId=1234, symbol='600519', name='贵州茅台', market='SH'
```

发给后端的 assets 数组：
```json
{ "assetId": 1234, "symbol": "600519", "name": "贵州茅台", "allocation": 60 }
```

### 6.2 MyHoldings.vue - 个人持仓页（新建）

**页面功能：**

| 区域 | 说明 |
|------|------|
| 持仓汇总卡片 | 持仓数量、持仓总成本（估算）、市场分布 |
| 持仓表格 | 代码、名称、市场标签、类型、数量、成本均价、持仓成本、备注、更新时间 |
| 添加持仓对话框 | 远程搜索选择资产 + 填写数量/成本/备注，执行 upsert |
| 编辑/删除持仓 | 行内操作，编辑时显示当前资产（不可修改资产），只能改数量/成本/备注 |
| 快速跳转 | 点击资产代码跳转到 `/assets/{assetId}` 个股详情页 |

**数字格式化规范：**

| 场景 | 格式 |
|------|------|
| 数量 | `toLocaleString('zh-CN')`，如 `10,000` |
| 成本均价 | 保留 2 位小数，如 `1800.00` |
| 持仓成本 | 自动换算（元/万/亿），如 `18.00万` |
| 日期 | `MM/DD`，如 `02/26` |

### 6.3 导航菜单

侧边栏「我的持仓」入口：登录用户可见，对应路由 `/holdings`，图标 `Coin`。

---

## 七、数据库迁移说明

迁移文件：`portfolios/migrations/0002_add_asset_fk_and_user_holding.py`

**关键操作：**
1. `unique_together` 先清空（允许 null）
2. 新增 `asset` ForeignKey（`null=True`）
3. `symbol`/`name` 改为 `blank=True`
4. 重建 `unique_together = ['portfolio', 'asset']`
5. 新建 `UserHolding` 表及索引

**迁移后状态：**
- 历史 `PortfolioAsset` 数据中 `asset=NULL`（正常，序列化时降级读 symbol/name）
- 新建组合时传 `assetId` 则 `asset` 字段有值，享有完整功能

---

## 八、关联设计图

```
  ┌──────────────┐       ┌──────────────────────────────────────┐
  │   content    │       │           portfolios                 │
  │              │       │                                      │
  │  Asset       │◀──FK──│  PortfolioAsset.asset                │
  │  ─────────── │       │  （组合持仓：code/name 由 asset 同步）│
  │  id          │       │                                      │
  │  code        │◀──FK──│  UserHolding.asset                   │
  │  name        │       │  （个人持仓：quantity/cost_price）    │
  │  market      │       │                                      │
  │  asset_type  │       └──────────────────────────────────────┘
  │  tushare_ts  │
  │  finnhub_sym │       ┌──────────────────────────────────────┐
  │              │       │           content                    │
  │              │◀──M2M─│  ContentAsset（帖子关联资产）         │
  └──────────────┘       └──────────────────────────────────────┘

       ↑ 三个域（组合/持仓/社区）均通过 asset_id FK 关联到同一资产记录
```

---

## 九、验收自测清单

### 组合分享

- [ ] 创建组合时，资产选择框可输入关键词远程搜索真实股票
- [ ] 选中股票后显示代码、名称、市场标签
- [ ] 创建成功后，组合详情 `assets[].assetId` 有值（非 null）
- [ ] 组合卡片饼图展示选中的真实股票代码

### 个人持仓

- [ ] `/holdings` 页面正常加载，空状态展示引导文案
- [ ] 搜索框可查找 A 股/美股/港股资产
- [ ] 新增持仓后列表刷新，数量/成本正确展示
- [ ] 编辑持仓：资产字段不可修改，数量/成本可改
- [ ] 删除持仓：弹确认框，删除后刷新
- [ ] 点击资产代码跳转个股详情页
- [ ] 汇总卡片持仓成本估算正确

### 数据关联一致性

- [ ] `PortfolioAsset.asset` 有值时，序列化返回完整 `market`、`assetType`、`displayMarket`
- [ ] `PortfolioAsset.asset` 为 null（历史数据）时，序列化降级读 `symbol`/`name`，不报错
- [ ] `UserHolding` 删除时，`Asset` 不被级联删除（`on_delete=PROTECT`）

---

## 十、后续扩展建议

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 持仓行情联动 | 在持仓列表实时展示最新价 + 浮盈浮亏（调用 `POST /api/assets/quotes/`） | P1 |
| 持仓变动历史 | 增加 `UserHoldingHistory` 记录每次买卖操作 | P2 |
| 组合收益计算 | 按持仓成本 + 最新价自动计算 `returnsYTD` | P1 |
| 批量导入持仓 | 支持 CSV 上传个人持仓数据 | P3 |
| 持仓分享 | 将个人持仓导出为可分享的组合快照 | P2 |

---

*文档由开发记录整理，对应功能：asset_id 强外键关联升级 + 个人持仓模块*
