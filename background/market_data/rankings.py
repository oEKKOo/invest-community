"""涨跌幅榜单：供 /api/market/rankings/ 与 Dashboard 聚合复用。"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.db.models import OuterRef, Subquery

from .models import AssetQuoteSnapshot


def compute_rankings_payload(
    rank_type: str, limit: int, market: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    返回 (payload, error_message)。error_message 非空表示参数不合法。
    """
    limit = min(max(1, limit), 50)

    latest_times = AssetQuoteSnapshot.objects.filter(
        asset=OuterRef('asset')
    ).order_by('-quote_time').values('quote_time')[:1]

    snapshots = AssetQuoteSnapshot.objects.filter(
        quote_time=Subquery(latest_times),
        price__isnull=False,
        change_pct__isnull=False,
    ).select_related('asset')

    if market:
        snapshots = snapshots.filter(asset__market=market)

    if rank_type == 'gainers':
        snapshots = snapshots.order_by('-change_pct')[:limit]
    elif rank_type == 'losers':
        snapshots = snapshots.order_by('change_pct')[:limit]
    elif rank_type == 'active':
        snapshots = snapshots.filter(volume__isnull=False).order_by('-volume')[:limit]
    else:
        return None, '不支持的 type'

    items = []
    for i, snap in enumerate(snapshots, 1):
        items.append(
            {
                'rank': i,
                'assetId': snap.asset_id,
                'code': snap.asset.code,
                'name': snap.asset.name,
                'market': snap.asset.market,
                'price': float(snap.price) if snap.price else None,
                'changePct': float(snap.change_pct) if snap.change_pct else None,
                'change': float(snap.change_amount) if snap.change_amount else None,
                'volume': snap.volume,
                'quoteTime': snap.quote_time.isoformat() if snap.quote_time else None,
            }
        )

    payload = {
        'type': rank_type,
        'market': market,
        'items': items,
    }
    return payload, None


def get_cached_rankings_payload(
    rank_type: str, limit: int, market: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """带缓存的榜单数据，与 market_rankings 视图共用缓存键。"""
    cache_ttl = int(getattr(settings, 'MARKET_RANKINGS_CACHE_TTL', 20))
    cache_key = f'rankings:v2:{rank_type}:{market or "ALL"}:{min(limit, 50)}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached, None
    payload, err = compute_rankings_payload(rank_type, limit, market)
    if err:
        return None, err
    cache.set(cache_key, payload, cache_ttl)
    return payload, None
