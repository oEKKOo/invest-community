"""
管理命令：fill_holding_snapshots
从 AssetKline 日K数据为所有用户持仓生成每日价格快照（SQL 批量补缺模式）。

性能优化说明（对比旧版）：
  旧版：Python for 循环，每个持仓单独查询 existing_dates + 逐条写入
        → N 次 SELECT + N*M 次 ORM 写入，5500 资产 × 365 天 = 数百万次 IO
  新版：一条 INSERT IGNORE INTO ... SELECT 完成全量补缺
        → 1 次 SQL，利用 UNIQUE(holding_id, date) 约束跳过已有记录
        → 速度提升 10~100 倍（通常几秒内完成）

使用方法：
  python manage.py fill_holding_snapshots
  python manage.py fill_holding_snapshots --days 365
  python manage.py fill_holding_snapshots --user-id 1
  python manage.py fill_holding_snapshots --force        # 先删除再重建
  python manage.py fill_holding_snapshots --holding-id 5  # 单持仓调试
"""
import datetime
import time

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from portfolios.models import HoldingDailySnapshot, UserHolding


class Command(BaseCommand):
    help = '从 AssetKline 日K数据为持仓生成每日快照（SQL 批量补缺，不重复写入）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=365,
            help='回补多少天的 K 线数据（默认 365）'
        )
        parser.add_argument(
            '--user-id', type=int, dest='user_id', default=None,
            help='只处理指定用户的持仓（调试用）'
        )
        parser.add_argument(
            '--holding-id', type=int, dest='holding_id', default=None,
            help='只处理单条持仓记录（调试用）'
        )
        parser.add_argument(
            '--force', action='store_true', default=False,
            help='强制重建：先删除 cutoff 日期之后的快照再重新生成'
        )

    def handle(self, *args, **options):
        days        = options['days']
        user_id     = options.get('user_id')
        holding_id  = options.get('holding_id')
        force       = options['force']

        cutoff_date = timezone.now().date() - datetime.timedelta(days=days)
        self.stdout.write(f'📅 回补范围：{cutoff_date} ~ 今天，force={force}')

        # ── 0. 统计待处理持仓数（用于日志） ────────────────────────────────────
        qs = UserHolding.objects.all()
        if holding_id:
            qs = qs.filter(pk=holding_id)
        elif user_id:
            qs = qs.filter(user_id=user_id)
        total_holdings = qs.count()
        self.stdout.write(f'📦 待处理持仓数：{total_holdings}')

        if total_holdings == 0:
            self.stdout.write(self.style.WARNING('⚠️  无持仓记录，退出'))
            return

        # ── 1. force 模式：先批量删除旧快照 ────────────────────────────────────
        if force:
            del_qs = HoldingDailySnapshot.objects.filter(date__gte=cutoff_date)
            if holding_id:
                del_qs = del_qs.filter(holding_id=holding_id)
            elif user_id:
                del_qs = del_qs.filter(holding__user_id=user_id)
            deleted_count, _ = del_qs.delete()
            self.stdout.write(f'  🗑️  已删除旧快照 {deleted_count} 条')

        # ── 2. SQL INSERT IGNORE INTO ... SELECT 批量补缺 ───────────────────────
        #
        # 原理：
        #   JOIN user_holding × asset_kline（同 asset_id，日K，cutoff 之后）
        #   → 直接生成 (holding_id, date, close_price) 三元组
        #   → INSERT IGNORE 利用 UNIQUE(holding_id, date) 跳过已有记录
        #
        # 与旧 Python 循环等价，但：
        #   - 零 Python 层 IO：DB 内部完成 JOIN + 去重
        #   - 零 Python 层循环：无 for holding in qs、for kline in klines
        #   - 事务次数：1 次（整个 INSERT 一个事务）
        #
        where_parts = [
            "ak.resolution = %s",
            "DATE(ak.k_time) >= %s",   # 使用 DATE() 保证跨时区语义一致
        ]
        params = ['D', str(cutoff_date)]

        if holding_id:
            where_parts.append("uh.id = %s")
            params.append(holding_id)
        elif user_id:
            where_parts.append("uh.user_id = %s")
            params.append(user_id)

        where_sql = "\n            AND ".join(where_parts)

        sql = f"""
            INSERT IGNORE INTO holding_daily_snapshot
                (holding_id, date, close_price, created_at)
            SELECT
                uh.id          AS holding_id,
                DATE(ak.k_time) AS date,
                ak.close       AS close_price,
                NOW()          AS created_at
            FROM user_holding uh
            INNER JOIN asset_kline ak
                ON  ak.asset_id  = uh.asset_id
            WHERE
                {where_sql}
        """

        self.stdout.write('⚡ 执行 SQL 批量补缺（INSERT IGNORE INTO ... SELECT）...')
        t0 = time.perf_counter()

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            inserted = cursor.rowcount   # MySQL：实际插入行数（跳过已有记录）

        elapsed = time.perf_counter() - t0

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'🎉 完成！新增 {inserted} 条快照 | 耗时 {elapsed:.2f}s'
        ))
        self.stdout.write('')
        self.stdout.write(
            '提示：后续可在服务启动时自动调用此命令（补缺模式），'
            '或写进定时任务（每日收盘后执行）。'
        )
