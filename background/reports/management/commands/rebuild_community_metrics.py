from django.core.management.base import BaseCommand

from reports.analytics_service import rebuild_community_metrics


class Command(BaseCommand):
    help = '重建社区日指标统计'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)

    def handle(self, *args, **options):
        days = options['days']
        rebuild_community_metrics(days=days)
        self.stdout.write(self.style.SUCCESS(f'社区日指标重建完成，days={days}'))
