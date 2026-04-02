"""
行情数据接口视图层
对应 work.mdc 中的新增/改动接口：
- GET  /api/assets/{asset_id}/quote/          # 6.4 单资产最新行情
- GET  /api/assets/{asset_id}/kline/          # 6.5 K线数据
- GET  /api/assets/{asset_id}/intraday/       # 6.6 分时数据
- POST /api/assets/quotes/                    # 6.7 批量行情
- GET  /api/assets/{asset_id}/quote/stream/   # 6.8 行情推送（SSE）
- GET  /api/assets/{asset_id}/contents/       # 资产内容（更通用版）
- GET  /api/market/jobs/                      # 后台任务监控
- POST /api/market/jobs/trigger/              # 手动触发任务

数据源路由规则：
  market in {SH,SZ,BJ} → Tushare（A 股日线数据）
  market HK 日 K       → Tushare hk_daily（库空回补）；分钟线等仍可用 Finnhub
  其他（如 US）         → Finnhub（实时行情 + K 线）
"""
import json
import logging
import time
from datetime import datetime, timedelta, timezone as py_tz
from typing import Optional

from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Max
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from content.models import Asset, Content
from content.serializers import ContentListSerializer
from .models import AssetQuoteSnapshot, AssetKline, DataJobLog
from .serializers import (
    QuoteSnapshotSerializer, KlineItemSerializer,
    DataJobLogSerializer, BulkQuoteRequestSerializer
)
from .tasks import (
    get_or_refresh_quote, kline_sync, quote_refresh,
    quote_refresh_popular, get_popular_asset_ids,
    dq_check, cleanup_old_snapshots,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 6.4  单资产最新行情
# GET /api/assets/{asset_id}/quote/
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def asset_quote(request, pk):
    """
    获取资产最新行情
    优先读取 60 秒内的快照，否则实时拉取 Finnhub 并写入快照
    """
    asset = get_object_or_404(Asset, pk=pk)
    quote_data = get_or_refresh_quote(asset)

    if quote_data is None:
        return Response({
            'code': 4040,
            'message': f'暂无 {asset.code} 的行情数据，请确认资产的 finnhub_symbol 已配置'
        }, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'code': 0,
        'data': {
            'assetId': quote_data['asset_id'],
            'code': quote_data['code'],
            'name': quote_data['name'],
            'market': quote_data['market'],
            'quoteTime': quote_data['quote_time'],
            'price': quote_data['price'],
            'change': quote_data['change_amount'],
            'changePct': quote_data['change_pct'],
            'open': quote_data['open'],
            'high': quote_data['high'],
            'low': quote_data['low'],
            'prevClose': quote_data['prev_close'],
            'volume': quote_data['volume'],
            'amount': quote_data['amount'],
            'dataUpdatedAt': quote_data['data_updated_at'],
            'isStale': quote_data.get('is_stale', False),
        }
    })


