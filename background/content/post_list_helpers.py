"""帖子列表接口：批量查询互动状态与转发数，避免 N+1。"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Set

from django.db.models import Count

from .models import Comment, Favorite, Like, Repost


def build_post_card_context(request, post_ids: Sequence[int | None]) -> Dict[str, Any]:
    """
    为 ContentCardSerializer / ContentListSerializer 列表提供：
    - liked_post_ids / favorited_post_ids（登录用户）
    - repost_counts: content_id -> int（与 ContentMeta.repost_count 一致时优先用 meta）
    """
    ids: List[int] = sorted({int(i) for i in post_ids if i is not None})
    ctx: Dict[str, Any] = {
        'request': request,
        'liked_post_ids': set(),
        'favorited_post_ids': set(),
        'repost_counts': {},
    }
    if not ids:
        return ctx

    repost_rows = (
        Repost.objects.filter(content_id__in=ids)
        .values('content_id')
        .annotate(c=Count('id'))
    )
    ctx['repost_counts'] = {row['content_id']: row['c'] for row in repost_rows}

    user = request.user
    if user.is_authenticated:
        ctx['liked_post_ids'] = set(
            Like.objects.filter(
                user=user, target_type='POST', target_id__in=ids
            ).values_list('target_id', flat=True)
        )
        ctx['favorited_post_ids'] = set(
            Favorite.objects.filter(user=user, content_id__in=ids).values_list(
                'content_id', flat=True
            )
        )
    return ctx


def build_comment_like_context(request, comment_ids: Iterable[int | None]) -> Dict[str, Any]:
    ids = sorted({int(i) for i in comment_ids if i is not None})
    ctx: Dict[str, Any] = {'request': request, 'liked_comment_ids': set()}
    if not ids or not request.user.is_authenticated:
        return ctx
    ctx['liked_comment_ids'] = set(
        Like.objects.filter(
            user=request.user, target_type='COMMENT', target_id__in=ids
        ).values_list('target_id', flat=True)
    )
    return ctx


def prefetch_reply_previews_for_comments(
    top_comments: Sequence[Comment], per_parent: int = 5
) -> Dict[int, List[Comment]]:
    """批量加载每条顶级评论的前 per_parent 条回复（按创建时间）。"""
    parent_ids = [c.id for c in top_comments]
    if not parent_ids:
        return {}
    from collections import defaultdict

    rows = (
        Comment.objects.filter(parent_id__in=parent_ids, status='NORMAL')
        .select_related('author', 'reply_to_user')
        .prefetch_related('attachments')
        .order_by('parent_id', 'created_at', 'id')
    )
    buckets: Dict[int, List[Comment]] = defaultdict(list)
    for r in rows:
        bid = r.parent_id
        if bid is None:
            continue
        if len(buckets[bid]) < per_parent:
            buckets[bid].append(r)
    return dict(buckets)
