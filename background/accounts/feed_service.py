from django.contrib.auth import get_user_model

from accounts.models import FollowFeedItem, UserFollow, UserStarFollow

User = get_user_model()


def write_follow_feed_for_actor(*, actor_user, action_type: str, object_type: str, object_id: int) -> int:
    """
    将某个行为写入其粉丝的关注流（幂等）。
    返回新写入条数。
    """
    follower_ids = list(
        UserFollow.objects.filter(followee=actor_user).values_list('follower_id', flat=True)
    )
    if not follower_ids:
        return 0

    star_user_ids = set(
        UserStarFollow.objects.filter(
            user_id__in=follower_ids,
            follow_user=actor_user,
        ).values_list('user_id', flat=True)
    )

    created_count = 0
    for follower_id in follower_ids:
        _, created = FollowFeedItem.objects.get_or_create(
            user_id=follower_id,
            action_type=action_type,
            object_type=object_type,
            object_id=object_id,
            defaults={
                'actor_user_id': actor_user.id,
                'is_star_actor': follower_id in star_user_ids,
                'score': 1,
            },
        )
        if created:
            created_count += 1
    return created_count
