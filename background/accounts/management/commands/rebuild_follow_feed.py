from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accounts.models import FollowFeedItem
from accounts.feed_service import write_follow_feed_for_actor
from content.models import Content
from portfolios.models import Portfolio

User = get_user_model()


class Command(BaseCommand):
    help = '回填关注动态表 follow_feed_item'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('开始回填 follow_feed_item ...'))
        FollowFeedItem.objects.all().delete()

        created_total = 0
        for post in Content.objects.filter(status='PUBLISHED').select_related('author').iterator():
            created_total += write_follow_feed_for_actor(
                actor_user=post.author,
                action_type='POST_PUBLISHED',
                object_type='POST',
                object_id=post.id,
            )

        for portfolio in Portfolio.objects.filter(is_public=True).select_related('owner').iterator():
            created_total += write_follow_feed_for_actor(
                actor_user=portfolio.owner,
                action_type='PORTFOLIO_PUBLISHED',
                object_type='PORTFOLIO',
                object_id=portfolio.id,
            )

        self.stdout.write(self.style.SUCCESS(f'回填完成，共写入 {created_total} 条 feed 记录'))
