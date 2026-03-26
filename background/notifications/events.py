from __future__ import annotations

"""
轻量级领域事件总线，用于把「业务动作」与「通知创建」解耦。

用法约定：
1）业务侧在合适的位置调用 publish_event(...)
   - like.created       → 点赞成功
   - comment.created    → 评论创建成功
   - follow.created     → 关注成功
   - content.reviewed   → 管理员审核帖子

2）本模块内部订阅这些事件并创建 Notification 记录
   后续如需扩展（积分、审计日志、推荐特征等），只需在这里增加订阅处理器。
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from django.utils import timezone

from .models import Notification


@dataclass
class DomainEvent:
    """简单领域事件载体"""

    name: str
    payload: Dict[str, Any]
    created_at: Any


_subscribers: Dict[str, List[Callable[[DomainEvent], None]]] = {}


def subscribe(event_name: str, handler: Callable[[DomainEvent], None]) -> None:
    """注册事件订阅者"""
    handlers = _subscribers.setdefault(event_name, [])
    handlers.append(handler)


def publish_event(event_name: str, **payload: Any) -> None:
    """
    发布领域事件（当前为同步分发，体量不大，便于调试。
    后续如需异步，可在这里接入 Celery / 消息队列。）
    """
    if event_name not in _subscribers:
        return

    event = DomainEvent(name=event_name, payload=payload, created_at=timezone.now())
    for handler in list(_subscribers.get(event_name, [])):
        try:
            handler(event)
        except Exception:
            # 为了不影响主业务流程，这里吞掉异常，后续可接入 sentry / 日志。
            # 日志在 handler 内部各自按需要记录。
            continue


# ─────────────────────────────────────────────────────────────
# 事件处理器：将领域事件映射为 Notification 记录
# ─────────────────────────────────────────────────────────────


def _handle_like_created(event: DomainEvent) -> None:
    """
    点赞成功 → 通知被点赞对象的所有者：
    - 点赞帖子   → 通知帖子作者
    - 点赞评论   → 通知评论作者
    - 点赞组合   → 通知组合创建者
    """
    user = event.payload.get("user")  # 点赞人
    target_type = event.payload.get("target_type")
    target_id = event.payload.get("target_id")

    if not user or not target_type or not target_id:
        return

    # 避免循环依赖，延迟导入
    from content.models import Content, Comment  # type: ignore
    from portfolios.models import Portfolio  # type: ignore

    receiver = None
    title = ""
    content = ""
    related_type = ""
    related_id: int | None = None

    if target_type == "POST":
        try:
            post = Content.objects.select_related("author").get(id=target_id)
        except Content.DoesNotExist:
            return
        receiver = post.author
        related_type = "POST"
        related_id = post.id
        title = "有人点赞了你的帖子"
        content = f'用户「{getattr(user, "display_name", user.username)}」点赞了你的帖子《{post.title}》。'
    elif target_type == "COMMENT":
        try:
            comment = Comment.objects.select_related("author", "content").get(id=target_id)
        except Comment.DoesNotExist:
            return
        receiver = comment.author
        related_type = "COMMENT"
        related_id = comment.id
        snippet = comment.body[:50]
        title = "有人点赞了你的评论"
        content = f'用户「{getattr(user, "display_name", user.username)}」点赞了你在《{comment.content.title}》下的评论：“{snippet}”。'
    elif target_type == "PORTFOLIO":
        try:
            portfolio = Portfolio.objects.select_related("owner").get(id=target_id)
        except Portfolio.DoesNotExist:
            return
        receiver = portfolio.owner
        related_type = "PORTFOLIO"
        related_id = portfolio.id
        title = "有人点赞了你的组合"
        content = f'用户「{getattr(user, "display_name", user.username)}」点赞了你的投资组合《{portfolio.title}》。'

    if receiver is None or receiver == user:
        # 不给自己发点赞通知
        return

    Notification.objects.create(
        user=receiver,
        notification_type="LIKE",
        title=title,
        content=content,
        related_object_type=related_type,
        related_object_id=related_id,
    )


def _handle_comment_created(event: DomainEvent) -> None:
    """
    评论创建 → 通知帖子作者 & 被回复用户（若有）
    """
    comment = event.payload.get("comment")
    if comment is None:
        return

    author = getattr(comment, "author", None)
    content_obj = getattr(comment, "content", None)
    if not author or not content_obj:
        return

    # 1）通知帖子作者
    post_author = getattr(content_obj, "author", None)
    if post_author and post_author != author:
        Notification.objects.create(
            user=post_author,
            notification_type="COMMENT",
            title="有人评论了你的帖子",
            content=(
                f'用户「{getattr(author, "display_name", author.username)}」'
                f'在你的帖子《{content_obj.title}》下发表了评论：“{comment.body[:80]}”。'
            ),
            related_object_type="POST",
            related_object_id=content_obj.id,
        )

    # 2）如果是回复某个用户，再额外通知被回复用户
    reply_to_user = getattr(comment, "reply_to_user", None)
    if reply_to_user and reply_to_user not in (author, post_author):
        Notification.objects.create(
            user=reply_to_user,
            notification_type="COMMENT",
            title="有人回复了你",
            content=(
                f'用户「{getattr(author, "display_name", author.username)}」'
                f'回复了你在《{content_obj.title}》下的评论：“{comment.body[:80]}”。'
            ),
            related_object_type="COMMENT",
            related_object_id=getattr(comment, "parent_id", None) or comment.id,
        )


def _handle_follow_created(event: DomainEvent) -> None:
    """
    关注成功 → 通知被关注用户
    """
    follower = event.payload.get("follower")
    followee = event.payload.get("followee")

    if not follower or not followee or follower == followee:
        return

    Notification.objects.create(
        user=followee,
        notification_type="FOLLOW",
        title="有人关注了你",
        content=f'用户「{getattr(follower, "display_name", follower.username)}」关注了你。',
        related_object_type="USER",
        related_object_id=getattr(follower, "id", None),
    )


def _handle_content_reviewed(event: DomainEvent) -> None:
    """
    帖子审核结果 → 通知作者
    """
    content_obj = event.payload.get("content")
    new_status = event.payload.get("new_status")
    reject_reason = event.payload.get("reject_reason", "")

    if not content_obj or not new_status:
        return

    author = getattr(content_obj, "author", None)
    if not author:
        return

    if new_status == "PUBLISHED":
        title = "你的帖子已通过审核"
        msg = f'你的帖子《{content_obj.title}》已通过审核并发布。'
    elif new_status == "REJECTED":
        title = "你的帖子未通过审核"
        base = f'你的帖子《{content_obj.title}》未通过审核。'
        if reject_reason:
            msg = f"{base} 原因：{reject_reason}"
        else:
            msg = base
    elif new_status == "TAKEN_DOWN":
        title = "你的帖子已被下架"
        msg = f'你的帖子《{content_obj.title}》已被管理员下架。'
    else:
        return

    Notification.objects.create(
        user=author,
        notification_type="REVIEW_RESULT",
        title=title,
        content=msg,
        related_object_type="POST",
        related_object_id=getattr(content_obj, "id", None),
    )


# 注册订阅关系
subscribe("like.created", _handle_like_created)
subscribe("comment.created", _handle_comment_created)
subscribe("follow.created", _handle_follow_created)
subscribe("content.reviewed", _handle_content_reviewed)


def _handle_mention_created(event: DomainEvent) -> None:
    from_user = event.payload.get("from_user")
    to_user = event.payload.get("to_user")
    source_type = event.payload.get("source_type")
    source_id = event.payload.get("source_id")
    if not from_user or not to_user or from_user == to_user:
        return
    Notification.objects.create(
        user=to_user,
        notification_type="MENTION",
        title="有人提及了你",
        content=f'用户「{getattr(from_user, "display_name", from_user.username)}」在{source_type}中提及了你。',
        related_object_type=source_type,
        related_object_id=source_id,
    )


def _handle_poll_voted(event: DomainEvent) -> None:
    poll = event.payload.get("poll")
    user = event.payload.get("user")
    content = event.payload.get("content")
    if not poll or not user or not content:
        return
    author = getattr(content, "author", None)
    if not author or author == user:
        return
    Notification.objects.create(
        user=author,
        notification_type="POLL_VOTED",
        title="你的投票有新参与",
        content=f'用户「{getattr(user, "display_name", user.username)}」参与了你的投票《{content.title}》。',
        related_object_type="POST",
        related_object_id=getattr(content, "id", None),
    )


def _handle_attachment_reviewed(event: DomainEvent) -> None:
    attachment = event.payload.get("attachment")
    new_status = event.payload.get("new_status")
    if not attachment or not new_status:
        return
    uploader = getattr(attachment, "uploaded_by", None)
    if not uploader:
        return
    title = "附件审核结果更新"
    if new_status == "APPROVED":
        msg = f'你上传的附件「{attachment.original_name}」已通过审核。'
    else:
        reason = attachment.reject_reason or "请修改后重新上传"
        msg = f'你上传的附件「{attachment.original_name}」未通过审核。原因：{reason}'
    Notification.objects.create(
        user=uploader,
        notification_type="ATTACHMENT_REVIEWED",
        title=title,
        content=msg,
        related_object_type="ATTACHMENT",
        related_object_id=getattr(attachment, "id", None),
    )


subscribe("mention.created", _handle_mention_created)
subscribe("poll.voted", _handle_poll_voted)
subscribe("attachment.reviewed", _handle_attachment_reviewed)

