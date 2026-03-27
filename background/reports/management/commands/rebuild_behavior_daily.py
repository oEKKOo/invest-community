from django.core.management.base import BaseCommand

from reports.analytics_service import rebuild_behavior_daily


class Command(BaseCommand):
    help = '重建用户行为日聚合统计'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)

    def handle(self, *args, **options):
        days = options['days']
        rebuild_behavior_daily(days=days)
        self.stdout.write(self.style.SUCCESS(f'用户行为日聚合重建完成，days={days}'))
