from django.core.management.base import BaseCommand

from reports.analytics_service import refresh_topic_metrics


class Command(BaseCommand):
    help = '刷新热门话题日指标'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--top-n', type=int, default=50)

    def handle(self, *args, **options):
        refresh_topic_metrics(days=options['days'], top_n=options['top_n'])
        self.stdout.write(
            self.style.SUCCESS(f"话题指标刷新完成，days={options['days']} top_n={options['top_n']}")
        )
