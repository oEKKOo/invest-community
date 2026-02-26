# A 股数据接入开发记录

> **记录日期**：2026-02-26  
> **涉及模块**：`market_data`、`content`、`invest_backend`  
> **数据源**：[Tushare Pro](https://tushare.pro)（A 股）+ Finnhub（美股 / 港股，原有）

---

## 一、背景与目标

项目原本仅通过 **Finnhub API** 提供美股行情数据。  
本次扩展目标：

- 接入 **Tushare Pro API**，支持沪深京三大交易所 A 股数据
- 覆盖：股票列表同步、日 K 线、分钟 K 线、最新行情快照
- 与原有 Finnhub 数据源并存，按市场标识（`market` 字段）动态路由

---

## 二、新增 / 修改的文件清单

| 文件路径 | 变更类型 | 说明 |
|---------|---------|------|
| `market_data/tushare_service.py` | **新建** | Tushare API 服务封装层 |
| `market_data/management/commands/import_cn_stocks.py` | **新建** | A 股批量导入管理命令 |
| `market_data/tasks.py` | **修改** | 数据同步任务增加 A 股路由 |
| `market_data/views.py` | **修改** | K 线 / 行情接口支持 Tushare |
| `content/models.py` | **修改** | `Asset` 增加 `tushare_ts_code` 字段 |
| `invest_backend/settings.py` | **修改** | 增加 Tushare Token 配置检测 |
| `requirements.txt` | **修改** | 增加 `tushare>=1.4.0` |
| `.env` | **修改** | 写入 `TUSHARE_API_TOKEN` |

---

## 三、核心设计

### 3.1 数据源路由策略

按 `Asset.market` 字段选择数据源：

```
market ∈ {SH, SZ, BJ}  →  Tushare Pro
market ∈ {US, HK, ...} →  Finnhub
```

代码体现（`tasks.py`、`views.py` 均采用同一规则）：

```python
if asset.market in ['SH', 'SZ', 'BJ']:
    data = ts_svc.get_daily_klines(asset.tushare_ts_code, ...)
else:
    data = fh.get_candles(asset.finnhub_symbol, ...)
```

### 3.2 市场标识映射

Tushare 原始字段 → 项目内部 `market` 字段：

| Tushare `exchange` | Tushare `market` | 内部 `market` |
|--------------------|-----------------|--------------|
| SSE（上交所）      | 主板 / 科创板   | `SH`         |
| SZSE（深交所）     | 主板 / 创业板   | `SZ`         |
| BSE（北交所）      | 北交所          | `BJ`         |

股票代码前缀推断规则（用于修复旧数据）：

| 代码前缀 | 归属市场 |
|---------|---------|
| `6xxxx`、`5xxxx` | `SH` |
| `8xxxx`、`4xxxx` | `BJ` |
| 其余（`0`、`2`、`3` 开头） | `SZ` |

### 3.3 Asset 模型新增字段

```python
# content/models.py
tushare_ts_code = models.CharField(
    max_length=16, blank=True, default='',
    help_text='Tushare ts_code，如 600519.SH'
)
```

数据库唯一约束（DB 实际约束）：

```sql
UNIQUE KEY uk_asset_type_code (asset_type, code)
```

> ⚠️ 注意：DB 约束只含 `(asset_type, code)`，**不含 market**。  
> 代码中的 `update_or_create` 必须以 `(code, asset_type)` 为查找键，`market` 放进 `defaults`。

---

## 四、新增服务层：`tushare_service.py`

### 关键函数

| 函数 | 说明 |
|------|------|
| `_init_tushare_api()` | 懒初始化 Tushare Pro API（单例，Token 来自环境变量） |
| `is_api_token_configured()` | 检测 Token 是否已配置（供其他模块调用） |
| `get_stock_basic(list_status, exchange)` | 获取 A 股股票列表 |
| `get_daily_klines(ts_code, start_date, end_date)` | 获取日 K 线数据 |
| `get_minute_klines(ts_code, freq, start_date, end_date)` | 获取分钟 K 线数据 |
| `get_latest_daily_quote(ts_code)` | 获取最新日行情快照 |

### API Key 管理规范

```python
def _get_api_token() -> str:
    # 从环境变量读取，禁止明文写入代码或日志
    return os.environ.get('TUSHARE_API_TOKEN', '')
```

`.env` 配置：
```
TUSHARE_API_TOKEN=<your_token_here>
```

---

## 五、管理命令：`import_cn_stocks`

### 支持的参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--list-status` | `L` | `L`上市 / `D`退市 / `P`暂停 |
| `--exchange` | 全市场 | `SSE` / `SZSE` / `BSE` |
| `--codes` | 全部 | 指定股票代码（逗号分隔） |
| `--kline` | false | 导入后同步日 K 线 |
| `--quote` | false | 导入后刷新行情快照 |
| `--days` | 365 | K 线同步天数 |
| `--kline-only` | false | 不重新导入，仅同步已入库股票的 K 线 |
| `--quote-only` | false | 不重新导入，仅刷新已入库股票行情 |
| `--force` | false | K 线强制回补（删除后重拉） |
| `--delay` | 0.5 | 每次 API 请求间隔（秒） |

### 常用命令示例

```bash
# 1. 导入全部上市 A 股（约 5500 只）
python manage.py import_cn_stocks

# 2. 导入 + 同步最近一年日 K 线
python manage.py import_cn_stocks --kline --days 365

# 3. 导入 + K 线 + 行情（一步到位）
python manage.py import_cn_stocks --kline --quote --days 365

# 4. 只同步 K 线（对已入库 A 股）
python manage.py import_cn_stocks --kline-only --days 365

# 5. 只刷新行情快照
python manage.py import_cn_stocks --quote-only

# 6. 只导入重点股票
python manage.py import_cn_stocks --codes 600519,000858,300750,000001 --kline --quote

# 7. 只导入上交所股票
python manage.py import_cn_stocks --exchange SSE

# 8. 只导入深交所创业板
python manage.py import_cn_stocks --exchange SZSE
```

---

## 六、数据同步任务变更（`tasks.py`）

### 新增任务：`cn_symbols_sync`

```python
def cn_symbols_sync(market: str) -> DataJobLog:
    """拉取 A 股列表并写入 Asset 表（支持增量更新）"""
```

调用示例（API 触发）：
```http
POST /api/market/job/trigger/
{
  "job_type": "CN_SYMBOLS_SYNC",
  "market": "SH"
}
```

### 修改任务：`kline_sync`

```python
cn_qs = queryset.filter(market__in=['SH', 'SZ', 'BJ'])
fh_qs = queryset.exclude(market__in=['SH', 'SZ', 'BJ'])

# A 股：Tushare 日 K 线
for asset in cn_qs:
    data = ts_svc.get_daily_klines(asset.tushare_ts_code, start_date, end_date)
    ...

# 美股/港股：Finnhub K 线
for asset in fh_qs:
    data = fh.get_candles(asset.finnhub_symbol, resolution, ...)
    ...
```

### 修改任务：`quote_refresh`

```python
cn_assets = [a for a in assets if a.market in ['SH', 'SZ', 'BJ']]
fh_assets = [a for a in assets if a.market not in ['SH', 'SZ', 'BJ']]

# A 股：Tushare 最新日行情
for asset in cn_assets:
    quote = ts_svc.get_latest_daily_quote(asset.tushare_ts_code)
    ...
```

---

## 七、Bug 修复：重复键冲突

### 现象

```
(1062, "Duplicate entry 'STOCK-000001' for key 'asset.uk_asset_type_code'")
```

首次运行 `import_cn_stocks` 时，10 只重点股票（600519、000001 等）报重复键错误。

### 根本原因

```
数据库实际约束：uk_asset_type_code → UNIQUE(asset_type, code)        ← 不含 market
旧数据状态：    这 10 只股票已以 market='CN' 导入（来自 Finnhub 时期）
冲突触发：     update_or_create(code='000001', market='SZ', ...) 找不到
              market='CN' 的旧记录，触发 INSERT → 唯一约束报错
```

### 修复方案

将 `update_or_create` 查找键从 `(code, market, asset_type)` 改为 `(code, asset_type)`，`market` 放入 `defaults`：

```python
# 修复前（触发冲突）
Asset.objects.update_or_create(
    code=code, market=market, asset_type='STOCK',
    defaults={...}
)

# 修复后（正确匹配并更新旧记录）
Asset.objects.update_or_create(
    code=code, asset_type='STOCK',
    defaults={'market': market, ...}   # 顺带修正 market='CN' → SH/SZ/BJ
)
```

同步修复文件：`import_cn_stocks.py` 和 `tasks.py/cn_symbols_sync`。

### 存量数据修复

对数据库中残留的 `market='CN'` 记录，按代码前缀推断并一次性修正：

```python
for asset in Asset.objects.filter(market='CN'):
    if asset.code.startswith(('6', '5')):
        new_market = 'SH'
    elif asset.code.startswith(('8', '4')):
        new_market = 'BJ'
    else:
        new_market = 'SZ'
    Asset.objects.filter(id=asset.id).update(market=new_market)
```

---

## 八、最终数据状态（2026-02-26）

| 指标 | 数值 |
|------|------|
| A 股资产总数（SH + SZ + BJ） | **5,484 只** |
| 新增 | 5,464 只 |
| 更新（含旧 CN 记录修正） | 20 只 |
| 导入错误 | **0 条**（修复后） |
| 残留 `market='CN'` | **0 条** |
| 已有日 K 线的资产数 | 142 只（K 线同步进行中）|

---

## 九、后续运维

### 定期同步建议

```bash
# 每个交易日收盘后刷新行情（约 5500 次 API 调用）
python manage.py import_cn_stocks --quote-only

# 每周末回补 K 线数据
python manage.py import_cn_stocks --kline-only --days 30

# 季度更新股票列表（处理新股 / 退市）
python manage.py import_cn_stocks
```

### Tushare API 限流注意事项

| 账户级别 | 每分钟调用次数 | 建议 `--delay` |
|---------|--------------|---------------|
| 普通免费 | 50 次/分钟    | `2.0` 秒       |
| 积分用户 | 200+ 次/分钟  | `0.5` 秒       |
| 机构用户 | 无限制        | `0.1` 秒       |

### 环境变量配置（`.env`）

```ini
# Finnhub（美股/港股）
FINNHUB_API_KEY=your_finnhub_key_here

# Tushare Pro（A股）
TUSHARE_API_TOKEN=your_tushare_token_here
```

---

## 十、架构对比

```
                    ┌─────────────────────────────┐
                    │         market_data          │
                    │                              │
  外部数据源         │   get_or_refresh_quote()     │   内部存储
  ┌──────────┐      │   kline_sync()               │   ┌─────────────────┐
  │ Finnhub  │──────▶   quote_refresh()            │──▶│ AssetKline      │
  │ (US/HK)  │      │                              │   │ AssetQuoteSnap  │
  └──────────┘      │   market 路由逻辑：           │   │ Asset           │
  ┌──────────┐      │   SH/SZ/BJ → Tushare         │   └─────────────────┘
  │ Tushare  │──────▶   US/HK    → Finnhub         │
  │ (A股)    │      │                              │
  └──────────┘      └─────────────────────────────┘
```

---

*文档由开发记录自动整理，对应 commit：Tushare A 股数据接入*
