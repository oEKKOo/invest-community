"""标的静态信息序列化结果缓存（不含 quote，quote 仍走 get_or_refresh_quote）。"""
import copy

from django.conf import settings
from django.core.cache import cache


def asset_detail_static_cache_key(asset_id: int) -> str:
    return f'asset:detail_static:v1:{asset_id}'


def get_cached_asset_static(asset_id: int):
    """返回缓存中 AssetSerializer 字典的副本，未命中返回 None。"""
    key = asset_detail_static_cache_key(asset_id)
    data = cache.get(key)
    if data is None:
        return None
    return copy.deepcopy(data)


def set_cached_asset_static(asset_id: int, serializer_data: dict) -> None:
    ttl = int(getattr(settings, 'ASSET_DETAIL_STATIC_CACHE_TTL', 600))
    cache.set(asset_detail_static_cache_key(asset_id), serializer_data, ttl)


def invalidate_asset_detail_cache(asset_id: int) -> None:
    cache.delete(asset_detail_static_cache_key(asset_id))
