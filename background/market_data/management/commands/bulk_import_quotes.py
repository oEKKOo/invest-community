"""
Django 管理命令：一键批量导入大量美股并刷新行情（前端展示用）

用法：
  # 快速模式：从 Finnhub 拉取全量美股列表，导入前 500 只并刷新行情
  python manage.py bulk_import_quotes

  # 指定导入数量（建议 200~1000，免费版 API 限速约 60次/分）
  python manage.py bulk_import_quotes --limit 300

  # 只刷新行情（不重新导入，对已有资产刷新）
  python manage.py bulk_import_quotes --quote-only

  # 增量模式：跳过已有快照的资产
  python manage.py bulk_import_quotes --limit 500 --skip-existing

  # 自定义请求延迟（免费版建议 >= 0.1s）
  python manage.py bulk_import_quotes --limit 300 --delay 0.15

执行流程：
  1. 从 Finnhub /stock/symbol 拉取美股列表（~30000 只）
  2. 按优先级排序（知名股票优先）
  3. 写入数据库（Asset 表）
  4. 逐一刷新行情快照（AssetQuoteSnapshot 表）
  5. 完成后前端即可看到大量实时行情数据

注意：
  - 免费版 Finnhub API 限速约 60次/分钟
  - 导入 300 只约需 0.5~1 分钟
  - 导入 1000 只约需 2~3 分钟
  - 可随时 Ctrl+C 中断，已完成的数据不会丢失
"""
import time
import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone as dj_tz

logger = logging.getLogger(__name__)

# Finnhub type → 内部 asset_type 映射
TYPE_MAP = {
    'Common Stock':       'STOCK',
    'ETP':                'ETF',
    'ETF':                'ETF',
    'Fund':               'FUND',
    'FUND':               'FUND',
    'Bond':               'BOND',
    'BOND':               'BOND',
    'Equity WRT':         'STOCK',
    'DR':                 'STOCK',
    'Closed-End Fund':    'FUND',
    'Unit':               'FUND',
    'Right':              'STOCK',
    'Warrant':            'STOCK',
    'Structured Product': 'STOCK',
    'MLP':                'STOCK',
    'REIT':               'STOCK',
    'Preferred Stock':    'STOCK',
    'ADR':                'STOCK',
    'GDR':                'STOCK',
    'Open-End Fund':      'FUND',
    'Index':              'ETF',
}

# 优先展示的知名股票（排在前面，保证行情刷新时优先覆盖）
PRIORITY_SYMBOLS = {
    # 科技七巨头
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA',
    # 金融
    'BRK.B', 'JPM', 'V', 'MA', 'GS', 'MS', 'BAC', 'WFC', 'C', 'AXP', 'BLK',
    # 半导体
    'TSM', 'AMD', 'INTC', 'AVGO', 'QCOM', 'TXN', 'MU', 'AMAT', 'LRCX',
    # 软件/云
    'CRM', 'ORCL', 'ADBE', 'NOW', 'INTU', 'SNOW', 'DDOG', 'CRWD', 'PANW',
    # 互联网
    'NFLX', 'UBER', 'ABNB', 'SHOP', 'BABA', 'PDD', 'JD', 'BIDU',
    # 消费
    'WMT', 'KO', 'PEP', 'MCD', 'SBUX', 'NKE', 'TGT', 'COST', 'HD', 'PG',
    # 医疗
    'JNJ', 'LLY', 'UNH', 'PFE', 'MRK', 'ABBV', 'GILD', 'MRNA', 'REGN',
    # 能源
    'XOM', 'CVX', 'COP', 'OXY',
    # 工业
    'BA', 'CAT', 'GE', 'HON', 'RTX', 'LMT', 'UPS', 'FDX',
    # 通信
    'DIS', 'CMCSA', 'T', 'VZ', 'TMUS',
    # 金融科技
    'PYPL', 'SQ', 'COIN',
    # 新能源
    'RIVN', 'NIO', 'ENPH',
    # ETF
    'SPY', 'QQQ', 'IWM', 'GLD', 'TLT', 'VTI', 'VOO', 'IVV', 'AGG',
    'XLK', 'XLF', 'XLE', 'XLV', 'ARKK',
}


