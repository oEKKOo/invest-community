"""
无 Celery 时的日终维护入口（适合 crontab）：

  python manage.py run_daily_market_jobs

等价于 Beat 中 market-kline-sync-daily + portfolios-fill-holding-snapshots
+ market-cleanup-quote-snapshots 的组合（不含每 2 分钟的热门行情刷新；
热门行情请单独定时：python manage.py sync_market_data --task quote --limit 0
或调用 API 触发 QUOTE_REFRESH_POPULAR）。
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from market_data.tasks import cleanup_old_snapshots, kline_sync


class Command(BaseCommand):
    help = '日终：日线 K 线同步 + 持仓快照补缺 + 清理过期行情快照'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=365, help='K 线回溯天数与持仓快照回补天数')
        parser.add_argument('--cleanup-days', type=int, default=7, help='行情快照保留天数')

    def handle(self, *args, **options):
        days = options['days']
        cleanup_days = options['cleanup_days']

        self.stdout.write(f'[1/3] kline_sync resolution=D days_back={days}...')
        job = kline_sync(resolution='D', days_back=days)
        self.stdout.write(f'      job id={getattr(job, "id", None)} status={getattr(job, "status", None)}')

        self.stdout.write('[2/3] fill_holding_snapshots...')
        call_command('fill_holding_snapshots', '--days', str(days))

        self.stdout.write(f'[3/3] cleanup_old_snapshots({cleanup_days}d)...')
        n = cleanup_old_snapshots(days=cleanup_days)
        self.stdout.write(f'      deleted_rows≈{n}')

        self.stdout.write(self.style.SUCCESS('run_daily_market_jobs 完成'))
