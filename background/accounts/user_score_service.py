from __future__ import annotations

from django.db import transaction

from accounts.models import User, UserPointLog, LevelRule


DEFAULT_SCORE_RULES = {
    'POST_CREATED': 5,
    'COMMENT_CREATED': 2,
    'CONTENT_LIKED': 1,
    'CONTENT_REJECTED': -10,
    'MODERATION_PENALTY': -20,
}


def _resolve_level(points: int) -> int:
    rule = (
        LevelRule.objects.filter(is_active=True, min_points__lte=points, max_points__gte=points)
        .order_by('level')
        .first()
    )
    if rule:
        return rule.level
    if points < 100:
        return 1
    if points < 300:
        return 2
    if points < 600:
        return 3
    return 4


@transaction.atomic
def apply_points(
    *,
    user: User,
    event_type: str,
    delta: int | None = None,
    source_type: str = '',
    source_id: int | None = None,
    reason: str = '',
    operator: User | None = None,
) -> UserPointLog:
    final_delta = DEFAULT_SCORE_RULES.get(event_type, 0) if delta is None else delta
    user.points = (user.points or 0) + final_delta
    user.level = _resolve_level(user.points)
    user.save(update_fields=['points', 'level', 'updated_at'])
    return UserPointLog.objects.create(
        user=user,
        delta=final_delta,
        event_type=event_type,
        source_type=source_type,
        source_id=source_id,
        reason=reason,
        operator=operator,
    )
