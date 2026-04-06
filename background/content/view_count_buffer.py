"""
帖子浏览量缓冲：USE_REDIS + VIEW_COUNT_USE_REDIS_BUFFER 时先写 Redis，周期性回写 MySQL。

键空间使用原生 Redis 命令（与 Django Cache 键前缀独立），避免与 cache.incr 混淆。
"""
from __future__ import annotations

import logging
from django.conf import settings
from django.db.models import F

logger = logging.getLogger(__name__)

# Redis 键（不含 django-redis 的 KEY_PREFIX；使用独立前缀便于 SCAN/运维）
VC_KEY = 'invest:vcbuf:{id}'
VC_PENDING = 'invest:vcbuf:pending'


def _use_redis_buffer() -> bool:
    # settings.VIEW_COUNT_USE_REDIS_BUFFER 已在 settings 中与 USE_REDIS 联动
    return bool(getattr(settings, 'VIEW_COUNT_USE_REDIS_BUFFER', False))


def _client():
    from django_redis import get_redis_connection

    return get_redis_connection('default')


def record_content_view(content_id: int) -> None:
    """记录一次浏览：缓冲模式下 INCR Redis；否则直接 UPDATE MySQL。"""
    from .models import Content

    if not _use_redis_buffer():
        Content.objects.filter(pk=content_id).update(view_count=F('view_count') + 1)
        return

    try:
        r = _client()
        key = VC_KEY.format(id=content_id)
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.sadd(VC_PENDING, str(content_id))
        pipe.execute()
    except Exception as exc:
        logger.warning('view_count buffer incr failed, fallback to DB: %s', exc)
        Content.objects.filter(pk=content_id).update(view_count=F('view_count') + 1)


def _pending_delta(content_id: int) -> int:
    if not _use_redis_buffer():
        return 0
    try:
        r = _client()
        raw = r.get(VC_KEY.format(id=content_id))
        if raw is None:
            return 0
        return int(raw)
    except Exception:
        return 0


def get_display_view_count(content_id: int, db_view_count: int) -> int:
    """展示用浏览量 = 库内值 + Redis 中尚未回写的增量。"""
    return int(db_view_count) + _pending_delta(content_id)


def flush_content_view_deltas() -> int:
    """
    将 Redis 中的浏览增量合并回 content.view_count，并清理对应键。
    返回成功合并的帖子数量（至少执行过一次 UPDATE 的 id 数）。
    """
    from .models import Content

    if not _use_redis_buffer():
        return 0

    try:
        r = _client()
    except Exception as exc:
        logger.error('flush view buffer: no redis: %s', exc)
        return 0

    ids_raw = r.smembers(VC_PENDING)
    if not ids_raw:
        return 0

    merged = 0
    for sid in ids_raw:
        try:
            cid = int(sid)
        except (TypeError, ValueError):
            continue
        key = VC_KEY.format(id=cid)
        try:
            raw = r.get(key)
            delta = int(raw) if raw is not None else 0
        except (TypeError, ValueError):
            delta = 0

        if delta > 0:
            updated = Content.objects.filter(pk=cid).update(
                view_count=F('view_count') + delta
            )
            if updated:
                merged += 1

        try:
            pipe = r.pipeline()
            pipe.delete(key)
            pipe.srem(VC_PENDING, str(cid))
            pipe.execute()
        except Exception as exc:
            logger.warning('flush view buffer cleanup failed for %s: %s', cid, exc)

    return merged