# ─────────────────────────────────────────────────────────────
# 6.5  K 线数据
# GET /api/assets/{asset_id}/kline/
# Query: interval(1d|60m|15m|5m|1m), limit(默认200), from, to
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def asset_kline(request, pk):
    """
    获取资产 K 线数据（优先读数据库，库中无数据时从 Finnhub 拉取）
    interval 映射关系：
      1d  → resolution='D'
      60m → resolution='60'
      15m → resolution='15'
      5m  → resolution='5'
      1m  → resolution='1'
    """
    asset = get_object_or_404(Asset, pk=pk)

    interval = request.query_params.get('interval', '1d')
    limit = min(int(request.query_params.get('limit', 200)), 500)
    from_param = request.query_params.get('from')
    to_param = request.query_params.get('to')

    # interval → resolution 映射
    interval_map = {
        '1d': 'D', '1D': 'D',
        '60m': '60', '1h': '60',
        '30m': '30',
        '15m': '15',
        '5m': '5',
        '1m': '1',
        'W': 'W', '1w': 'W',
        'M': 'M', '1mo': 'M',
    }
    resolution = interval_map.get(interval, 'D')
    cache_ttl = int(getattr(settings, 'KLINE_API_CACHE_TTL', 60))
    cache_key = f'kline:v1:{asset.id}:{resolution}:{limit}:{from_param or ""}:{to_param or ""}'
    cached_payload = cache.get(cache_key)
    if cached_payload is not None:
        return Response({'code': 0, 'data': cached_payload})

    # 构建查询
    queryset = AssetKline.objects.filter(asset=asset, resolution=resolution)

    if from_param:
        try:
            from_dt = _parse_date_param(from_param)
            queryset = queryset.filter(k_time__gte=from_dt)
        except ValueError:
            return Response({'code': 4001, 'message': 'from 参数格式错误，支持 YYYY-MM-DD 或 ISO 时间'})

    if to_param:
        try:
            to_dt = _parse_date_param(to_param)
            queryset = queryset.filter(k_time__lte=to_dt)
        except ValueError:
            return Response({'code': 4001, 'message': 'to 参数格式错误，支持 YYYY-MM-DD 或 ISO 时间'})

    queryset = queryset.order_by('-k_time')[:limit]
    klines = list(queryset)

    # 数据库无数据时，按市场选择数据源拉取并落库
    if not klines:
        from .tasks import _write_klines
        from .tushare_service import CN_MARKETS
        from . import tushare_service as ts_svc

        if asset.market in CN_MARKETS and resolution == 'D':
            # A 股日线 → Tushare
            ts_code = ts_svc.get_tushare_code(asset.code, asset.market)
            if ts_code and ts_svc.is_api_token_configured():
                logger.info('[kline] 数据库无 %s [%s] 数据，从 Tushare 拉取', asset.code, resolution)
                days = 365
                from_dt = datetime.now(tz=py_tz.utc) - timedelta(days=days)
                start_str = ts_svc.date_to_tushare_str(from_dt)
                end_str   = ts_svc.date_to_tushare_str(datetime.now(tz=py_tz.utc))
                items = ts_svc.get_daily_klines(ts_code, start_str, end_str)
                if items:
                    _write_klines(asset, 'D', items, force_refetch=False)
                    queryset = AssetKline.objects.filter(
                        asset=asset, resolution=resolution
                    ).order_by('-k_time')[:limit]
                    klines = list(queryset)

        elif asset.market == 'HK' and resolution == 'D' and ts_svc.is_api_token_configured():
            ts_code = ts_svc.get_hk_tushare_code(asset.code)
            if ts_code:
                logger.info('[kline] 数据库无 %s [%s] 数据，从 Tushare 港股拉取', asset.code, resolution)
                days = 365
                from_dt = datetime.now(tz=py_tz.utc) - timedelta(days=days)
                start_str = ts_svc.date_to_tushare_str(from_dt)
                end_str   = ts_svc.date_to_tushare_str(datetime.now(tz=py_tz.utc))
                items = ts_svc.get_hk_daily_klines(ts_code, start_str, end_str)
                if items:
                    _write_klines(asset, 'D', items, force_refetch=False)
                    queryset = AssetKline.objects.filter(
                        asset=asset, resolution=resolution
                    ).order_by('-k_time')[:limit]
                    klines = list(queryset)

        if not klines and asset.finnhub_symbol:
            # 美股 / 港股分钟线 / 港股日 K 未走通 Tushare 时回退
            from . import finnhub_service as fh
            logger.info('[kline] 数据库无 %s [%s] 数据，从 Finnhub 拉取', asset.code, resolution)
            days = 365 if resolution == 'D' else 30
            to_ts = fh.now_ts()
            from_ts = fh.datetime_to_ts(datetime.now(tz=py_tz.utc) - timedelta(days=days))
            data = fh.get_candles(asset.finnhub_symbol, resolution, from_ts, to_ts)
            if data:
                _write_klines(asset, resolution, data['items'], force_refetch=False)
                queryset = AssetKline.objects.filter(
                    asset=asset, resolution=resolution
                ).order_by('-k_time')[:limit]
                klines = list(queryset)

    # 按时间正序排列返回给前端（ECharts 需要升序）
    klines.reverse()

    serializer = KlineItemSerializer(klines, many=True)
    payload = {
        'assetId': asset.id,
        'code': asset.code,
        'interval': interval,
        'resolution': resolution,
        'count': len(klines),
        'items': serializer.data,
    }
    cache.set(cache_key, payload, cache_ttl)
    return Response({'code': 0, 'data': payload})


