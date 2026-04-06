"""
Celery 任务封装（可选依赖 celery）。

业务实现仍位于 `market_data.tasks`；此处仅提供 @shared_task 入口供 worker/beat 调用。
未安装 celery 时本模块不参与加载（由 autodiscover 跳过）。
"""
from __future__ import annotations

try:
    from celery import shared_task  # type: ignore
except ImportError:

    def shared_task(f=None, **_kw):  # type: ignore
        if callable(f):
            return f

        def _decorator(fn):
            return fn

        return _decorator


@shared_task
def quote_refresh_popular_task():
    from .tasks import quote_refresh_popular

    job = quote_refresh_popular()
    return job.id if job else None


@shared_task
def kline_sync_daily_task():
    from .tasks import kline_sync

    job = kline_sync(resolution='D', days_back=365)
    return job.id if job else None


@shared_task
def cleanup_quote_snapshots_task():
    from .tasks import cleanup_old_snapshots

    return cleanup_old_snapshots(days=7)


@shared_task
def fill_holding_snapshots_task():
    from django.core.management import call_command

    call_command('fill_holding_snapshots', '--days', '365')
    return 'ok'
