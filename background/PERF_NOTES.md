# API 性能自测说明

## 请求耗时日志

设置环境变量 `DJANGO_API_TIMING_LOG=true`（或在 `DEBUG=True` 时由 `invest_backend/perf_timing.py` 记录部分接口），在 `django.log` 中检索 `api_timing` / `duration_ms`。

## 建议用 Django Debug Toolbar（可选）

在 `DEBUG=True` 且安装 `django-debug-toolbar` 时，可对以下路径对比优化前后 **SQL 次数**：

- `GET /api/posts/`
- `GET /api/posts/{id}/`
- `GET /api/posts/{id}/comments/`
- `GET /api/assets/{id}/posts/` 与 `GET /api/assets/{id}/contents/`
- `GET /api/dashboard/overview/`
- `GET /api/users/{id}/overview/`

列表接口应不再对每条帖子执行独立的点赞/收藏 `exists()`；帖子列表响应以 `excerpt` 为主字段，体积应明显小于全文 `content`。

## EXPLAIN 热点 SQL（索引自测）

```bash
python manage.py db_explain_hot_paths
```

在 **MySQL** 上会对帖子流、标的讨论区、`favorite` 按用户时间排序、以及帖子关键词（`MATCH` FULLTEXT）、资产关键词等执行 `EXPLAIN`。请结合 `key`、`rows`、`Extra`（如 `Using filesort`）判断是否需继续优化查询或索引。

帖子关键词在 MySQL 上依赖迁移 `content.0010` 创建的 `FULLTEXT INDEX ft_content_title_body`；SQLite 等环境仍走 `icontains` 回退。

## 冷热数据与归档（运维备忘）

| 数据 | 策略说明 |
|------|----------|
| `asset_quote_snapshot` | 模型注释建议保留约 7 天；实现见 `market_data.tasks.cleanup_old_snapshots(days=7)`，建议由 Celery/定时任务每日执行；管理端也可走 `market_data` 相关清理接口（若有）。 |
| `asset_kline` | 按业务保留最近 N 根/区间；过量历史可迁出冷表或对象存储，配合 `DQ_CHECK` 任务做质量巡检。 |
| `notification` | 大量历史通知可按期归档到历史表或按时间清理已读记录，避免主表无限增长（需单独迁移/任务）。 |

全文检索中文若效果不佳，可在 MySQL 上为 `content` 使用 **ngram** 解析器重建 FULLTEXT（需 DBA 评估词长与存储）。

---

## 互动与媒体：回归自测清单（手工）

在前后端联调环境完成以下用例，对比优化前 Network 请求数与首屏耗时：

| 场景 | 预期 |
|------|------|
| 点赞 / 取消赞帖子 | 返回快；通知侧可走 Celery（无 worker 时 `on_commit` 同步执行仍正确） |
| 赞评论 | 同上 |
| 发表评论 / 回复 | 主事务短；积分与 `comment.created` 事件在提交后异步 |
| 关注 / 取关 | 粉丝数、关注数并发下不丢；取关用 `Greatest(F()-1,0)` |
| 帖子评论列表 | `GET /api/posts/{id}/comments/?page=1&pageSize=20` 返回 `data.items` 与 `total`；翻页不重复 |
| 楼中楼 | 预览 ≤5 条；展开后按页拉取回复，`加载更多回复` 仅在有剩余时显示 |
| 附件上传 | 超过大小或单边像素超限返回 400；图片生成 `thumb` 后列表 `thumbUrl` 可用 |
| 静态资源 | 生产环境 `/media/` 由 Nginx `alias` 直出（见 `docs/nginx-frontend.example.conf`） |