class Command(BaseCommand):
    help = '一键批量导入大量美股并刷新行情快照（前端展示用）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--exchange',
            type=str,
            default='US',
            help='Finnhub 交易所代码，默认 US（美股）'
        )
        parser.add_argument(
            '--market',
            type=str,
            default='US',
            help='写入 Asset.market 的值，默认 US'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=500,
            help='最多导入 N 只（默认 500，0=全部，建议先用 200~500 测试）'
        )
        parser.add_argument(
            '--type',
            type=str,
            default='',
            dest='stock_type',
            help='只导入指定类型，如 "Common Stock"（不传则全部类型）'
        )
        parser.add_argument(
            '--quote-only',
            action='store_true',
            dest='quote_only',
            help='不重新导入，只对已有资产刷新行情（受 --limit 控制）'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            dest='skip_existing',
            help='刷新行情时跳过已有快照的资产（增量模式）'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.12,
            help='每次 Finnhub 行情请求之间的延迟（秒），默认 0.12s，免费版建议 >=0.1'
        )
        parser.add_argument(
            '--no-quote',
            action='store_true',
            dest='no_quote',
            help='只导入资产列表，不刷新行情（快速入库）'
        )

    def handle(self, *args, **options):
        from market_data import finnhub_service as fh

        if not fh.is_api_key_configured():
            raise CommandError(
                'FINNHUB_API_KEY 未配置！\n'
                '请在 D:\\invest\\background\\.env 中添加：\n'
                '  FINNHUB_API_KEY=your_key_here'
            )

        exchange   = options['exchange']
        market     = options['market']
        limit      = options['limit']
        stock_type = options['stock_type']
        quote_only = options['quote_only']
        skip_exist = options['skip_existing']
        delay      = options['delay']
        no_quote   = options['no_quote']

        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'  批量导入美股行情数据\n'
            f'  交易所: {exchange}  市场: {market}  限制: {limit if limit > 0 else "全量"}\n'
            f'{"="*60}\n'
        ))

        # ── 仅刷新行情模式 ────────────────────────────────────────────────
        if quote_only:
            self._refresh_quotes(market, limit, skip_exist, delay)
            return

        # ── Step 1: 从 Finnhub 拉取股票列表 ──────────────────────────────
        self.stdout.write(f'[1/3] 从 Finnhub 拉取 {exchange} 股票列表...')
        symbols = fh.get_stock_symbols(exchange)

        if not symbols:
            raise CommandError(
                f'无法从 Finnhub 获取 {exchange} 股票列表，请检查 Key 和网络\n'
                f'提示：可先运行 python manage.py sync_market_data --task status 检查 Key 配置'
            )

        self.stdout.write(f'      Finnhub 返回 {len(symbols)} 只股票')

        # ── Step 2: 过滤 + 排序（优先知名股票） ──────────────────────────
        if stock_type:
            symbols = [s for s in symbols if s.get('type', '') == stock_type]
            self.stdout.write(f'      过滤 type="{stock_type}" 后剩余 {len(symbols)} 只')

        # 过滤掉无 symbol 的条目
        symbols = [s for s in symbols if s.get('symbol', '').strip()]

        # 优先级排序：知名股票排前面
        def sort_key(s):
            sym = s.get('symbol', '')
            return (0 if sym in PRIORITY_SYMBOLS else 1, sym)

        symbols.sort(key=sort_key)

        # 应用 limit
        if limit > 0:
            symbols = symbols[:limit]
            self.stdout.write(f'      应用 --limit={limit}，实际处理 {len(symbols)} 只')
        else:
            self.stdout.write(f'      全量导入 {len(symbols)} 只（可用 --limit N 限制数量）')

        # ── Step 3: 写入数据库 ────────────────────────────────────────────
        self.stdout.write(f'\n[2/3] 写入数据库...')
        created_count = 0
        updated_count = 0
        error_count = 0
        asset_objs = []

        from content.models import Asset

        for i, sym in enumerate(symbols, 1):
            finnhub_sym = sym.get('symbol', '').strip()
            display_sym = sym.get('displaySymbol', finnhub_sym).strip() or finnhub_sym
            description = sym.get('description', '').strip() or finnhub_sym
            currency    = sym.get('currency', 'USD').strip() or 'USD'
            raw_type    = sym.get('type', 'Common Stock')
            asset_type  = TYPE_MAP.get(raw_type, 'STOCK')

            try:
                obj, created = Asset.objects.update_or_create(
                    code=display_sym,
                    market=market,
                    defaults={
                        'name':           description,
                        'asset_type':     asset_type,
                        'finnhub_symbol': finnhub_sym,
                        'currency':       currency,
                        'exchange':       exchange,
                        'status':         'ACTIVE',
                        'last_sync_at':   dj_tz.now(),
                    }
                )
                asset_objs.append(obj)
                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # 每 100 条打印一次进度
                if i % 100 == 0 or i == len(symbols):
                    self.stdout.write(
                        f'  进度: {i}/{len(symbols)}  '
                        f'新增={created_count}  更新={updated_count}  错误={error_count}'
                    )

            except Exception as e:
                error_count += 1
                logger.warning('[bulk_import_quotes] 写入失败: symbol=%s err=%s', finnhub_sym, str(e))
                if error_count <= 5:
                    self.stdout.write(self.style.WARNING(f'  [WARN] {finnhub_sym}: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n[2/3] 入库完成！新增 {created_count} 只，更新 {updated_count} 只，'
            f'错误 {error_count} 只，共 {len(asset_objs)} 只资产已入库'
        ))

        # ── Step 4: 刷新行情（可选） ──────────────────────────────────────
        if no_quote:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('[跳过] 已跳过行情刷新（--no-quote）'))
            self.stdout.write('[TIP] 稍后可运行以下命令刷新行情：')
            self.stdout.write('  python manage.py bulk_import_quotes --quote-only')
            self.stdout.write('  python manage.py sync_market_data --task quote')
        else:
            self._refresh_quotes_for_assets(asset_objs, skip_exist, delay)

    # ── 内部方法 ──────────────────────────────────────────────────────────

    def _refresh_quotes(self, market: str, limit: int, skip_exist: bool, delay: float):
        """对已有资产刷新行情（quote-only 模式）"""
        from content.models import Asset
        from market_data.models import AssetQuoteSnapshot

        queryset = Asset.objects.filter(
            market=market, status='ACTIVE'
        ).exclude(finnhub_symbol='').exclude(finnhub_symbol__isnull=True)

        if skip_exist:
            has_snap = AssetQuoteSnapshot.objects.values_list('asset_id', flat=True).distinct()
            queryset = queryset.exclude(id__in=has_snap)

        # 优先知名股票
        all_assets = list(queryset)
        all_assets.sort(key=lambda a: (0 if a.code in PRIORITY_SYMBOLS else 1, a.code))

        if limit > 0:
            all_assets = all_assets[:limit]

        self.stdout.write(f'[quote-only] 对 {len(all_assets)} 只资产刷新行情...')
        self._refresh_quotes_for_assets(all_assets, skip_exist=False, delay=delay)

    def _refresh_quotes_for_assets(self, asset_objs: list, skip_exist: bool, delay: float):
        """批量刷新行情快照，带进度输出"""
        from market_data.tasks import get_or_refresh_quote
        from market_data.models import AssetQuoteSnapshot

        total = len(asset_objs)
        est_minutes = total * delay / 60

        self.stdout.write(f'\n[3/3] 刷新行情快照（共 {total} 只，延迟={delay}s/只）...')
        self.stdout.write(f'      免费版限速 ~60次/分，预计耗时约 {est_minutes:.1f} 分钟')
        self.stdout.write('      （Ctrl+C 可中断，已刷新的数据不会丢失）\n')

        success = 0
        no_data = 0
        errors  = 0

        for i, asset in enumerate(asset_objs, 1):
            if not asset.finnhub_symbol:
                no_data += 1
                continue

            if skip_exist:
                if AssetQuoteSnapshot.objects.filter(asset=asset).exists():
                    no_data += 1
                    continue

            try:
                quote = get_or_refresh_quote(asset)
                if quote and quote.get('price'):
                    price      = quote['price']
                    change_pct = quote.get('change_pct') or 0
                    sign       = '+' if change_pct >= 0 else ''
                    success += 1
                    # 每 20 只打印一次，或者是知名股票
                    if i % 20 == 0 or asset.code in PRIORITY_SYMBOLS or i == total:
                        self.stdout.write(
                            f'  [{i:>4}/{total}] {asset.code:<12} '
                            f'[{asset.market}]  ${price:<10.2f}  {sign}{change_pct:.2f}%'
                        )
                else:
                    no_data += 1
                    if asset.code in PRIORITY_SYMBOLS:
                        self.stdout.write(
                            self.style.WARNING(f'  [{i:>4}] {asset.code} 无行情数据')
                        )
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING(
                    f'\n[中断] 已完成 {i-1}/{total}，'
                    f'成功={success} 无数据={no_data} 错误={errors}'
                ))
                self._print_summary(success, no_data, errors, total)
                return
            except Exception as e:
                errors += 1
                logger.warning('[bulk_import_quotes] 行情刷新失败: %s err=%s', asset.code, str(e))

            time.sleep(delay)

        self._print_summary(success, no_data, errors, total)

    def _print_summary(self, success: int, no_data: int, errors: int, total: int):
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'[DONE] 行情刷新完成！\n'
            f'  ✅ 成功={success}  ⚠️ 无数据={no_data}  ❌ 错误={errors}  共={total}\n'
            f'  成功率: {success/total*100:.1f}%' if total > 0 else ''
        ))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('现在可以启动前端查看行情数据：'))
        self.stdout.write('  cd D:\\invest\\frontend && npm run dev')
        self.stdout.write('')
        self.stdout.write('[TIP] 定期刷新行情可运行：')
        self.stdout.write('  python manage.py sync_market_data --task quote')
        self.stdout.write('  python manage.py bulk_import_quotes --quote-only --limit 500')