# ─────────────────────────────────────────────────────────────
# 6.6  分时数据（当日走势）
# GET /api/assets/{asset_id}/intraday/
# Query: date(YYYY-MM-DD 默认今天), interval(1m|5m)
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def asset_intraday(request, pk):
    """
    获取当日分时数据（分钟 K 线聚合展示）
    数据来自 AssetKline（1/5 分钟周期）
    若无分钟级数据，从 Finnhub 拉取并落库
    """
    asset = get_object_or_404(Asset, pk=pk)

    date_str = request.query_params.get('date', timezone.now().strftime('%Y-%m-%d'))
    interval = request.query_params.get('interval', '5m')

    interval_map = {'1m': '1', '5m': '5', '15m': '15'}
    resolution = interval_map.get(interval, '5')

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'code': 4001, 'message': 'date 格式错误，应为 YYYY-MM-DD'})

    # 查询指定日期的分钟 K 线
    start_dt = datetime(target_date.year, target_date.month, target_date.day,
                        0, 0, 0, tzinfo=py_tz.utc)
    end_dt = start_dt + timedelta(days=1)

    klines = AssetKline.objects.filter(
        asset=asset, resolution=resolution,
        k_time__gte=start_dt, k_time__lt=end_dt
    ).order_by('k_time')

    # 无数据时按市场选择数据源拉取
    if not klines.exists():
        from .tasks import _write_klines
        from .tushare_service import CN_MARKETS

        if asset.market in CN_MARKETS:
            # A 股：Tushare 分钟数据权限较高，降级为日线数据提示
            # 注：Tushare 免费积分不支持分钟线，此处仅做友好提示
            logger.info('[intraday] A股 %s 暂不支持分钟线（Tushare 积分限制）', asset.code)
        elif asset.finnhub_symbol:
            from . import finnhub_service as fh
            from_ts = fh.datetime_to_ts(start_dt)
            to_ts = fh.datetime_to_ts(end_dt)
            data = fh.get_candles(asset.finnhub_symbol, resolution, from_ts, to_ts)
            if data:
                _write_klines(asset, resolution, data['items'], force_refetch=False)
                klines = AssetKline.objects.filter(
                    asset=asset, resolution=resolution,
                    k_time__gte=start_dt, k_time__lt=end_dt
                ).order_by('k_time')

    # 构造分时响应：每分钟价格 + 均价
    items = []
    cumulative_volume = 0
    cumulative_amount = 0

    for kl in klines:
        cumulative_volume += kl.volume or 0
        price = float(kl.close) if kl.close else None
        avg_price = None
        if cumulative_volume and price:
            cumulative_amount += float(kl.close) * (kl.volume or 0)
            avg_price = round(cumulative_amount / cumulative_volume, 4) if cumulative_volume else None

        items.append({
            'time': kl.k_time.strftime('%H:%M'),
            'price': price,
            'avgPrice': avg_price,
            'volume': kl.volume,
            'open': float(kl.open) if kl.open else None,
            'high': float(kl.high) if kl.high else None,
            'low': float(kl.low) if kl.low else None,
        })

    return Response({
        'code': 0,
        'data': {
            'assetId': asset.id,
            'code': asset.code,
            'date': date_str,
            'interval': interval,
            'items': items,
        }
    })


# ─────────────────────────────────────────────────────────────
# 6.7  批量获取最新行情
# POST /api/assets/quotes/
# Body: { "assetIds": [1, 2, 3] }
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def asset_quotes_bulk(request):
    """
    批量获取资产最新行情（列表页/组合页必备）
    最多支持 50 个资产同时查询
    """
    serializer = BulkQuoteRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'code': 4001,
            'message': '参数错误',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    asset_ids = serializer.validated_data['assetIds']
    assets = Asset.objects.filter(id__in=asset_ids)

    # 批量从快照表获取（最新快照，不实时调 Finnhub）
    # 对于批量接口，读快照库即可，不做实时拉取（避免大量 API 调用）
    asset_map = {a.id: a for a in assets}
    results = []

    latest_times = AssetQuoteSnapshot.objects.filter(
        asset_id__in=asset_ids
    ).values('asset_id').annotate(latest_quote_time=Max('quote_time'))
    latest_time_map = {row['asset_id']: row['latest_quote_time'] for row in latest_times}

    snapshot_q = Q()
    for aid, latest_quote_time in latest_time_map.items():
        if latest_quote_time is not None:
            snapshot_q |= Q(asset_id=aid, quote_time=latest_quote_time)

    latest_snapshot_map = {}
    if snapshot_q:
        latest_snapshots = AssetQuoteSnapshot.objects.filter(snapshot_q)
        latest_snapshot_map = {snap.asset_id: snap for snap in latest_snapshots}

    for asset_id in asset_ids:
        asset = asset_map.get(asset_id)
        if not asset:
            results.append({'assetId': asset_id, 'error': '资产不存在'})
            continue

        snapshot = latest_snapshot_map.get(asset_id)

        if snapshot:
            results.append({
                'assetId': asset_id,
                'code': asset.code,
                'name': asset.name,
                'market': asset.market,
                'price': float(snapshot.price) if snapshot.price else None,
                'changePct': float(snapshot.change_pct) if snapshot.change_pct else None,
                'change': float(snapshot.change_amount) if snapshot.change_amount else None,
                'quoteTime': snapshot.quote_time.isoformat() if snapshot.quote_time else None,
                'dataUpdatedAt': snapshot.created_at.isoformat() if snapshot.created_at else None,
            })
        else:
            results.append({
                'assetId': asset_id,
                'code': asset.code,
                'name': asset.name,
                'market': asset.market,
                'price': None,
                'changePct': None,
                'change': None,
                'quoteTime': None,
                'dataUpdatedAt': None,
            })

    return Response({
        'code': 0,
        'data': {
            'items': results,
            'total': len(results),
        }
    })


