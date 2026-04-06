"""
社区高频交互的异步/延后副作用（通知、积分等）。

- 优先通过 Celery `.delay()` 投递（worker 执行，缩短 API 写路径耗时）。
- 未安装 Celery 或未运行 worker 时：`shared_task` 退化为同步函数，由 `safe_task_delay` 在
  `transaction.on_commit` 后直接调用，仍保证「先提交主写入再执行副作用」。
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


def safe_task_delay(task, args=None, kwargs=None):
    """调用 Celery 任务：有 `.delay` 则异步，否则同步执行。"""
    args = args or ()
    kwargs = kwargs or {}
    delay = getattr(task, "delay", None)
    if callable(delay):
        return delay(*args, **kwargs)
    return task(*args, **kwargs)


@shared_task
def publish_like_created_task(user_id: int, target_type: str, target_id: int) -> None:
    from django.contrib.auth import get_user_model

    from notifications.events import publish_event

    User = get_user_model()
    user = User.objects.get(pk=user_id)
    publish_event(
        "like.created",
        user=user,
        target_type=target_type,
        target_id=target_id,
    )


@shared_task
def publish_comment_created_task(comment_id: int) -> None:
    from content.models import Comment
    from notifications.events import publish_event

    comment = Comment.objects.select_related("author", "content", "reply_to_user").get(
        pk=comment_id
    )
    publish_event("comment.created", comment=comment)


@shared_task
def apply_points_comment_task(
    user_id: int,
    event_type: str,
    source_type: str,
    source_id: int,
    reason: str,
) -> None:
    from django.contrib.auth import get_user_model

    from accounts.user_score_service import apply_points

    User = get_user_model()
    user = User.objects.get(pk=user_id)
    apply_points(
        user=user,
        event_type=event_type,
        source_type=source_type,
        source_id=source_id,
        reason=reason,
    )


@shared_task
def publish_follow_created_task(follower_id: int, followee_id: int) -> None:
    from django.contrib.auth import get_user_model

    from notifications.events import publish_event

    User = get_user_model()
    follower = User.objects.get(pk=follower_id)
    followee = User.objects.get(pk=followee_id)
    publish_event("follow.created", follower=follower, followee=followee, follow=None)


@shared_task
def publish_mention_created_task(
    from_user_id: int,
    to_user_id: int,
    source_type: str,
    source_id: int,
) -> None:
    from django.contrib.auth import get_user_model

    from notifications.events import publish_event

    User = get_user_model()
    from_user = User.objects.get(pk=from_user_id)
    to_user = User.objects.get(pk=to_user_id)
    publish_event(
        "mention.created",
        from_user=from_user,
        to_user=to_user,
        source_type=source_type,
        source_id=source_id,
    )


@shared_task
def apply_points_post_created_task(user_id: int, source_id: int) -> None:
    from django.contrib.auth import get_user_model

    from accounts.user_score_service import apply_points

    User = get_user_model()
    user = User.objects.get(pk=user_id)
    apply_points(
        user=user,
        event_type='POST_CREATED',
        source_type='POST',
        source_id=source_id,
        reason='发布内容积分',
    )


@shared_task
def write_follow_feed_post_published_task(actor_user_id: int, object_id: int) -> None:
    from django.contrib.auth import get_user_model

    from accounts.feed_service import write_follow_feed_for_actor

    User = get_user_model()
    actor = User.objects.get(pk=actor_user_id)
    write_follow_feed_for_actor(
        actor_user=actor,
        action_type='POST_PUBLISHED',
        object_type='POST',
        object_id=object_id,
    )
