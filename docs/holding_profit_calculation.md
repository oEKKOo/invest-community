# 个人持仓收益计算功能设计与实现文档

> **文档版本**：1.0  
> **完成日期**：2026-02-26  
> **功能模块**：portfolios（Django App）+ MyHoldings（Vue 前端页面）

---

## 一、功能背景与设计目标

### 1.1 背景

由于行情数据 API（Tushare / Finnhub）的调用频率受限，无法做到股票价格实时更新，因此采用**模拟基金每日净值**的方式来呈现个人持仓收益：

- 以**日 K 收盘价**为唯一估值口径
- 每天固定更新一次（或系统启动时仅补缺）
- 所有收益计算均基于"每日价格快照"

### 1.2 收益口径定义

| 收益类型 | 计算公式 | 说明 |
|---|---|---|
| **当日收益（Daily PnL）** | `Σ(quantity × (price_today - price_yesterday))` | 以昨日估值 → 今日估值之差计算 |
| **当日收益率** | `daily_pnl / total_value_yesterday` | 前一日总市值为基数 |
| **持有收益（Unrealized PnL）** | `Σ(quantity × (price_today - avg_cost))` | 成本价 → 今日估值之差 |
| **持有收益率** | `unrealized_pnl / total_cost_value` | 以总持仓成本为基数 |
| **累计收益（Total PnL）** | MVP 阶段：等同于持有收益（浮盈亏） | 二期可拆分已实现+未实现 |

---

## 二、数据库变更

### 2.1 新增表：`holding_daily_snapshot`

**文件**：`background/portfolios/models.py`

```python
class HoldingDailySnapshot(models.Model):
    """
    持仓每日价格快照
    以日K收盘价为唯一估值口径，用于计算日收益/持有收益/累计收益。
    设计原则：
      - 每天固定更新一次（或启动时补缺）
      - 只存 close_price，计算时结合 UserHolding.quantity / cost_price 实时推导
      - unique_together = (holding, date)，防止重复写入
    """
    holding = models.ForeignKey(UserHolding, on_delete=models.CASCADE, related_name='daily_snapshots')
    date = models.DateField('快照日期')
    close_price = models.DecimalField('收盘估值价', max_digits=18, decimal_places=6)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'holding_daily_snapshot'
        unique_together = ['holding', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['holding', '-date'], name='idx_holding_snap_date'),
        ]
```

**字段说明**

| 字段 | 类型 | 说明 |
|---|---|---|
| `holding` | FK → `UserHolding` | 关联持仓，CASCADE 删除 |
| `date` | DateField | 快照日期（交易日） |
| `close_price` | DECIMAL(18,6) | 当日收盘价，来源 `AssetKline.close` |
| `created_at` | DateTimeField | 快照写入时间 |

**唯一约束**：`(holding, date)` — 同一持仓同一天只有一条快照，防止重复写入。

### 2.2 迁移文件

**文件**：`background/portfolios/migrations/0003_holding_daily_snapshot.py`

依赖迁移：
- `content.0003_add_asset_fk_and_user_holding`
- `portfolios.0002_add_asset_fk_and_user_holding`

执行方式：
```bash
cd D:\invest\background
python manage.py migrate portfolios
```

---

## 三、后端实现

### 3.1 数据补缺管理命令

**文件**：`background/portfolios/management/commands/fill_holding_snapshots.py`

#### 功能说明

从 `AssetKline`（日 K 表）中读取历史收盘价，为所有 `UserHolding` 批量生成缺失的每日快照记录。

#### 核心逻辑

1. 查询所有（或指定）用户持仓
2. 获取该持仓已有的快照日期集合（避免重复写入）
3. 从 `AssetKline` 拉取该资产在回补范围内的日 K 数据
4. 过滤掉已有快照日期，批量 `bulk_create`（`ignore_conflicts=True`）

#### 命令用法

```bash
# 默认：回补所有持仓最近 365 天的缺失快照
python manage.py fill_holding_snapshots

# 指定回补天数（如 90 天）
python manage.py fill_holding_snapshots --days 90

# 只处理指定用户的持仓
python manage.py fill_holding_snapshots --user-id 1

# 只处理单条持仓（调试）
python manage.py fill_holding_snapshots --holding-id 5

# 强制重建：先删除 cutoff 日期之后的快照再重新生成
python manage.py fill_holding_snapshots --force
```

