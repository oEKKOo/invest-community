"""
Django 管理命令：从 Tushare 批量导入 A 股到数据库，并可立即同步日线 K 线和行情快照

用法：
  # 导入全部上市 A 股（约 5000 只）
  python manage.py import_cn_stocks

  # 只导入上交所股票
  python manage.py import_cn_stocks --exchange SSE

  # 导入后立即同步最近 365 天日线 K 线
  python manage.py import_cn_stocks --kline --days 365

  # 导入后立即刷新行情快照
  python manage.py import_cn_stocks --quote

  # 导入指定状态（L=上市 D=退市 P=暂停）
  python manage.py import_cn_stocks --list-status L

  # 只同步 K 线（不重新导入，对已有资产同步）
  python manage.py import_cn_stocks --kline-only --days 30

  # 只刷新行情快照（不重新导入）
  python manage.py import_cn_stocks --quote-only

  # 指定资产代码列表（逗号分隔）
  python manage.py import_cn_stocks --codes 600519,000001,000002 --kline
"""
import time
import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as dj_tz

logger = logging.getLogger(__name__)

# 重点 A 股（沪深300 + 知名个股）—— 导入时排序优先，行情刷新时优先覆盖
PRIORITY_CN_CODES = {
    # 沪市蓝筹
    '600519',  # 贵州茅台
    '601318',  # 中国平安
    '600036',  # 招商银行
    '601166',  # 兴业银行
    '600276',  # 恒瑞医药
    '600887',  # 伊利股份
    '601888',  # 中国中免
    '600900',  # 长江电力
    '603288',  # 海天味业
    '601012',  # 隆基绿能
    # 深市蓝筹
    '000858',  # 五粮液
    '000651',  # 格力电器
    '000333',  # 美的集团
    '002415',  # 海康威视
    '000001',  # 平安银行
    '300750',  # 宁德时代
    '002594',  # 比亚迪
    '300059',  # 东方财富
    '000002',  # 万科A
    '002230',  # 科大讯飞
    # 宽基指数 ETF（按代码导入时可用）
    '510300',  # 沪深300ETF
    '510500',  # 中证500ETF
    '159919',  # 沪深300ETF(嘉实)
    '588000',  # 科创50ETF
}


