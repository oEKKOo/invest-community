"""
Django 管理命令：数据同步入口
用法：
  # 同步美股标的清单
  python manage.py sync_market_data --task symbols --exchange US --market US

  # 同步 K 线（最近 365 天日 K，全量资产）
  python manage.py sync_market_data --task kline --days 365

  # 同步指定资产 K 线（回补）
  python manage.py sync_market_data --task kline --asset-ids 1 2 3 --days 30 --force

  # 刷新行情快照
  python manage.py sync_market_data --task quote

  # 数据质量校验
  python manage.py sync_market_data --task dq --days 30

  # 清理过期快照（保留 7 天）
  python manage.py sync_market_data --task cleanup --days 7

  # 查看 Finnhub Key 配置状态
  python manage.py sync_market_data --task status
"""
from django.core.management.base import BaseCommand, CommandError
from market_data import finnhub_service as fh


class Command(BaseCommand):
    help = '市场行情数据同步与维护工具'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            required=True,
            choices=['symbols', 'kline', 'quote', 'dq', 'cleanup', 'status'],
            help='任务类型: symbols(标的同步) kline(K线) quote(行情快照) dq(数据校验) cleanup(清理) status(状态)'
        )
        parser.add_argument('--exchange', type=str, default='US', help='Finnhub 交易所代码（symbols 任务用）')
        parser.add_argument('--market', type=str, default='US', help='内部市场标识（symbols 任务用）')
        parser.add_argument('--asset-ids', nargs='+', type=int, help='指定资产ID列表')
        parser.add_argument('--days', type=int, default=365, help='向前拉取天数 / 保留天数')
        parser.add_argument('--resolution', type=str, default='D', help='K线周期（kline 任务用）')
        parser.add_argument('--force', action='store_true', help='强制回补（kline 任务：删除后重拉）')

    def handle(self, *args, **options):
        task = options['task']

        # 状态检查
        if task == 'status':
            configured = fh.is_api_key_configured()
            self.stdout.write(
                self.style.SUCCESS('✅ FINNHUB_API_KEY 已配置') if configured
                else self.style.ERROR('❌ FINNHUB_API_KEY 未配置，请设置环境变量')
            )
            return

        # 所有同步任务都需要 Key
        if not fh.is_api_key_configured():
            raise CommandError('FINNHUB_API_KEY 未配置，请先设置环境变量')

        if task == 'symbols':
            from market_data.tasks import symbols_sync
            exchange = options['exchange']
            market = options['market']
            self.stdout.write(f'🔄 开始同步 {exchange} 标的清单（内部市场：{market}）...')
            job = symbols_sync(exchange=exchange, market=market)
            self._print_job_result(job)

        elif task == 'kline':
            from market_data.tasks import kline_sync
            asset_ids = options.get('asset_ids')
            days = options['days']
            resolution = options['resolution']
            force = options['force']
            desc = f'资产 {asset_ids}' if asset_ids else '全量资产'
            self.stdout.write(f'🔄 开始同步 K 线 [{resolution}]，{desc}，{days}天，force={force}...')
            job = kline_sync(
                asset_ids=asset_ids,
                resolution=resolution,
                days_back=days,
                force_refetch=force
            )
            self._print_job_result(job)

        elif task == 'quote':
            from market_data.tasks import quote_refresh
            asset_ids = options.get('asset_ids')
            desc = f'资产 {asset_ids}' if asset_ids else '全量资产'
            self.stdout.write(f'🔄 刷新行情快照，{desc}...')
            job = quote_refresh(asset_ids=asset_ids)
            self._print_job_result(job)

        elif task == 'dq':
            from market_data.tasks import dq_check
            asset_ids = options.get('asset_ids')
            days = options['days']
            self.stdout.write(f'🔍 执行数据质量校验，最近 {days} 天...')
            job = dq_check(asset_ids=asset_ids, days=days)
            self._print_job_result(job)
            # 打印发现的 issues
            if job.extra_info.get('issues'):
                self.stdout.write(self.style.WARNING(f'\n发现 {job.extra_info.get("total_issues", 0)} 个问题:'))
                for issue in job.extra_info['issues'][:20]:
                    self.stdout.write(f'  [{issue["type"]}] {issue["asset"]} @ {issue.get("k_time", "")}')

        elif task == 'cleanup':
            from market_data.tasks import cleanup_old_snapshots
            days = options['days']
            self.stdout.write(f'🗑️  清理 {days} 天前的快照...')
            deleted = cleanup_old_snapshots(days=days)
            self.stdout.write(self.style.SUCCESS(f'✅ 清理完成，共删除 {deleted} 条快照'))

    def _print_job_result(self, job):
        if job.status == 'SUCCESS':
            self.stdout.write(self.style.SUCCESS(
                f'✅ 任务完成 [ID={job.id}] status={job.status} rows={job.affected_rows}'
            ))
        elif job.status == 'PARTIAL':
            self.stdout.write(self.style.WARNING(
                f'⚠️  任务部分成功 [ID={job.id}] rows={job.affected_rows} '
                f'failed={len(job.extra_info.get("failed_assets", []))}'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'❌ 任务失败 [ID={job.id}] error={job.error_message}'
            ))
