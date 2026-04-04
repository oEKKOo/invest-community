# asset_quote_snapshot 索引说明（榜单与行情查询）

## 背景

`/api/market/rankings/` 在 `asset_quote_snapshot` 上：

- 用子查询匹配「每个资产最新一条」快照（与 `asset_id`、`quote_time` 相关）；
- 再按 `change_pct`（涨幅/跌幅榜）或 `volume`（活跃榜）排序并 `LIMIT`。

数据量大时，缺少排序字段索引易产生 **Using filesort**、慢查询（约数秒）。

## 已有索引（Django `Meta.indexes` / 迁移）

| 索引名 | 字段 | 用途 |
|--------|------|------|
| `idx_quote_asset_time` | `(asset_id, quote_time DESC)` | 按资产取最新快照、时间过滤 |
| `idx_quote_asset_created` | `(asset_id, created_at DESC)` | 按写入时间取某资产最新快照（如列表带 `withQuote` 的子查询） |
| `idx_quote_time` | `(quote_time DESC)` | 按时间扫表/清理 |
| `idx_quote_change_pct` | `(change_pct DESC)` | 涨幅/跌幅榜排序 |
| `idx_quote_volume` | `(volume DESC)` | 活跃榜按成交量排序 |

主键 `id` 默认存在。

## 应用迁移

```bash
cd background
python manage.py migrate market_data
```

## 自检（MySQL 8）

```sql
SHOW INDEX FROM asset_quote_snapshot;

EXPLAIN SELECT ...
-- 在 Django Debug Toolbar 或开启慢查询日志中观察是否仍出现 filesort
```

迁移 `market_data.0004` 增加 `idx_quote_asset_created`；应用后执行 `python manage.py migrate market_data`。

## 若仍慢

- 确认 `MARKET_RANKINGS_CACHE_TTL`（默认约 20s）命中 Redis/LocMem 缓存；
- 用 Debug Toolbar 看该接口 **重复 SQL** 与 **实际执行计划**；
- 快照表行数极大时，可配合定期清理任务（已有 `cleanup_old_snapshots` 类逻辑）控制表规模。