class Command(BaseCommand):
    help = '从 Tushare Pro 批量导入 A 股资产，并可同步日线 K 线和行情快照'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list-status',
            type=str,
            default='L',
            dest='list_status',
            choices=['L', 'D', 'P'],
            help='股票状态：L(上市，默认) D(退市) P(暂停上市)',
        )
        parser.add_argument(
            '--exchange',
            type=str,
            default='',
            help='只导入指定交易所：SSE(上交所) SZSE(深交所) BSE(北交所)，不传则全市场',
        )
        parser.add_argument(
            '--codes',
            type=str,
            default='',
            help='只导入指定股票代码（逗号分隔，如 600519,000001）',
        )
        parser.add_argument(
            '--kline',
            action='store_true',
            help='导入后立即同步日线 K 线',
        )
        parser.add_argument(
            '--quote',
            action='store_true',
            help='导入后立即刷新行情快照',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='K 线同步天数（--kline 时有效），默认 365 天',
        )
        parser.add_argument(
            '--kline-only',
            action='store_true',
            dest='kline_only',
            help='不重新导入，只对已有 A 股资产同步 K 线',
        )
        parser.add_argument(
            '--quote-only',
            action='store_true',
            dest='quote_only',
            help='不重新导入，只对已有 A 股资产刷新行情快照',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='K 线同步时强制回补（删除后重拉）',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='每次 Tushare API 请求之间的延迟（秒），默认 0.5',
        )

    def handle(self, *args, **options):
        from market_data import tushare_service as ts_svc

        if not ts_svc.is_api_token_configured():
            raise CommandError(
                'TUSHARE_API_TOKEN 未配置！\n'
                '请在 D:\\invest\\background\\.env 中添加：\n'
                '  TUSHARE_API_TOKEN=your_token_here'
            )

        list_status = options['list_status']
        exchange_filter = options['exchange'].strip()
        codes_filter = [c.strip() for c in options['codes'].split(',') if c.strip()]
        do_kline = options['kline']
        do_quote = options['quote']
        days = options['days']
        kline_only = options['kline_only']
        quote_only = options['quote_only']
        force = options['force']
        delay = options['delay']

        # ── 仅同步 K 线模式 ────────────────────────────────────────────────
        if kline_only:
            self._sync_klines_for_existing(days, force, delay)
            return

        # ── 仅刷新行情模式 ────────────────────────────────────────────────
        if quote_only:
            self._refresh_quotes_for_existing(delay)
            return

        # ── Step 1: 从 Tushare 拉取 A 股列表 ─────────────────────────────
        self.stdout.write(f'[1/3] 从 Tushare 拉取 A 股列表（list_status={list_status}）...')
        stocks = ts_svc.get_stock_basic(list_status=list_status)

        if not stocks:
            raise CommandError('无法从 Tushare 获取股票列表，请检查 Token 和网络')

        self.stdout.write(f'      Tushare 返回 {len(stocks)} 只股票')

        # ── Step 2: 过滤 ──────────────────────────────────────────────────
        if exchange_filter:
            # Tushare exchange 字段: SSE / SZSE / BSE
            stocks = [s for s in stocks if s.get('exchange', '') == exchange_filter]
            self.stdout.write(f'      过滤 exchange="{exchange_filter}" 后剩余 {len(stocks)} 只')

        if codes_filter:
            codes_set = set(codes_filter)
            stocks = [s for s in stocks if s.get('code', '') in codes_set]
            self.stdout.write(f'      过滤指定代码后剩余 {len(stocks)} 只')

        # 优先重点股票排在前面
        stocks.sort(key=lambda s: (0 if s.get('code', '') in PRIORITY_CN_CODES else 1,
                                   s.get('code', '')))

        # ── Step 3: 写入数据库 ────────────────────────────────────────────
        self.stdout.write(f'\n[2/3] 写入数据库（共 {len(stocks)} 只）...')
        created_count = 0
        updated_count = 0
        error_count = 0
        asset_objs = []

        from content.models import Asset

        exchange_display_map = {'SSE': 'SH', 'SZSE': 'SZ', 'BSE': 'BJ'}

        for i, s in enumerate(stocks, 1):
            code     = s.get('code', '')
            market   = s.get('market', '')  # SH / SZ / BJ
            name     = s.get('name', '').strip() or code
            industry = s.get('industry', '')
            ts_code  = s.get('ts_code', '')
            raw_exchange = s.get('exchange', '')
            exchange = exchange_display_map.get(raw_exchange, raw_exchange)

            if not code or market not in ts_svc.CN_MARKETS:
                continue

            try:
                # 注意：数据库有 uk_asset_type_code 约束，仅覆盖 (asset_type, code)，
                # 不含 market。因此以 (code, asset_type) 为查找键，把 market 放进
                # defaults，这样旧记录（如 market='CN'）也能被正确更新为 SH/SZ/BJ。
                obj, created = Asset.objects.update_or_create(
                    code=code,
                    asset_type='STOCK',
                    defaults={
                        'name':         name,
                        'market':       market,   # 修正旧的 market='CN' → SH/SZ/BJ
                        'currency':     'CNY',
                        'exchange':     exchange,
                        'industry':     industry,
                        'status':       'ACTIVE',
                        'meta_json':    {
                            'tushare_code': ts_code,
                            'area':        s.get('area', ''),
                            'list_date':   s.get('list_date', ''),
                        },
                        'last_sync_at': dj_tz.now(),
                    }
                )
                asset_objs.append(obj)
                if created:
                    created_count += 1
                else:
                    updated_count += 1

                if i % 200 == 0 or i == len(stocks):
                    self.stdout.write(
                        f'  进度 {i}/{len(stocks)}  '
                        f'新增={created_count}  更新={updated_count}  错误={error_count}'
                    )

            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    self.stdout.write(self.style.WARNING(f'  [WARN] {code}: {e}'))
                logger.warning('[import_cn_stocks] 写入失败: code=%s err=%s', code, str(e))

        self.stdout.write(self.style.SUCCESS(
            f'\n[2/3] 完成！新增 {created_count} 只，更新 {updated_count} 只，'
            f'错误 {error_count} 只，共 {len(asset_objs)} 只 A 股已入库'
        ))

        # ── Step 4: 同步 K 线（可选）────────────────────────────────────
        if do_kline:
            self._sync_klines_for_assets(asset_objs, days, force, delay)

        # ── Step 5: 刷新行情（可选）─────────────────────────────────────
        if do_quote:
            self._refresh_quotes_for_assets(asset_objs, delay)

        if not do_kline and not do_quote:
            self.stdout.write('')
            self.stdout.write('[TIP] 导入完成后可运行以下命令同步 K 线和行情：')
            self.stdout.write('  python manage.py import_cn_stocks --kline-only --days 365')
            self.stdout.write('  python manage.py import_cn_stocks --quote-only')
            self.stdout.write('  python manage.py sync_cn_data --task kline --days 365')

    # ── 内部方法 ──────────────────────────────────────────────────────────────

    def _sync_klines_for_existing(self, days: int, force: bool, delay: float):
        """对已有 A 股资产同步日线 K 线（kline-only 模式）"""
        from content.models import Asset
        from market_data.tushare_service import CN_MARKETS

        assets = list(Asset.objects.filter(
            market__in=list(CN_MARKETS), status='ACTIVE'
        ))
        self.stdout.write(f'[kline-only] 对 {len(assets)} 只 A 股资产同步 K 线...')
        self._sync_klines_for_assets(assets, days, force, delay)

    def _refresh_quotes_for_existing(self, delay: float):
        """对已有 A 股资产刷新行情快照（quote-only 模式）"""
        from content.models import Asset
        from market_data.tushare_service import CN_MARKETS

        assets = list(Asset.objects.filter(
            market__in=list(CN_MARKETS), status='ACTIVE'
        ))
        self.stdout.write(f'[quote-only] 对 {len(assets)} 只 A 股资产刷新行情...')
        self._refresh_quotes_for_assets(assets, delay)

    def _sync_klines_for_assets(self, asset_objs: list, days: int, force: bool, delay: float):
        """
        批量同步日线 K 线（按日期批量拉取，彻底取消逐股 API 调用）。

        核心优化：
          旧模式：5484 只 × 1 次 API × 0.9s = ~82 分钟
          新模式：days 次 API（每次拿全市场当日数据）× 0.4s ≈ days × 0.4s
            --days 1  → 1 次 API ≈ 1 秒（拿今日全市场）
            --days 30 → ~30 次 API ≈ 12 秒
            --days 365→ ~365 次 API ≈ 2.5 分钟

        delay 参数仍保留（对 API 节流），但不再对 DB 写入节流。
        """
        from datetime import datetime, timedelta, timezone as _tz, date as _date
        from market_data import tushare_service as ts_svc
        from market_data.models import AssetKline

        from_dt  = datetime.now(tz=_tz.utc) - timedelta(days=days)
        end_dt   = datetime.now(tz=_tz.utc)
        start_str = ts_svc.date_to_tushare_str(from_dt)
        end_str   = ts_svc.date_to_tushare_str(end_dt)

        self.stdout.write(
            f'\n[3/x] 同步日线 K 线（全市场按日期批量），共 {len(asset_objs)} 只，'
            f'时间范围 {start_str}~{end_str}...'
        )

        # ── 构建 code → Asset 映射，供后续快速路由 ────────────────────────────
        asset_map: dict = {a.code: a for a in asset_objs}

        # ── force 模式：清除时间范围内旧数据（按 asset_id 批量 DELETE）──────────
        if force:
            asset_ids = [a.id for a in asset_objs]
            k_from = datetime(from_dt.year, from_dt.month, from_dt.day, tzinfo=_tz.utc)
            k_to   = datetime(end_dt.year,  end_dt.month,  end_dt.day,  tzinfo=_tz.utc)
            deleted, _ = AssetKline.objects.filter(
                asset_id__in=asset_ids,
                resolution='D',
                k_time__gte=k_from,
                k_time__lte=k_to,
            ).delete()
            self.stdout.write(f'  🗑️  force 模式：删除旧 K 线 {deleted} 条')

        # ── 按日期迭代，每天一次 API 拿全市场数据 ────────────────────────────
        total_written  = 0
        total_no_data  = 0
        trading_days   = 0
        errors         = 0
        BATCH_SIZE     = 2000

        cur = from_dt.date()
        today = end_dt.date()

        while cur <= today:
            date_str = cur.strftime('%Y%m%d')
            cur += timedelta(days=1)  # 先推进，方便 continue

            try:
                daily_items = ts_svc.get_daily_klines_by_date(date_str)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING(f'\n[中断] 最后处理日期: {date_str}'))
                break
            except Exception as e:
                errors += 1
                logger.warning('[import_cn_stocks] 拉取 %s 失败: %s', date_str, str(e))
                time.sleep(delay)
                continue

            if not daily_items:
                total_no_data += 1
                # 非交易日无需 sleep（未调用 API，_call_with_retry 内部已处理退避）
                continue

            trading_days += 1

            # 构造 ORM 对象列表：只保留在 asset_map 中的股票
            objs = []
            for item in daily_items:
                asset = asset_map.get(item['code'])
                if asset is None:
                    continue
                objs.append(AssetKline(
                    asset=asset,
                    resolution='D',
                    k_time=item['k_time'],
                    open=item.get('open') or 0,
                    high=item.get('high') or 0,
                    low=item.get('low') or 0,
                    close=item.get('close') or 0,
                    volume=item.get('volume'),
                ))

            # 分批 bulk_create（INSERT IGNORE）
            for i in range(0, len(objs), BATCH_SIZE):
                AssetKline.objects.bulk_create(
                    objs[i:i + BATCH_SIZE],
                    batch_size=BATCH_SIZE,
                    ignore_conflicts=True,
                )
            total_written += len(objs)

            self.stdout.write(
                f'  📅 {date_str}  入库 {len(objs):>5} 条'
                f'  累计 {total_written} 条  交易日={trading_days}'
            )

            # 仅对 API 节流（delay 默认 0.5，但 _call_with_retry 内已有 0.4s）
            # 只在实际调用了 API 后才 sleep
            if delay > 0:
                time.sleep(max(0.0, delay - 0.4))  # 扣除已等待的 REQUEST_DELAY

        self.stdout.write(self.style.SUCCESS(
            f'\n[DONE] K 线同步完成！'
            f'交易日={trading_days}  总入库={total_written}  '
            f'非交易日={total_no_data}  错误={errors}'
        ))

    def _refresh_quotes_for_assets(self, asset_objs: list, delay: float):
        """
        批量刷新行情快照（一次 API 获取全市场，彻底取消逐股调用）。

        核心优化：
          旧模式：5485 只 × 1 次 API × 0.9s ≈ 82 分钟
          新模式：1 次 API（get_latest_daily_quotes_all，自动回退找最近交易日）≈ 0.4 秒
                  + 1 次 bulk_create（2000/批）写入全部快照 ≈ 0.5 秒
                  → 全流程 < 3 秒

        delay 参数已无实际作用（仅保留兼容命令行参数，不用于写库）。
        """
        from market_data import tushare_service as ts_svc
        from market_data.models import AssetQuoteSnapshot

        self.stdout.write(
            f'\n[3/x] 刷新行情快照（全市场批量），共 {len(asset_objs)} 只...'
        )

        t0 = time.time()

        # ── 一次 API 拿全市场最近交易日数据 ──────────────────────────────────
        try:
            daily_items = ts_svc.get_latest_daily_quotes_all(lookback_days=7)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n[中断] 行情快照刷新已中止'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n[ERROR] 拉取全市场行情失败: {e}'))
            logger.error('[import_cn_stocks] 批量行情拉取失败: %s', str(e))
            return

        if not daily_items:
            self.stdout.write(self.style.WARNING(
                '⚠️  最近 7 天均无 A 股行情数据（可能是长假），跳过快照写入'
            ))
            return

        self.stdout.write(
            f'  📡 API 返回 {len(daily_items)} 条行情，耗时 {time.time()-t0:.2f}s'
        )

        # ── code → Asset 映射（O(1) 查找）────────────────────────────────────
        asset_map = {a.code: a for a in asset_objs}

        # ── 构造 ORM 对象，顺便收集优先股输出行 ────────────────────────────
        objs = []
        priority_lines = []
        no_data = 0

        for item in daily_items:
            asset = asset_map.get(item['code'])
            if asset is None:
                continue  # 该股不在本次目标列表中

            price      = item.get('close')
            change_pct = item.get('pct_chg')
            change_amt = item.get('change')

            if not price:
                no_data += 1
                continue

            objs.append(AssetQuoteSnapshot(
                asset=asset,
                price=price,
                change_amount=change_amt,
                change_pct=change_pct,
                open=item.get('open'),
                high=item.get('high'),
                low=item.get('low'),
                prev_close=item.get('pre_close'),
                volume=item.get('volume'),
                amount=item.get('amount'),
                quote_time=item.get('k_time'),
                source='tushare',
            ))

            # 只打印重点股票行情（避免输出 5000 行）
            if asset.code in PRIORITY_CN_CODES:
                sign = '+' if (change_pct or 0) >= 0 else ''
                priority_lines.append(
                    f'  {asset.code} {asset.name[:8]:<8} '
                    f'¥{float(price):<10.2f}  {sign}{float(change_pct or 0):.2f}%'
                )

        # ── 分批 bulk_create（AssetQuoteSnapshot 无 unique 约束，直接插入）──
        BATCH_SIZE = 2000
        written = 0
        for i in range(0, len(objs), BATCH_SIZE):
            batch = objs[i:i + BATCH_SIZE]
            AssetQuoteSnapshot.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            written += len(batch)

        elapsed = time.time() - t0

        # 打印重点股票行情
        for line in priority_lines:
            self.stdout.write(line)

        self.stdout.write(self.style.SUCCESS(
            f'\n[DONE] 行情快照刷新完成！'
            f'写入={written}  无价格={no_data}  '
            f'共={len(asset_objs)}  耗时={elapsed:.2f}s'
        ))