#### 输出示例

```
📅 回补范围：2025-02-26 ~ 今天，force=False
📦 待处理持仓数：3
  ✅ 000001 (SZ): 新增 125 条快照
  ✅ AAPL (US): 新增 98 条快照
  ⚠️  600519 (SH): 无日K数据，跳过

🎉 完成！新增 223 条 | 跳过 0 条 | 无K线 1 个持仓
```

#### 建议使用场景

| 场景 | 命令 |
|---|---|
| 服务首次启动时补缺 | `fill_holding_snapshots --days 365` |
| 每日收盘后定时任务 | `fill_holding_snapshots --days 3`（只补最近几天） |
| 新增持仓后补充历史数据 | `fill_holding_snapshots --holding-id {id} --days 365` |
| 数据异常重建 | `fill_holding_snapshots --force --days 30` |

### 3.2 收益查询 API

**文件**：`background/portfolios/views.py`

#### 接口定义

```
GET /api/holdings/performance/
权限：需要登录（IsAuthenticated）
```

#### 响应结构

```json
{
  "code": 0,
  "data": {
    "asOf": "2026-02-25",
    "totalMarketValue": "120000.00",
    "totalCostValue": "100000.00",
    "totalUnrealizedPnl": "20000.00",
    "totalUnrealizedReturn": "0.2000",
    "totalDailyPnl": "500.00",
    "totalDailyReturn": "0.0042",
    "hasAnyData": true,
    "items": [
      {
        "holdingId": 1,
        "assetId": 10,
        "code": "000001",
        "name": "平安银行",
        "market": "SZ",
        "displayMarket": "深市A",
        "assetType": "STOCK",
        "quantity": "1000.0000",
        "costPrice": "12.0000",
        "todayPrice": "13.5000",
        "yesterdayPrice": "13.4500",
        "marketValue": "13500.00",
        "costValue": "12000.00",
        "unrealizedPnl": "1500.00",
        "unrealizedReturn": "0.1250",
        "dailyPnl": "50.00",
        "dailyReturn": "0.0037",
        "snapshotDate": "2026-02-25",
        "hasData": true
      }
    ]
  }
}
```

#### 字段说明

**汇总字段**

| 字段 | 说明 |
|---|---|
| `asOf` | 估值基准日期（最新快照日期） |
| `totalMarketValue` | 所有持仓当日市值之和 |
| `totalCostValue` | 所有持仓成本之和 |
| `totalUnrealizedPnl` | 总持有收益（浮盈亏） |
| `totalUnrealizedReturn` | 总持有收益率（如 `"0.2000"` = 20%） |
| `totalDailyPnl` | 总当日收益 |
| `totalDailyReturn` | 总当日收益率 |
| `hasAnyData` | 是否有任意持仓具有快照数据 |

**单持仓字段（`items[]`）**

| 字段 | 说明 |
|---|---|
| `todayPrice` | 最新快照收盘价（估值价） |
| `yesterdayPrice` | 前一交易日快照收盘价 |
| `marketValue` | `quantity × todayPrice` |
| `unrealizedPnl` | `(todayPrice - costPrice) × quantity` |
| `dailyPnl` | `(todayPrice - yesterdayPrice) × quantity` |
| `hasData` | `false` 表示无 K 线快照，价格字段均为 `null` |

#### 注意事项

- 若某持仓无快照（`hasData: false`），所有价格字段返回 `null`，不影响其他持仓的计算
- 当日收益依赖**昨日快照**；若昨日快照不存在，`dailyPnl` 和 `dailyReturn` 均为 `null`
- 接口不实时调用行情 API，纯粹读取 `HoldingDailySnapshot` 数据库记录

### 3.3 URL 注册

**文件**：`background/portfolios/urls.py`

```python
path('holdings/performance/', views.HoldingPerformanceView.as_view(), name='holding_performance'),
```

---

## 四、前端实现

### 4.1 类型定义

**文件**：`frontend/src/types/index.ts`

新增两个接口类型：

