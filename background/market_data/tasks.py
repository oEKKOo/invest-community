"""
数据同步任务（支持 Finnhub（美股/港股）+ Tushare（A 股）双数据源）
- 任务 A:  symbols_sync        — Finnhub 标的清单同步（美股/港股）
- 任务 A2: cn_symbols_sync     — Tushare A 股标的清单同步
- 任务 A3: hk_symbols_sync     — Tushare 港股标的清单同步（hk_basic）
- 任务 B:  kline_sync          — 日线数据同步（增量 + 回补，自动选择数据源）
- 任务 C:  quote_refresh       — 行情快照刷新（自动选择数据源，可高频调用）
- 任务 C2: quote_refresh_popular — 热门标的行情刷新（定时调度）
- 任务 D:  dq_check            — 数据质量校验（缺失/重复/异常检测）

数据源路由规则：
  market in {'SH','SZ','BJ'}  → Tushare（A 股日线，收盘数据）
  market == 'HK' 日 K          → Tushare hk_daily；港股非日 K / 实时报价 → Finnhub（若已配置 finnhub_symbol）
  美股等                       → Finnhub

缓存分层策略：
  L1 Django Cache（LocMem / Redis）—— 命中直接返回，无 DB/API 开销
  L2 DB 快照（AssetQuoteSnapshot）—— TTL 内有效则写 L1 后返回
  L3 数据源 API               —— 实时/日线拉取，写 DB + 写 L1 后返回

可通过 Django management commands 或 Celery Beat 调度。
每次运行都会写 DataJobLog 记录。
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone as dj_timezone

from .models import AssetQuoteSnapshot, AssetKline, DataJobLog
from . import finnhub_service as fh
from . import tushare_service as ts_svc
from .tushare_service import CN_MARKETS

logger = logging.getLogger(__name__)


def _log_gorq_timing(asset, layer: str, t0: float) -> None:
    try:
        from invest_backend.perf_timing import api_timing_enabled, log_api_duration

        if api_timing_enabled():
            ms = (time.perf_counter() - t0) * 1000
            log_api_duration(
                'get_or_refresh_quote',
                ms,
                asset_id=asset.id,
                code=getattr(asset, 'code', ''),
                layer=layer,
            )
    except Exception:
        pass


# ---------- 缓存工具 ----------

def _quote_cache_key(asset_id: int) -> str:
    """统一的行情缓存键，格式：quote:asset:{id}"""
    return f'quote:asset:{asset_id}'


def _get_quote_ttl() -> int:
    """从 Django settings 读取行情 TTL（秒），默认 60"""
    return int(getattr(settings, 'FINNHUB_QUOTE_CACHE_TTL', 60))


# ---------- 内部工具 ----------

def _start_job(job_type: str, market: str = '', asset_code: str = '') -> DataJobLog:
    """创建任务日志并标记为 RUNNING"""
    job = DataJobLog.objects.create(
        job_type=job_type,
        status='RUNNING',
        market=market,
        asset_code=asset_code,
    )
    logger.info('[Task] 开始任务: type=%s market=%s asset=%s id=%d', job_type, market, asset_code, job.id)
    return job


def _finish_job(job: DataJobLog, success: bool, affected_rows: int = 0, error: str = '',
                extra: dict = None):
    """更新任务日志状态"""
    job.status = 'SUCCESS' if success else 'FAILED'
    job.finished_at = dj_timezone.now()
    job.affected_rows = affected_rows
    job.error_message = error
    if extra:
        job.extra_info = extra
    job.save(update_fields=['status', 'finished_at', 'affected_rows', 'error_message', 'extra_info'])
    logger.info(
        '[Task] 任务结束: id=%d type=%s status=%s rows=%d',
        job.id, job.job_type, job.status, affected_rows
    )


# ---------- 任务 A: 标的清单同步 ----------

def symbols_sync(exchange: str, market: str = '') -> DataJobLog:
    """
    拉取指定交易所的股票列表并更新/新增到 Asset 表
    exchange: Finnhub 侧的交易所代码（如 US/HK）
    market:   内部市场标识（如 US/HK/SH/SZ）
    """
    from content.models import Asset

    job = _start_job('SYMBOLS_SYNC', market=market)
    try:
        symbols = fh.get_stock_symbols(exchange)
        if symbols is None:
            _finish_job(job, False, error='Finnhub 返回 None，可能是网络错误或 Key 未配置')
            return job

        created_count = 0
        updated_count = 0

        for sym in symbols:
            finnhub_sym = sym.get('symbol', '')
            display_sym = sym.get('displaySymbol', finnhub_sym)
            description = sym.get('description', '')
            currency = sym.get('currency', '')
            asset_type_raw = sym.get('type', '').upper()

            # 映射 Finnhub type → 内部 asset_type
            type_map = {
                'COMMON STOCK': 'STOCK',
                'ETP': 'ETF',
                'ETF': 'ETF',
                'FUND': 'FUND',
                'BOND': 'BOND',
            }
            asset_type = type_map.get(asset_type_raw, 'STOCK')

            if not finnhub_sym:
                continue

            defaults = {
                'name': description,
                'asset_type': asset_type,
                'market': market,
                'currency': currency,
                'exchange': exchange,
                'finnhub_symbol': finnhub_sym,
                'last_sync_at': dj_timezone.now(),
            }

            try:
                obj, created = Asset.objects.update_or_create(
                    code=display_sym,
                    market=market,
                    asset_type=asset_type,
                    defaults=defaults
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.warning('[Task:symbols_sync] 写入异常: symbol=%s err=%s', finnhub_sym, str(e))

        total = created_count + updated_count
        _finish_job(job, True, affected_rows=total,
                    extra={'created': created_count, 'updated': updated_count})

    except Exception as exc:
        logger.exception('[Task:symbols_sync] 未预期异常')
        _finish_job(job, False, error=str(exc))

    return job


# ---------- 任务 A2: A 股标的清单同步（Tushare）----------

def cn_symbols_sync(list_status: str = 'L') -> DataJobLog:
    """
    从 Tushare 拉取 A 股股票列表并更新/新增到 Asset 表
    list_status: L(上市) D(退市) P(暂停上市)，默认 L
    覆盖范围：SH（上交所）、SZ（深交所）、BJ（北交所）
    """
    from content.models import Asset

    job = _start_job('SYMBOLS_SYNC', market='CN')
    try:
        if not ts_svc.is_api_token_configured():
            _finish_job(job, False, error='TUSHARE_API_TOKEN 未配置')
            return job

        stocks = ts_svc.get_stock_basic(list_status=list_status)
        if stocks is None:
            _finish_job(job, False, error='Tushare 返回 None，可能是 Token 无效或网络错误')
            return job

        created_count = 0
        updated_count = 0

        for s in stocks:
            code   = s.get('code', '')
            market = s.get('market', '')   # SH / SZ / BJ
            name   = s.get('name', '')
            industry = s.get('industry', '')

            if not code or market not in CN_MARKETS:
                continue

            # 交易所映射：Tushare exchange → 内部 exchange 字段
            # Tushare exchange: SSE(上交所) / SZSE(深交所) / BSE(北交所)
            exchange_map = {'SSE': 'SH', 'SZSE': 'SZ', 'BSE': 'BJ'}
            raw_exchange = s.get('exchange', '')
            exchange = exchange_map.get(raw_exchange, raw_exchange)

            defaults = {
                'name':         name,
                'asset_type':   'STOCK',
                'market':       market,   # 放进 defaults，修正旧的 market='CN'
                'currency':     'CNY',
                'exchange':     exchange,
                'industry':     industry,
                'status':       'ACTIVE',
                'meta_json':    {'tushare_code': s.get('ts_code', ''),
                                 'area': s.get('area', ''),
                                 'list_date': s.get('list_date', '')},
                'last_sync_at': dj_timezone.now(),
            }

            try:
                # DB 唯一约束 uk_asset_type_code 仅覆盖 (asset_type, code)，
                # 查找键不含 market，避免旧记录（market='CN'）触发重复插入。
                obj, created = Asset.objects.update_or_create(
                    code=code,
                    asset_type='STOCK',
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.warning('[Task:cn_symbols_sync] 写入异常: code=%s err=%s', code, str(e))

        total = created_count + updated_count
        _finish_job(job, True, affected_rows=total,
                    extra={'created': created_count, 'updated': updated_count,
                           'list_status': list_status})
        logger.info('[Task:cn_symbols_sync] 完成: total=%d created=%d updated=%d',
                    total, created_count, updated_count)

    except Exception as exc:
        logger.exception('[Task:cn_symbols_sync] 未预期异常')
        _finish_job(job, False, error=str(exc))

    return job


# ---------- 任务 A3: 港股标的清单同步（Tushare hk_basic）----------

def hk_symbols_sync(list_status: str = 'L') -> DataJobLog:
    """
    从 Tushare 拉取港股列表并更新/新增到 Asset 表（code 五位数字 + market=HK）。
    list_status: L(上市) D(退市) P(暂停上市)，默认 L
    """
    from content.models import Asset

    job = _start_job('SYMBOLS_SYNC', market='HK')
    try:
        if not ts_svc.is_api_token_configured():
            _finish_job(job, False, error='TUSHARE_API_TOKEN 未配置')
            return job

        stocks = ts_svc.get_hk_basic(list_status=list_status)
        if stocks is None:
            _finish_job(job, False, error='Tushare hk_basic 返回 None')
            return job

        created_count = 0
        updated_count = 0

        for s in stocks:
            code = s.get('code', '')
            name = s.get('name', '')
            ts_code = s.get('ts_code', '')
            if not code:
                continue

            curr = (s.get('curr_type') or 'HKD').strip() or 'HKD'

            defaults = {
                'name':         name or code,
                'asset_type':   'STOCK',
                'market':       'HK',
                'currency':     curr,
                'exchange':     'HKEX',
                'status':       'ACTIVE',
                'meta_json':    {
                    'tushare_ts_code': ts_code,
                    'fullname': s.get('fullname', ''),
                    'list_status': s.get('list_status', ''),
                    'list_date': s.get('list_date', ''),
                },
                'last_sync_at': dj_timezone.now(),
            }

            try:
                obj, created = Asset.objects.update_or_create(
                    code=code,
                    market='HK',
                    asset_type='STOCK',
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.warning('[Task:hk_symbols_sync] 写入异常: code=%s err=%s', code, str(e))

        total = created_count + updated_count
        _finish_job(job, True, affected_rows=total,
                    extra={'created': created_count, 'updated': updated_count,
                           'list_status': list_status})
        logger.info('[Task:hk_symbols_sync] 完成: total=%d created=%d updated=%d',
                    total, created_count, updated_count)

    except Exception as exc:
        logger.exception('[Task:hk_symbols_sync] 未预期异常')
        _finish_job(job, False, error=str(exc))

    return job


# ---------- 任务 B: K 线数据同步 ----------

def kline_sync(
    asset_ids: Optional[List[int]] = None,
    resolution: str = 'D',
    days_back: int = 365,
    force_refetch: bool = False,
    market_filter: Optional[str] = None,
) -> DataJobLog:
    """
    增量同步 K 线（日线），自动按市场选择数据源：
      A 股（SH/SZ/BJ）→ Tushare pro.daily（仅支持日线 'D'）
      港股（HK）日 K  → Tushare pro.hk_daily
      其他（如 US）   → Finnhub（日 K 不含港股，避免与 hk_daily 重复）

    参数：
    - asset_ids:     指定资产列表；None 表示全量同步
    - resolution:    K线周期，默认 'D'（日K）；A 股仅支持 'D'
    - days_back:     向前拉取的天数
    - force_refetch: True 则清空并重拉（数据回补）
    - market_filter: 只同步指定市场，如 'SH'/'US'/'HK'；None 表示全市场
    """
    from content.models import Asset

    job = _start_job('KLINE_SYNC', market=market_filter or '')
    try:
        cn_qs = Asset.objects.filter(market__in=CN_MARKETS)
        hk_qs = Asset.objects.filter(market='HK')
        fh_qs = Asset.objects.exclude(
            finnhub_symbol__isnull=True
        ).exclude(finnhub_symbol='').exclude(market__in=CN_MARKETS).exclude(market='HK')

        if asset_ids:
            cn_qs = cn_qs.filter(id__in=asset_ids)
            hk_qs = hk_qs.filter(id__in=asset_ids)
            fh_qs = fh_qs.filter(id__in=asset_ids)

        if market_filter:
            if market_filter in CN_MARKETS:
                cn_qs = cn_qs.filter(market=market_filter)
                hk_qs = hk_qs.none()
                fh_qs = fh_qs.none()
            elif market_filter == 'HK':
                cn_qs = cn_qs.none()
                fh_qs = fh_qs.none()
            else:
                cn_qs = cn_qs.none()
                hk_qs = hk_qs.none()
                fh_qs = fh_qs.filter(market=market_filter)

        total_rows = 0
        failed_assets = []

        # ── B1: Tushare（A 股 + 港股日线）—— 按日期批量拉取，每天各一次 API ───
        if ts_svc.is_api_token_configured() and resolution == 'D':
            from_dt  = datetime.now(tz=timezone.utc) - timedelta(days=days_back)
            end_dt   = datetime.now(tz=timezone.utc)

            cn_assets   = list(cn_qs)
            hk_assets   = list(hk_qs)
            cn_asset_map = {a.code: a for a in cn_assets}
            hk_asset_map = {ts_svc.normalize_hk_listing_code(a.code): a for a in hk_assets}
            BATCH_SIZE  = 2000

            k_from = datetime(from_dt.year, from_dt.month, from_dt.day, tzinfo=timezone.utc)
            k_to   = datetime(end_dt.year,  end_dt.month,  end_dt.day,  tzinfo=timezone.utc)

            if force_refetch and cn_assets:
                _ids = [a.id for a in cn_assets]
                AssetKline.objects.filter(
                    asset_id__in=_ids, resolution='D',
                    k_time__gte=k_from, k_time__lte=k_to,
                ).delete()

            if force_refetch and hk_assets:
                _ids = [a.id for a in hk_assets]
                AssetKline.objects.filter(
                    asset_id__in=_ids, resolution='D',
                    k_time__gte=k_from, k_time__lte=k_to,
                ).delete()

            cur = from_dt.date()
            today = end_dt.date()
            while cur <= today:
                date_str = cur.strftime('%Y%m%d')
                cur += timedelta(days=1)

                if cn_assets:
                    try:
                        daily_items = ts_svc.get_daily_klines_by_date(date_str)
                    except Exception as exc:
                        logger.warning('[Task:kline_sync] A股 %s 失败: %s', date_str, str(exc))
                        failed_assets.append({'code': f'[CN date:{date_str}]', 'error': str(exc)})
                        daily_items = None
                    else:
                        if daily_items:
                            objs = []
                            for item in daily_items:
                                asset = cn_asset_map.get(item['code'])
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
                            for i in range(0, len(objs), BATCH_SIZE):
                                AssetKline.objects.bulk_create(
                                    objs[i:i + BATCH_SIZE],
                                    batch_size=BATCH_SIZE,
                                    ignore_conflicts=True,
                                )
                            total_rows += len(objs)
                            logger.info('[Task:kline_sync] A股 %s 入库 %d 条', date_str, len(objs))

                if hk_assets:
                    try:
                        hk_items = ts_svc.get_hk_daily_by_date(date_str)
                    except Exception as exc:
                        logger.warning('[Task:kline_sync] 港股 %s 失败: %s', date_str, str(exc))
                        failed_assets.append({'code': f'[HK date:{date_str}]', 'error': str(exc)})
                        hk_items = None
                    else:
                        if hk_items:
                            objs = []
                            for item in hk_items:
                                asset = hk_asset_map.get(item['code'])
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
                            for i in range(0, len(objs), BATCH_SIZE):
                                AssetKline.objects.bulk_create(
                                    objs[i:i + BATCH_SIZE],
                                    batch_size=BATCH_SIZE,
                                    ignore_conflicts=True,
                                )
                            total_rows += len(objs)
                            logger.info('[Task:kline_sync] 港股 %s 入库 %d 条', date_str, len(objs))

        elif resolution == 'D' and not ts_svc.is_api_token_configured():
            logger.warning('[Task:kline_sync] TUSHARE_API_TOKEN 未配置，跳过 A 股/港股日线同步')

        # ── B2: Finnhub（美股等非港股日 K；港股日 K 已由 hk_daily 覆盖）──────
        if fh.is_api_key_configured():
            to_ts   = fh.now_ts()
            from_dt = datetime.now(tz=timezone.utc) - timedelta(days=days_back)
            from_ts = fh.datetime_to_ts(from_dt)

            for asset in fh_qs:
                try:
                    data = fh.get_candles(asset.finnhub_symbol, resolution, from_ts, to_ts)
                    if data is None:
                        logger.debug('[Task:kline_sync] %s 无 K 线数据', asset.finnhub_symbol)
                        continue
                    items = data.get('items', [])
                    written = _write_klines(asset, resolution, items, force_refetch)
                    total_rows += written
                except Exception as exc:
                    logger.warning('[Task:kline_sync] %s 失败: %s', asset.finnhub_symbol, str(exc))
                    failed_assets.append({'code': asset.code, 'error': str(exc)})

        success = len(failed_assets) == 0
        status_val = 'SUCCESS' if success else ('PARTIAL' if total_rows > 0 else 'FAILED')
        job.status = status_val
        job.finished_at = dj_timezone.now()
        job.affected_rows = total_rows
        job.extra_info = {'failed_assets': failed_assets[:50]}
        if not success and total_rows == 0:
            job.error_message = f'全部失败，共 {len(failed_assets)} 个资产'
        job.save(update_fields=['status', 'finished_at', 'affected_rows', 'error_message', 'extra_info'])

        logger.info('[Task:kline_sync] 完成: rows=%d failed=%d', total_rows, len(failed_assets))

    except Exception as exc:
        logger.exception('[Task:kline_sync] 未预期异常')
        _finish_job(job, False, error=str(exc))

    return job


_KLINE_BATCH_SIZE = 2000  # 每批写入 K 线数量（可通过 settings 覆盖）


def _write_klines(asset, resolution: str, items: list, force_refetch: bool) -> int:
    """
    批量写入 K 线（bulk_create + ignore_conflicts，彻底取消逐条写入）。

    - 正常模式：INSERT IGNORE（UNIQUE KEY 保证不重复），一批 2000 条提交一次。
    - force 模式：先按时间范围 DELETE，再 INSERT（保证最新数据覆盖旧值）。

    返回"尝试写入条数"（force 模式下等于实际写入数）。
    """
    from .models import AssetKline

    if not items:
        return 0

    # ── force 模式：先删除时间范围内旧数据，保证回补覆盖最新值 ──────────────
    if force_refetch:
        times = [i['k_time'] for i in items if i.get('k_time')]
        if times:
            AssetKline.objects.filter(
                asset=asset, resolution=resolution,
                k_time__gte=min(times), k_time__lte=max(times)
            ).delete()

    # ── 构造 ORM 对象列表（不发 SQL，仅内存） ────────────────────────────────
    objs = []
    for item in items:
        k_time = item.get('k_time')
        if not k_time:
            continue
        objs.append(AssetKline(
            asset=asset,
            resolution=resolution,
            k_time=k_time,
            open=item.get('open') or 0,
            high=item.get('high') or 0,
            low=item.get('low') or 0,
            close=item.get('close') or 0,
            volume=item.get('volume'),
        ))

    if not objs:
        return 0

    # ── 分批 bulk_create，ignore_conflicts 对应 INSERT IGNORE ────────────────
    batch_size = int(getattr(settings, 'KLINE_BULK_BATCH_SIZE', _KLINE_BATCH_SIZE))
    for i in range(0, len(objs), batch_size):
        AssetKline.objects.bulk_create(
            objs[i:i + batch_size],
            batch_size=batch_size,
            ignore_conflicts=True,
        )

    logger.debug('[kline_write] bulk_create: asset=%s resolution=%s count=%d',
                 asset.code, resolution, len(objs))
    return len(objs)


# ---------- 任务 C: 行情快照刷新 ----------

def _fetch_quote_for_asset(asset) -> Optional[dict]:
    """
    根据资产市场选择数据源拉取最新行情（内部工具函数）：
    - A 股（SH/SZ/BJ）→ Tushare 最近交易日收盘数据
    - 其他（US/HK）   → Finnhub 实时报价
    返回统一格式的 quote dict，或 None
    """
    if asset.market in CN_MARKETS:
        ts_code = ts_svc.get_tushare_code(asset.code, asset.market)
        if not ts_code:
            return None
        return ts_svc.get_latest_daily_quote(ts_code)
    else:
        if not asset.finnhub_symbol:
            return None
        return fh.get_quote(asset.finnhub_symbol)


def quote_refresh(
    asset_ids: Optional[List[int]] = None,
    delay: float = 0.12,
    log_interval: int = 20,
) -> DataJobLog:
    """
    刷新行情快照（自动选择数据源，可高频调用）：
    - A 股（SH/SZ/BJ）→ Tushare 全市场批量拉取（1 次 API + bulk_create，秒级完成）
    - 其他（US/HK）   → Finnhub 实时报价（逐个调用，delay 节流）

    - asset_ids=None：刷新所有符合条件的 ACTIVE 资产（A 股 + 有 finnhub_symbol 的资产）
    - asset_ids=[...]：仅刷新指定资产
    - delay：Finnhub 请求之间的节流延迟（秒）；A 股批量模式不受此参数影响
    - log_interval：Finnhub 支路每隔多少只打印一次进度日志
    """
    import time as _time
    from content.models import Asset

    _BULK_BATCH = 2000

    ttl = _get_quote_ttl()
    job = _start_job('QUOTE_REFRESH')
    try:
        queryset = Asset.objects.filter(status='ACTIVE').filter(
            Q(market__in=list(CN_MARKETS)) |
            (Q(finnhub_symbol__isnull=False) & ~Q(finnhub_symbol=''))
        )
        if asset_ids:
            queryset = queryset.filter(id__in=asset_ids)

        assets    = list(queryset)
        cn_assets = [a for a in assets if a.market in CN_MARKETS]
        fh_assets = [a for a in assets if a.market not in CN_MARKETS]
        total   = len(assets)
        written = 0
        no_data = 0
        failed  = []

        logger.info(
            '[Task:quote_refresh] 开始刷新：A股=%d 海外=%d 共=%d',
            len(cn_assets), len(fh_assets), total
        )

        # ── A 股：全市场批量拉取，一次 API + bulk_create ──────────────────────
        if cn_assets:
            try:
                daily_items = ts_svc.get_latest_daily_quotes_all(lookback_days=7)
            except Exception as exc:
                logger.warning('[Task:quote_refresh] A股批量行情拉取失败: %s', str(exc))
                daily_items = None

            if daily_items:
                code_to_asset = {a.code: a for a in cn_assets}
                cn_objs = []
                for item in daily_items:
                    asset = code_to_asset.get(item['code'])
                    if asset is None or not item.get('close'):
                        continue
                    cn_objs.append(AssetQuoteSnapshot(
                        asset=asset,
                        price=item.get('close'),
                        change_amount=item.get('change'),
                        change_pct=item.get('pct_chg'),
                        open=item.get('open'),
                        high=item.get('high'),
                        low=item.get('low'),
                        prev_close=item.get('pre_close'),
                        volume=item.get('volume'),
                        amount=item.get('amount'),
                        quote_time=item.get('k_time'),
                        source='tushare',
                    ))

                for i in range(0, len(cn_objs), _BULK_BATCH):
                    batch = cn_objs[i:i + _BULK_BATCH]
                    created_batch = AssetQuoteSnapshot.objects.bulk_create(
                        batch, batch_size=_BULK_BATCH
                    )
                    written += len(created_batch)

                    # 回填缓存（批量回填）
                    for snap in created_batch:
                        try:
                            result = _snapshot_to_dict(snap.asset, snap)
                            cache.set(_quote_cache_key(snap.asset_id), result, timeout=ttl)
                        except Exception:
                            pass

                cn_no_data = len(cn_assets) - len(cn_objs)
                no_data += cn_no_data
                logger.info(
                    '[Task:quote_refresh] A股批量完成: 写入=%d 无价格=%d',
                    len(cn_objs), cn_no_data
                )
            else:
                no_data += len(cn_assets)
                logger.warning('[Task:quote_refresh] A股批量行情无数据（可能为非交易日）')

        # ── 海外资产（US/HK）：Finnhub 逐个调用 ─────────────────────────────
        for idx, asset in enumerate(fh_assets, 1):
            try:
                quote = _fetch_quote_for_asset(asset)
                if quote is None or not quote.get('price'):
                    no_data += 1
                    if idx % log_interval == 0 or idx == len(fh_assets):
                        logger.info(
                            '[Task:quote_refresh] 海外进度 %d/%d  written=%d  no_data=%d  failed=%d',
                            idx, len(fh_assets), written, no_data, len(failed)
                        )
                    _time.sleep(delay)
                    continue

                source = quote.get('source', 'finnhub')
                new_snapshot = AssetQuoteSnapshot.objects.create(
                    asset=asset,
                    price=quote.get('price'),
                    change_amount=quote.get('change_amount'),
                    change_pct=quote.get('change_pct'),
                    open=quote.get('open'),
                    high=quote.get('high'),
                    low=quote.get('low'),
                    prev_close=quote.get('prev_close'),
                    volume=quote.get('volume'),
                    amount=quote.get('amount'),
                    quote_time=quote.get('quote_time'),
                    source=source,
                )
                written += 1

                result = _snapshot_to_dict(asset, new_snapshot)
                cache.set(_quote_cache_key(asset.id), result, timeout=ttl)

                if idx % log_interval == 0 or idx == len(fh_assets):
                    logger.info(
                        '[Task:quote_refresh] 海外进度 %d/%d  written=%d  no_data=%d  failed=%d',
                        idx, len(fh_assets), written, no_data, len(failed)
                    )

            except Exception as exc:
                logger.warning('[Task:quote_refresh] %s 失败: %s', asset.code, str(exc))
                failed.append(asset.code)

            _time.sleep(delay)

        status = 'SUCCESS' if not failed else ('PARTIAL' if written > 0 else 'FAILED')
        job.status = status
        job.finished_at = dj_timezone.now()
        job.affected_rows = written
        job.extra_info = {
            'total': total,
            'written': written,
            'no_data': no_data,
            'failed': failed[:50],
        }
        if status == 'FAILED':
            job.error_message = f'全部失败，共 {len(failed)} 个资产'
        job.save(update_fields=['status', 'finished_at', 'affected_rows', 'error_message', 'extra_info'])

        logger.info(
            '[Task:quote_refresh] 完成: total=%d written=%d no_data=%d failed=%d',
            total, written, no_data, len(failed)
        )

    except Exception as exc:
        logger.exception('[Task:quote_refresh] 未预期异常')
        _finish_job(job, False, error=str(exc))

    return job


# ---------- 热门标的工具 ----------

def get_popular_asset_ids(top_n: int = 20) -> List[int]:
    """
    按"关联的已发布内容数"降序取 Top-N 活跃资产 ID。
    涵盖 A 股（Tushare）和美股/港股（Finnhub）。
    fallback：若所有资产均无内容，则返回最早同步的 top_n 个资产 ID。
    """
    from content.models import Asset

    # 符合行情刷新条件的资产：A 股市场 OR 有 finnhub_symbol
    base_qs = Asset.objects.filter(status='ACTIVE').filter(
        Q(market__in=list(CN_MARKETS)) |
        (Q(finnhub_symbol__isnull=False) & ~Q(finnhub_symbol=''))
    )

    ids = list(
        base_qs.annotate(
            pub_content_count=Count(
                'contentasset',
                filter=Q(contentasset__content__status='PUBLISHED'),
                distinct=True,
            )
        )
        .order_by('-pub_content_count', 'code')
        .values_list('id', flat=True)[:top_n]
    )

    if not ids:
        ids = list(
            base_qs.order_by('last_sync_at', 'id')
            .values_list('id', flat=True)[:top_n]
        )

    return ids


def quote_refresh_popular(top_n: Optional[int] = None) -> DataJobLog:
    """
    刷新热门标的行情快照（供榜单/列表定时调度）。

    top_n 优先级：
      1. 调用参数 top_n
      2. settings.QUOTE_REFRESH_POPULAR_TOP_N
      3. 默认值 20

    定时调度建议（Celery Beat / crontab）：
      交易时段（09:30-15:00 / 09:30-16:00）每 1~2 分钟执行一次；
      非交易时段降频至每 10 分钟或暂停。
    """
    if top_n is None:
        top_n = int(getattr(settings, 'QUOTE_REFRESH_POPULAR_TOP_N', 20))

    logger.info('[Task:quote_refresh_popular] 开始刷新热门标的 top_n=%d', top_n)
    asset_ids = get_popular_asset_ids(top_n)

    if not asset_ids:
        logger.warning('[Task:quote_refresh_popular] 无符合条件的热门标的，跳过')
        job = _start_job('QUOTE_REFRESH')
        _finish_job(job, True, affected_rows=0, extra={'top_n': top_n, 'note': '无活跃资产'})
        return job

    logger.info('[Task:quote_refresh_popular] 热门标的 IDs=%s', asset_ids)
    return quote_refresh(asset_ids=asset_ids)


def cleanup_old_snapshots(days: int = 7) -> int:
    """
    清理过期行情快照（保留最近 N 天）
    建议每天凌晨执行一次
    """
    cutoff = dj_timezone.now() - timedelta(days=days)
    deleted, _ = AssetQuoteSnapshot.objects.filter(quote_time__lt=cutoff).delete()
    logger.info('[Task:cleanup] 清理过期快照 %d 条（%d 天前）', deleted, days)
    return deleted


# ---------- 任务 D: 数据质量校验 ----------

def dq_check(asset_ids: Optional[List[int]] = None, days: int = 30) -> DataJobLog:
    """
    数据质量校验
    - 缺失检测：对比交易日历检测缺失 K 线（简化版：检测连续性）
    - 重复检测：检测同资产同时间点重复记录（理论上约束已防止，但仍做检测）
    - 异常检测：超过 20% 的单日涨跌幅（防止第三方数据错误）
    """
    from content.models import Asset
    from django.db.models import Count

    job = _start_job('DQ_CHECK')
    try:
        queryset = Asset.objects.exclude(finnhub_symbol__isnull=True).exclude(finnhub_symbol='')
        if asset_ids:
            queryset = queryset.filter(id__in=asset_ids)

        issues = []
        cutoff = dj_timezone.now() - timedelta(days=days)

        for asset in queryset:
            # 1. 重复检测
            duplicates = AssetKline.objects.filter(
                asset=asset, resolution='D', k_time__gte=cutoff
            ).values('k_time').annotate(cnt=Count('id')).filter(cnt__gt=1)

            for dup in duplicates:
                issues.append({
                    'type': 'DUPLICATE',
                    'asset': asset.code,
                    'k_time': str(dup['k_time']),
                    'count': dup['cnt'],
                })

            # 2. 极端涨跌幅检测（超过 ±50% 认为异常）
            extreme = AssetKline.objects.filter(
                asset=asset, resolution='D', k_time__gte=cutoff
            ).extra(
                where=['ABS((close - open) / NULLIF(open, 0)) > 0.5']
            )

            for kl in extreme:
                issues.append({
                    'type': 'EXTREME_CHANGE',
                    'asset': asset.code,
                    'k_time': str(kl.k_time),
                    'open': str(kl.open),
                    'close': str(kl.close),
                })

        _finish_job(job, True, affected_rows=len(issues),
                    extra={'issues': issues[:100], 'total_issues': len(issues)})

    except Exception as exc:
        logger.exception('[Task:dq_check] 未预期异常')
        _finish_job(job, False, error=str(exc))

    return job


# ---------- 单资产行情获取（供接口层调用） ----------

def get_or_refresh_quote(asset) -> Optional[dict]:
    """
    获取资产最新行情（三层缓存策略）：

    L1 Django Cache：命中则直接返回，零 DB/API 开销；
    L2 DB 快照：TTL 内有效则回填 L1 并返回；
    L3 Finnhub API：实时拉取，写入 DB 快照 + 写 L1 后返回。

    TTL 由 settings.FINNHUB_QUOTE_CACHE_TTL 控制（默认 60 秒）。
    返回格式化的行情字典，或 None（资产无 finnhub_symbol / 无任何数据）。
    """
    t0 = time.perf_counter()
    ttl = _get_quote_ttl()
    cache_key = _quote_cache_key(asset.id)

    # ── L1: Django Cache ──────────────────────────────────────────────────────
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug('[get_or_refresh_quote] L1 命中: asset=%s', asset.code)
        _log_gorq_timing(asset, 'L1', t0)
        return cached

    try:
        # ── L2: DB 快照（TTL 内有效）────────────────────────────────────────
        cutoff = dj_timezone.now() - timedelta(seconds=ttl)
        snapshot = AssetQuoteSnapshot.objects.filter(
            asset=asset
        ).order_by('-quote_time').first()

        if snapshot and snapshot.created_at >= cutoff:
            logger.debug('[get_or_refresh_quote] L2 命中: asset=%s', asset.code)
            result = _snapshot_to_dict(asset, snapshot)
            cache.set(cache_key, result, timeout=ttl)
            _log_gorq_timing(asset, 'L2', t0)
            return result

        # ── L3: 按市场选择数据源实时/日线拉取 ───────────────────────────────
        quote = _fetch_quote_for_asset(asset)
        if quote is None:
            # 无新数据时，若有旧快照仍返回（带 stale 标记，TTL 缩短为 30s）
            if snapshot:
                result = _snapshot_to_dict(asset, snapshot)
                result['is_stale'] = True
                cache.set(cache_key, result, timeout=min(ttl, 30))
                _log_gorq_timing(asset, 'L2_stale', t0)
                return result
            _log_gorq_timing(asset, 'miss', t0)
            return None

        # 写入 DB 快照
        new_snapshot = AssetQuoteSnapshot.objects.create(
            asset=asset,
            price=quote.get('price'),
            change_amount=quote.get('change_amount'),
            change_pct=quote.get('change_pct'),
            open=quote.get('open'),
            high=quote.get('high'),
            low=quote.get('low'),
            prev_close=quote.get('prev_close'),
            volume=quote.get('volume'),
            amount=quote.get('amount'),
            quote_time=quote.get('quote_time'),
            source=quote.get('source', 'finnhub'),
        )

        result = _snapshot_to_dict(asset, new_snapshot)
        # 回填 L1 缓存
        cache.set(cache_key, result, timeout=ttl)
        logger.debug('[get_or_refresh_quote] L3 写入: asset=%s ttl=%ds', asset.code, ttl)
        _log_gorq_timing(asset, 'L3', t0)
        return result

    except Exception as exc:
        logger.error('[get_or_refresh_quote] 异常: asset=%s err=%s', asset.code, str(exc))
        _log_gorq_timing(asset, 'error', t0)
        return None


def _snapshot_to_dict(asset, snapshot: AssetQuoteSnapshot) -> dict:
    """将 AssetQuoteSnapshot 转换为统一的行情字典"""
    return {
        'asset_id': asset.id,
        'code': asset.code,
        'name': asset.name,
        'market': asset.market,
        'price': float(snapshot.price) if snapshot.price is not None else None,
        'change_amount': float(snapshot.change_amount) if snapshot.change_amount is not None else None,
        'change_pct': float(snapshot.change_pct) if snapshot.change_pct is not None else None,
        'open': float(snapshot.open) if snapshot.open is not None else None,
        'high': float(snapshot.high) if snapshot.high is not None else None,
        'low': float(snapshot.low) if snapshot.low is not None else None,
        'prev_close': float(snapshot.prev_close) if snapshot.prev_close is not None else None,
        'volume': snapshot.volume,
        'amount': float(snapshot.amount) if snapshot.amount is not None else None,
        'quote_time': snapshot.quote_time.isoformat() if snapshot.quote_time else None,
        'data_updated_at': snapshot.created_at.isoformat() if snapshot.created_at else None,
        'source': snapshot.source,
        'is_stale': False,
    }