# ─────────────────────────────────────────────────────────────
# 6.8  行情推送 SSE
# GET /api/assets/{asset_id}/quote/stream/
# 注意：此视图不使用 @api_view，绕过 DRF 内容协商（避免 406 错误）
# ─────────────────────────────────────────────────────────────

@csrf_exempt
def asset_quote_stream(request, pk):
    """
    行情 SSE 推送（Server-Sent Events）
    - 不使用 @api_view，绕过 DRF 内容协商（text/event-stream 不在默认渲染器中）
    - 前端使用 EventSource 接入，JWT token 通过 ?token= 查询参数传入
    - 每 5 秒推送一次，调用 get_or_refresh_quote 获取最新行情（有 60s 缓存）
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        asset = Asset.objects.get(pk=pk)
    except Asset.DoesNotExist:
        return JsonResponse({'error': '资产不存在'}, status=404)

    def event_generator():
        """生成器：每 5 秒推送一次最新行情（通过 get_or_refresh_quote 实时拉取 Finnhub）"""
        max_duration = 300  # 最多推送 5 分钟
        interval = 5        # 推送间隔（秒）；Finnhub 免费版 60s 缓存，此处稍微拉长避免无效调用
        elapsed = 0

        while elapsed < max_duration:
            try:
                quote_data = get_or_refresh_quote(asset)

                if quote_data:
                    data = {
                        'assetId': asset.id,
                        'code': asset.code,
                        'name': asset.name,
                        'price': quote_data['price'],
                        'change': quote_data['change_amount'],
                        'changePct': quote_data['change_pct'],
                        'open': quote_data['open'],
                        'high': quote_data['high'],
                        'low': quote_data['low'],
                        'prevClose': quote_data['prev_close'],
                        'volume': quote_data.get('volume'),
                        'quoteTime': quote_data['quote_time'],
                        'dataUpdatedAt': quote_data['data_updated_at'],
                        'isStale': quote_data.get('is_stale', False),
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                else:
                    yield f"data: {json.dumps({'assetId': asset.id, 'code': asset.code, 'price': None, 'error': '暂无行情数据'})}\n\n"

            except Exception as e:
                logger.error('[SSE] 推送异常: asset=%s err=%s', asset.code, str(e))
                yield f"event: error\ndata: {json.dumps({'message': '行情获取失败'})}\n\n"

            time.sleep(interval)
            elapsed += interval

        # 超时关闭
        yield "event: close\ndata: {}\n\n"

    response = StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # 禁止 Nginx 缓冲，保证实时推送
    response['Access-Control-Allow-Origin'] = '*'
    return response


# ─────────────────────────────────────────────────────────────
# 资产内容聚合（更通用版）
# GET /api/assets/{asset_id}/contents/
# Query: type(POST|ARTICLE), sort(new|hot), page, pageSize
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def asset_contents(request, pk):
    """
    资产内容聚合（通用版，取代 /posts/ 路由，向后兼容）
    支持按内容类型过滤（未来可扩展 ARTICLE/REVIEW 等类型）
    """
    asset = get_object_or_404(Asset, pk=pk)

    content_type = request.query_params.get('type')  # POST|ARTICLE 等
    sort_param = request.query_params.get('sort', 'new')
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('pageSize', 20))

    queryset = Content.objects.filter(
        assets=asset,
        status='PUBLISHED'
    ).select_related('author').prefetch_related('assets')

    if content_type:
        # 预留：将来 Content 模型加 content_type 字段时在此过滤
        pass

    if sort_param == 'hot':
        queryset = queryset.order_by('-like_count', '-comment_count', '-created_at')
    else:
        queryset = queryset.order_by('-created_at')

    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = queryset[start:end]

    serializer = ContentListSerializer(items, many=True, context={'request': request})

    return Response({
        'code': 0,
        'data': {
            'assetId': asset.id,
            'assetCode': asset.code,
            'assetName': asset.name,
            'items': serializer.data,
            'page': page,
            'pageSize': page_size,
            'total': total,
        }
    })


# ─────────────────────────────────────────────────────────────
# 后台：数据任务监控接口
# GET  /api/market/jobs/          — 任务日志列表
# POST /api/market/jobs/trigger/  — 手动触发任务
# GET  /api/market/status/        — 系统状态（Key 是否配置等）
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_log_list(request):
    """
    数据任务日志列表（仅管理员可访问）
    支持筛选：job_type, status
    """
    user = request.user
    if user.role not in ['MODERATOR', 'ADMIN']:
        return Response({'code': 4030, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    queryset = DataJobLog.objects.all()

    job_type = request.query_params.get('jobType')
    if job_type:
        queryset = queryset.filter(job_type=job_type)

    job_status = request.query_params.get('status')
    if job_status:
        queryset = queryset.filter(status=job_status)

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('pageSize', 20))
    total = queryset.count()
    start = (page - 1) * page_size
    items = queryset[start:start + page_size]

    serializer = DataJobLogSerializer(items, many=True)
    return Response({
        'code': 0,
        'data': {
            'items': serializer.data,
            'page': page,
            'pageSize': page_size,
            'total': total,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_job(request):
    """
    手动触发数据同步任务（管理员后台回补入口）
    支持的 jobType：
    - SYMBOLS_SYNC:    同步股票列表（美股/港股），需传 exchange, market
    - CN_SYMBOLS_SYNC: 同步 A 股标的列表（Tushare），可传 listStatus
    - HK_SYMBOLS_SYNC: 同步港股标的列表（Tushare hk_basic），可传 listStatus
    - KLINE_SYNC:      同步K线，可传 assetIds[], daysBack, resolution, marketFilter
    - QUOTE_REFRESH:   刷新行情快照（A股+美股自动路由），可传 assetIds[]
    - DQ_CHECK:        数据质量校验，可传 assetIds[]
    - CLEANUP:         清理过期快照，可传 daysToKeep
    """
    user = request.user
    if user.role not in ['MODERATOR', 'ADMIN']:
        return Response({'code': 4030, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    job_type = request.data.get('jobType')
    if not job_type:
        return Response({'code': 4001, 'message': 'jobType 必填'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if job_type == 'SYMBOLS_SYNC':
            from .tasks import symbols_sync
            exchange = request.data.get('exchange', 'US')
            market = request.data.get('market', 'US')
            job = symbols_sync(exchange=exchange, market=market)
            return Response({'code': 0, 'data': DataJobLogSerializer(job).data})

        elif job_type == 'CN_SYMBOLS_SYNC':
            from .tasks import cn_symbols_sync
            list_status = request.data.get('listStatus', 'L')
            job = cn_symbols_sync(list_status=list_status)
            return Response({'code': 0, 'data': DataJobLogSerializer(job).data})

        elif job_type == 'HK_SYMBOLS_SYNC':
            from .tasks import hk_symbols_sync
            list_status = request.data.get('listStatus', 'L')
            job = hk_symbols_sync(list_status=list_status)
            return Response({'code': 0, 'data': DataJobLogSerializer(job).data})

        elif job_type == 'KLINE_SYNC':
            asset_ids = request.data.get('assetIds')
            days_back = int(request.data.get('daysBack', 365))
            resolution = request.data.get('resolution', 'D')
            force = bool(request.data.get('forceRefetch', False))
            market_filter = request.data.get('marketFilter')
            job = kline_sync(
                asset_ids=asset_ids,
                resolution=resolution,
                days_back=days_back,
                force_refetch=force,
                market_filter=market_filter,
            )
            return Response({'code': 0, 'data': DataJobLogSerializer(job).data})

        elif job_type == 'QUOTE_REFRESH':
            asset_ids = request.data.get('assetIds')
            job = quote_refresh(asset_ids=asset_ids)
            return Response({'code': 0, 'data': DataJobLogSerializer(job).data})

        elif job_type == 'QUOTE_REFRESH_POPULAR':
            top_n = request.data.get('topN')
            top_n = int(top_n) if top_n else None
            job = quote_refresh_popular(top_n=top_n)
            return Response({'code': 0, 'data': DataJobLogSerializer(job).data})

        elif job_type == 'DQ_CHECK':
            asset_ids = request.data.get('assetIds')
            days = int(request.data.get('days', 30))
            job = dq_check(asset_ids=asset_ids, days=days)
            return Response({'code': 0, 'data': DataJobLogSerializer(job).data})

        elif job_type == 'CLEANUP':
            days_to_keep = int(request.data.get('daysToKeep', 7))
            deleted = cleanup_old_snapshots(days=days_to_keep)
            return Response({'code': 0, 'data': {'deleted': deleted}})

        else:
            return Response({
                'code': 4001,
                'message': f'不支持的 jobType: {job_type}'
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as exc:
        logger.exception('[trigger_job] 任务执行异常: jobType=%s', job_type)
        return Response({
            'code': 5000,
            'message': f'任务执行异常: {str(exc)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def market_status(request):
    """
    系统状态查询（Key/Token 配置状态 + 最近任务状态）
    不暴露 Key/Token 本身，只返回是否已配置
    """
    from .finnhub_service import is_api_key_configured as fh_configured
    from .tushare_service import is_api_token_configured as ts_configured

    # 最近各类任务状态
    recent_jobs = {}
    for job_type in ['SYMBOLS_SYNC', 'KLINE_SYNC', 'QUOTE_REFRESH', 'DQ_CHECK']:
        job = DataJobLog.objects.filter(job_type=job_type).order_by('-started_at').first()
        if job:
            recent_jobs[job_type] = {
                'status': job.status,
                'started_at': job.started_at.isoformat(),
                'affected_rows': job.affected_rows,
            }
        else:
            recent_jobs[job_type] = None

    # 数据库统计（按市场分组）
    from content.models import Asset
    from .tushare_service import CN_MARKETS
    asset_count = Asset.objects.count()
    cn_asset_count = Asset.objects.filter(market__in=list(CN_MARKETS)).count()
    snapshot_count = AssetQuoteSnapshot.objects.count()
    kline_count = AssetKline.objects.count()

    return Response({
        'code': 0,
        'data': {
            'finnhubKeyConfigured': fh_configured(),
            'tushareTokenConfigured': ts_configured(),
            'assetCount': asset_count,
            'cnAssetCount': cn_asset_count,
            'snapshotCount': snapshot_count,
            'klineCount': kline_count,
            'recentJobs': recent_jobs,
        }
    })


# ─────────────────────────────────────────────────────────────
# 涨跌幅榜单
# GET /api/market/rankings/
# Query: type(gainers|losers|active), limit(默认10)
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def market_rankings(request):
    """
    涨跌幅榜单（读最新快照）
    type: gainers(涨幅榜) | losers(跌幅榜) | active(活跃榜/按成交量)
    """
    rank_type = request.query_params.get('type', 'gainers')
    limit = min(int(request.query_params.get('limit', 10)), 50)
    market = request.query_params.get('market')  # 可选市场过滤
    cache_ttl = int(getattr(settings, 'MARKET_RANKINGS_CACHE_TTL', 20))
    cache_key = f'rankings:v2:{rank_type}:{market or "ALL"}:{limit}'
    cached_payload = cache.get(cache_key)
    if cached_payload is not None:
        return Response({'code': 0, 'data': cached_payload})

    # 获取每个资产的最新快照（使用子查询取最新）
    from django.db.models import OuterRef, Subquery

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
        return Response({'code': 4001, 'message': '不支持的 type'})

    items = []
    for i, snap in enumerate(snapshots, 1):
        items.append({
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
        })

    payload = {
        'type': rank_type,
        'market': market,
        'items': items,
    }
    cache.set(cache_key, payload, cache_ttl)
    return Response({'code': 0, 'data': payload})


# ─────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────

def _parse_date_param(param: str) -> datetime:
    """解析日期或时间参数，返回 UTC datetime"""
    # 尝试 ISO datetime
    formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']
    for fmt in formats:
        try:
            dt = datetime.strptime(param, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=py_tz.utc)
            return dt
        except ValueError:
            continue
    raise ValueError(f"无法解析日期参数: {param}")