```typescript
/** 单只持仓的收益明细 */
export interface HoldingPerformanceItem {
  holdingId: number
  assetId: number
  code: string
  name: string
  market: string
  displayMarket: string
  assetType: string
  quantity: string
  costPrice: string        // 成本均价
  todayPrice: string | null    // 今日估值价（日K close）
  yesterdayPrice: string | null  // 昨日估值价
  marketValue: string | null   // 今日市值
  costValue: string          // 持仓成本
  unrealizedPnl: string | null // 持有收益
  unrealizedReturn: string | null // 持有收益率（"0.0556" = 5.56%）
  dailyPnl: string | null      // 当日收益
  dailyReturn: string | null   // 当日收益率
  snapshotDate: string | null  // 快照日期 YYYY-MM-DD
  hasData: boolean           // false 表示无K线快照
}

/** 持仓收益汇总 */
export interface HoldingPerformance {
  asOf: string | null          // 估值基准日期
  totalMarketValue: string     // 总市值
  totalCostValue: string       // 总持仓成本
  totalUnrealizedPnl: string   // 总持有收益
  totalUnrealizedReturn: string  // 总持有收益率
  totalDailyPnl: string        // 总当日收益
  totalDailyReturn: string     // 总当日收益率
  hasAnyData: boolean          // 是否有任意一只有快照数据
  items: HoldingPerformanceItem[]
}
```

### 4.2 API 层

**文件**：`frontend/src/api/holdings.ts`

新增函数：

```typescript
// 获取持仓收益（基于每日快照，模拟基金净值效果）
export const getHoldingPerformance = (): Promise<HoldingPerformance> => {
  return get('/holdings/performance/')
}
```

### 4.3 MyHoldings.vue 页面改动

**文件**：`frontend/src/views/MyHoldings.vue`

#### 新增：收益概览 Banner

位于汇总卡片上方，在持仓非空时展示：

```
┌─────────────────────────────────────────────────────────────────┐
│  总市值                   当日收益          持有收益（浮盈）        │
│  ¥ 12.50 万              +500.00          +20,000.00           │
│  持仓成本: ¥ 10.00 万    +0.42%           +20.00%              │
│                                              估值日期：2026-02-25 ℹ│
└─────────────────────────────────────────────────────────────────┘
```

- **绿色（`pnl-up`）**：收益为正
- **红色（`pnl-down`）**：收益为负
- **灰色（`pnl-zero`）**：收益为零
- 无快照数据时显示"暂无行情快照，请先运行数据同步"提示
- 估值日期旁有 Tooltip 说明："基于日K收盘价，每日一次更新，无实时行情"

#### 新增：表格收益列

在"持仓成本"列之后新增 4 列：

| 列名 | 说明 | 无数据时 |
|---|---|---|
| **今日估值** | 最新快照收盘价（`¥ xx.xx`） | `—` |
| **市值** | `quantity × todayPrice`（万/亿自动换算） | `—` |
| **当日收益** | 涨跌额 + 涨跌率（绿涨红跌双行展示） | `—` |
| **持有收益** | 浮盈金额 + 收益率（绿涨红跌双行展示） | `—` |

#### 新增：格式化工具函数

```typescript
formatMoney(val)     // 带万/亿单位，如 "¥ 1.25 万"
formatMoneyShort(val) // 表格内简短格式，如 "1.25万"
formatPnl(val)       // 带正负号，如 "+500.00" 或 "-200.00"
formatRate(val)      // 百分比格式，如 "+5.56%" （输入 "0.0556"）
pnlClass(val)        // 返回 CSS 类名：'pnl-up' | 'pnl-down' | 'pnl-zero'
```

#### 数据刷新时机

| 操作 | 触发收益数据刷新 |
|---|---|
| 页面首次加载 | ✅ `onMounted` 并发请求 |
| 添加/编辑持仓成功 | ✅ 非阻塞刷新（`fetchPerformance()`） |
| 删除持仓成功 | ✅ 等待刷新 |

---

## 五、数据流图

```
用户持仓（UserHolding）
    │ quantity, cost_price
    ↓
AssetKline（日K表）
    │ resolution='D', close
    ↓
fill_holding_snapshots（管理命令/定时任务）
    │ bulk_create
    ↓
HoldingDailySnapshot（每日快照表）
    │ holding, date, close_price
    ↓
GET /api/holdings/performance/
    │ 计算今日/昨日差值
    ↓
前端 MyHoldings.vue
    │ 收益概览 Banner + 表格列
    ↓
用户查看收益
```

