from django.core.management.base import BaseCommand

from content.view_count_buffer import flush_content_view_deltas


class Command(BaseCommand):
    help = '将 Redis 中缓冲的帖子浏览量增量合并回 MySQL（需 USE_REDIS + VIEW_COUNT_USE_REDIS_BUFFER）'

    def handle(self, *args, **options):
        n = flush_content_view_deltas()
        self.stdout.write(self.style.SUCCESS(f'已合并 {n} 条内容的浏览增量'))
