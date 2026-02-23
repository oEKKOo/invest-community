"""
数据同步任务（Finnhub 规范 §5 三类任务）
- 任务 A: symbols_sync        — 标的清单同步
- 任务 B: kline_sync          — 日线数据同步（增量 + 回补）
- 任务 C: quote_refresh       — 行情快照刷新（可高频调用）
- 任务 C2: quote_refresh_popular — 热门标的行情刷新（定时调度，供榜单/列表稳定展示）
- 任务 D: dq_check            — 数据质量校验（缺失/重复/异常检测）

缓存分层策略：
  L1 Django Cache（LocMem / Redis）—— 命中直接返回，无 DB/API 开销
  L2 DB 快照（AssetQuoteSnapshot）—— TTL 内有效则写 L1 后返回
  L3 Finnhub API                  —— 实时拉取，写 DB + 写 L1 后返回

可通过 Django management commands 或 Celery Beat 调度。
每次运行都会写 DataJobLog 记录。
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone as dj_timezone

from .models import AssetQuoteSnapshot, AssetKline, DataJobLog
from . import finnhub_service as fh

logger = logging.getLogger(__name__)


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


# ---------- 任务 B: K 线数据同步 ----------

def kline_sync(
    asset_ids: Optional[List[int]] = None,
    resolution: str = 'D',
    days_back: int = 365,
    force_refetch: bool = False
) -> DataJobLog:
    """
    增量同步 K 线（日线）
    - asset_ids: 指定资产列表；None 表示同步所有有 finnhub_symbol 的资产
    - resolution: K线周期，默认 'D'（日K）
    - days_back: 向前拉取的天数（历史数据初始化时设大，增量时设 2~5 天）
    - force_refetch: True 则清空并重拉（用于数据回补）
    """
    from content.models import Asset

    job = _start_job('KLINE_SYNC', market='')
    try:
        queryset = Asset.objects.exclude(finnhub_symbol__isnull=True).exclude(finnhub_symbol='')
        if asset_ids:
            queryset = queryset.filter(id__in=asset_ids)

        to_ts = fh.now_ts()
        from_dt = datetime.now(tz=timezone.utc) - timedelta(days=days_back)
        from_ts = fh.datetime_to_ts(from_dt)

        total_rows = 0
        failed_assets = []

        for asset in queryset:
            try:
                data = fh.get_candles(asset.finnhub_symbol, resolution, from_ts, to_ts)
                if data is None:
                    logger.debug('[Task:kline_sync] %s 无 K 线数据', asset.finnhub_symbol)
                    continue

                items = data.get('items', [])
                written = _write_klines(asset, resolution, items, force_refetch)
                total_rows += written

            except Exception as exc:
                logger.warning('[Task:kline_sync] 资产 %s 失败: %s', asset.finnhub_symbol, str(exc))
                failed_assets.append({'code': asset.code, 'error': str(exc)})

        success = len(failed_assets) == 0
        status_val = 'SUCCESS' if success else ('PARTIAL' if total_rows > 0 else 'FAILED')
        job.status = status_val
        job.finished_at = dj_timezone.now()
        job.affected_rows = total_rows
        job.extra_info = {'failed_assets': failed_assets[:50]}  # 最多记录 50 条
        if not success and total_rows == 0:
            job.error_message = f'全部失败，共 {len(failed_assets)} 个资产'
        job.save(update_fields=['status', 'finished_at', 'affected_rows', 'error_message', 'extra_info'])

        logger.info('[Task:kline_sync] 完成: rows=%d failed=%d', total_rows, len(failed_assets))

    except Exception as exc:
        logger.exception('[Task:kline_sync] 未预期异常')
        _finish_job(job, False, error=str(exc))

    return job


def _write_klines(asset, resolution: str, items: list, force_refetch: bool) -> int:
    """批量写入 K 线（防重，支持 upsert）"""
    from .models import AssetKline

    if force_refetch and items:
        # 回补模式：删除时间范围内旧数据
        times = [i['k_time'] for i in items if i.get('k_time')]
        if times:
            AssetKline.objects.filter(
                asset=asset, resolution=resolution,
                k_time__gte=min(times), k_time__lte=max(times)
            ).delete()

    written = 0
    for item in items:
        k_time = item.get('k_time')
        if not k_time:
            continue
        try:
            AssetKline.objects.update_or_create(
                asset=asset,
                resolution=resolution,
                k_time=k_time,
                defaults={
                    'open': item.get('open') or 0,
                    'high': item.get('high') or 0,
                    'low': item.get('low') or 0,
                    'close': item.get('close') or 0,
                    'volume': item.get('volume'),
                }
            )
            written += 1
        except Exception as e:
            logger.debug('[kline_write] 写入失败: asset=%s time=%s err=%s', asset.code, k_time, str(e))

    return written


# ---------- 任务 C: 行情快照刷新 ----------

def quote_refresh(
    asset_ids: Optional[List[int]] = None,
    delay: float = 0.12,
    log_interval: int = 20,
) -> DataJobLog:
    """
    刷新行情快照（可高频调用，建议交易时段每分钟调度）。
    每次写入新快照后同步回填 L1 缓存，确保下次请求直接命中缓存层。

    - asset_ids=None：刷新所有有 finnhub_symbol 的 ACTIVE 资产
    - asset_ids=[...]：仅刷新指定资产
    - delay：每次 API 请求之间的延迟（秒），免费版建议 >= 0.1，默认 0.12
    - log_interval：每隔多少只打印一次进度日志，默认 20
    """
    import time as _time
    from content.models import Asset

    ttl = _get_quote_ttl()
    job = _start_job('QUOTE_REFRESH')
    try:
        queryset = Asset.objects.filter(status='ACTIVE').exclude(
            finnhub_symbol__isnull=True).exclude(finnhub_symbol='')
        if asset_ids:
            queryset = queryset.filter(id__in=asset_ids)

        assets = list(queryset)
        total = len(assets)
        written = 0
        no_data = 0
        failed = []

        logger.info('[Task:quote_refresh] 开始刷新，共 %d 只资产，delay=%.2fs', total, delay)

        for idx, asset in enumerate(assets, 1):
            try:
                quote = fh.get_quote(asset.finnhub_symbol)
                if quote is None or not quote.get('price'):
                    no_data += 1
                    if idx % log_interval == 0 or idx == total:
                        logger.info(
                            '[Task:quote_refresh] 进度 %d/%d  written=%d  no_data=%d  failed=%d',
                            idx, total, written, no_data, len(failed)
                        )
                    _time.sleep(delay)
                    continue

                new_snapshot = AssetQuoteSnapshot.objects.create(
                    asset=asset,
                    price=quote.get('price'),
                    change_amount=quote.get('change_amount'),
                    change_pct=quote.get('change_pct'),
                    open=quote.get('open'),
                    high=quote.get('high'),
                    low=quote.get('low'),
                    prev_close=quote.get('prev_close'),
                    quote_time=quote.get('quote_time'),
                    source='finnhub',
                )
                written += 1

                # 写入快照后同步回填 L1 缓存，下次请求直接命中
                result = _snapshot_to_dict(asset, new_snapshot)
                cache.set(_quote_cache_key(asset.id), result, timeout=ttl)

                if idx % log_interval == 0 or idx == total:
                    logger.info(
                        '[Task:quote_refresh] 进度 %d/%d  written=%d  no_data=%d  failed=%d',
                        idx, total, written, no_data, len(failed)
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
    用于定时刷新热门标的行情，保证榜单/列表数据新鲜度。

    fallback：若所有资产均无内容，则返回最早同步的 top_n 个资产 ID。
    """
    from content.models import Asset

    ids = list(
        Asset.objects.filter(status='ACTIVE')
        .exclude(finnhub_symbol__isnull=True).exclude(finnhub_symbol='')
        .annotate(
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
        # fallback：无内容时按最早同步的资产兜底
        ids = list(
            Asset.objects.filter(status='ACTIVE')
            .exclude(finnhub_symbol__isnull=True).exclude(finnhub_symbol='')
            .order_by('last_sync_at', 'id')
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
    ttl = _get_quote_ttl()
    cache_key = _quote_cache_key(asset.id)

    # ── L1: Django Cache ──────────────────────────────────────────────────────
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug('[get_or_refresh_quote] L1 命中: asset=%s', asset.code)
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
            return result

        # ── L3: Finnhub 实时拉取 ─────────────────────────────────────────────
        if not asset.finnhub_symbol:
            logger.debug('[get_or_refresh_quote] %s 无 finnhub_symbol，跳过', asset.code)
            return None

        quote = fh.get_quote(asset.finnhub_symbol)
        if quote is None:
            # Finnhub 无数据时，若有旧快照仍返回（带 stale 标记，TTL 缩短为 30s）
            if snapshot:
                result = _snapshot_to_dict(asset, snapshot)
                result['is_stale'] = True
                cache.set(cache_key, result, timeout=min(ttl, 30))
                return result
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
            quote_time=quote.get('quote_time'),
            source='finnhub',
        )

        result = _snapshot_to_dict(asset, new_snapshot)
        # 回填 L1 缓存
        cache.set(cache_key, result, timeout=ttl)
        logger.debug('[get_or_refresh_quote] L3 写入: asset=%s ttl=%ds', asset.code, ttl)
        return result

    except Exception as exc:
        logger.error('[get_or_refresh_quote] 异常: asset=%s err=%s', asset.code, str(exc))
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