---

## 六、收益计算示例

**场景**：用户持有平安银行 `000001` 1000 股，成本均价 12.00 元

| 日期 | 收盘价 | 当日收益 | 当日收益率 | 持有收益 | 持有收益率 |
|---|---|---|---|---|---|
| 2026-02-20 | 12.50 | — | — | +500.00 | +4.17% |
| 2026-02-21 | 13.00 | +500.00 | +4.00% | +1000.00 | +8.33% |
| 2026-02-24 | 13.20 | +200.00 | +1.54% | +1200.00 | +10.00% |
| 2026-02-25 | 13.50 | +300.00 | +2.27% | +1500.00 | +12.50% |

> 注：当日收益率 = daily_pnl / 昨日市值

---

## 七、运维建议

### 7.1 数据初始化

首次部署后执行：

```bash
# 1. 先确保 AssetKline 日K数据已同步（依赖 Tushare/Finnhub）
python manage.py sync_market_data --candles

# 2. 为所有持仓生成历史快照（最近1年）
python manage.py fill_holding_snapshots --days 365
```

### 7.2 定时任务（每日执行一次）

建议在每个交易日收盘后（约 16:00）执行：

```bash
python manage.py fill_holding_snapshots --days 3
```

可通过 **Celery Beat** 或系统 **cron** 调度：

```cron
# 每个工作日 16:30 执行（服务器时区为 UTC+8）
30 16 * * 1-5 cd /path/to/background && python manage.py fill_holding_snapshots --days 3
```

### 7.3 数据依赖关系

```
AssetKline（日K数据）
    ↑
    由 sync_market_data --candles 命令填充
    （依赖：Asset.tushare_ts_code 或 Asset.finnhub_symbol）
    
HoldingDailySnapshot（持仓快照）
    ↑
    由 fill_holding_snapshots 命令从 AssetKline 中读取并生成
    （依赖：UserHolding 存在 + AssetKline 有对应资产的日K数据）
```

---

## 八、已知限制与二期规划

### 8.1 当前限制（MVP）

| 限制 | 说明 |
|---|---|
| 无实时价格 | 估值价为前一交易日收盘价，非当日实时价 |
| 累计收益 = 持有收益 | 未引入交易流水，无法计算已实现收益 |
| 非交易日无快照 | 周末/节假日无 K 线数据，对应日期不生成快照 |
| 持仓变更不溯源 | 修改成本价/数量后，历史快照的 `unrealizedPnl` 需重新计算 |

### 8.2 二期优化方向

1. **引入交易流水（TradeRecord）**
   - 记录每次买入/卖出：时间、价格、数量
   - 已实现收益 = Σ(卖出价 - 成本价) × 卖出数量
   - 累计收益 = 已实现收益 + 未实现收益

2. **快照中冗余持仓信息**
   - 快照写入时同步记录 `quantity`、`cost_price`
   - 持仓变更时触发快照重建（而非依赖实时 `UserHolding` 字段）

3. **服务启动自动补缺**
   - Django `AppConfig.ready()` 中异步触发 `fill_holding_snapshots`

4. **收益走势图**
   - 以日期为横轴，市值为纵轴
   - 基于 `HoldingDailySnapshot` 聚合历史数据，使用 ECharts 绘制曲线

---

## 九、相关文件索引

| 文件路径 | 说明 |
|---|---|
| `background/portfolios/models.py` | `HoldingDailySnapshot` 模型定义 |
| `background/portfolios/migrations/0003_holding_daily_snapshot.py` | 数据库迁移文件 |
| `background/portfolios/management/commands/fill_holding_snapshots.py` | 数据补缺管理命令 |
| `background/portfolios/views.py` | `HoldingPerformanceView` API 视图 |
| `background/portfolios/urls.py` | URL 路由注册 |
| `frontend/src/types/index.ts` | `HoldingPerformance` / `HoldingPerformanceItem` 类型定义 |
| `frontend/src/api/holdings.ts` | `getHoldingPerformance()` API 函数 |
| `frontend/src/views/MyHoldings.vue` | 收益概览 Banner + 表格收益列 |
