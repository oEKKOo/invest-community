from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    Portfolio,
    PortfolioAsset,
    UserHolding,
    HoldingDailySnapshot,
    PortfolioComment,
    PortfolioFavorite,
    PortfolioSubscription,
    PortfolioUpdateLog,
)
from .serializers import (
    PortfolioListSerializer,
    PortfolioCreateSerializer,
    PortfolioDetailSerializer,
    UserHoldingSerializer,
    UserHoldingCreateSerializer,
    PortfolioCommentSerializer,
    PortfolioCommentCreateSerializer,
    PortfolioUpdateLogSerializer,
)
from accounts.feed_service import write_follow_feed_for_actor
from market_data.models import AssetKline


# ===========================================================================
# 投资组合
# ===========================================================================

def _to_decimal(val, default='0'):
    if val is None:
        return Decimal(default)
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal(default)


def _build_asset_latest_prices(asset_ids):
    """获取资产最近两日收盘价，用于计算日收益"""
    if not asset_ids:
        return {}
    now = timezone.now()
    cutoff = now - timedelta(days=14)
    klines = (
        AssetKline.objects
        .filter(asset_id__in=asset_ids, resolution='D', k_time__gte=cutoff)
        .values('asset_id', 'k_time', 'close')
        .order_by('asset_id', '-k_time')
    )
    result = {}
    for row in klines:
        aid = row['asset_id']
        if aid not in result:
            result[aid] = {'latest': row['close'], 'previous': None}
        elif result[aid]['previous'] is None:
            result[aid]['previous'] = row['close']
    return result


def _pick_close_before_or_equal(date_price_list, target_date):
    picked = None
    for d, p in date_price_list:
        if d <= target_date:
            picked = p
        else:
            break
    return picked


def _build_portfolio_metrics(portfolios):
    """按组合资产权重聚合 total/daily/7d 收益率"""
    if not portfolios:
        return {}
    asset_ids = set()
    portfolio_assets = {}
    for p in portfolios:
        items = []
        for a in p.assets.all():
            if not a.asset_id:
                continue
            weight = _to_decimal(a.allocation) / Decimal('100')
            if weight <= 0:
                continue
            items.append((a.asset_id, weight))
            asset_ids.add(a.asset_id)
        portfolio_assets[p.id] = items

    if not asset_ids:
        return {p.id: {'totalReturn': float(p.returns_ytd), 'dailyReturn': None, 'sevenDayReturn': None} for p in portfolios}

    # 需要足够长的日 K 才能计算「年初至今」加权收益（与 daily/7d 同源，避免 total 恒为库内 returns_ytd=0）
    cutoff = timezone.now() - timedelta(days=400)
    rows = (
        AssetKline.objects
        .filter(asset_id__in=list(asset_ids), resolution='D', k_time__gte=cutoff)
        .values('asset_id', 'k_time', 'close')
        .order_by('asset_id', 'k_time')
    )
    per_asset_series = defaultdict(list)
    for row in rows:
        per_asset_series[row['asset_id']].append((row['k_time'].date(), _to_decimal(row['close'])))

    today = timezone.now().date()
    target_7d = today - timedelta(days=7)
    target_ytd = date(today.year, 1, 1)

    metrics = {}
    for p in portfolios:
        weighted_daily = Decimal('0')
        weighted_7d = Decimal('0')
        weighted_ytd = Decimal('0')
        has_daily = False
        has_7d = False
        has_ytd = False
        for asset_id, weight in portfolio_assets.get(p.id, []):
            series = per_asset_series.get(asset_id, [])
            if len(series) < 1:
                continue
            latest = series[-1][1]
            prev = series[-2][1] if len(series) > 1 else None
            base_7d = _pick_close_before_or_equal(series, target_7d)
            base_ytd = _pick_close_before_or_equal(series, target_ytd)
            if prev and prev > 0:
                weighted_daily += weight * ((latest - prev) / prev)
                has_daily = True
            if base_7d and base_7d > 0:
                weighted_7d += weight * ((latest - base_7d) / base_7d)
                has_7d = True
            if base_ytd and base_ytd > 0:
                weighted_ytd += weight * ((latest - base_ytd) / base_ytd)
                has_ytd = True

        metrics[p.id] = {
            'totalReturn': float(weighted_ytd) if has_ytd else float(p.returns_ytd),
            'dailyReturn': float(weighted_daily) if has_daily else None,
            'sevenDayReturn': float(weighted_7d) if has_7d else None,
        }
    return metrics


def _build_portfolio_holding_details(portfolio):
    """组合持仓明细：weight + latest price + market value + return rate（可降级）"""
    assets = list(portfolio.assets.select_related('asset'))
    if not assets:
        return []
    asset_ids = [a.asset_id for a in assets if a.asset_id]
    latest_map = _build_asset_latest_prices(asset_ids)
    user_holdings = {
        h.asset_id: h for h in UserHolding.objects.filter(
            user=portfolio.owner, asset_id__in=asset_ids
        ).only('asset_id', 'quantity', 'cost_price')
    }
    details = []
    for a in assets:
        if not a.asset_id:
            details.append({
                'assetId': None,
                'code': a.symbol,
                'name': a.name,
                'market': '',
                'weight': float(_to_decimal(a.allocation)),
                'price': None,
                'marketValue': None,
                'returnRate': None,
            })
            continue
        pinfo = latest_map.get(a.asset_id, {})
        latest = _to_decimal(pinfo.get('latest')) if pinfo.get('latest') is not None else None
        prev = _to_decimal(pinfo.get('previous')) if pinfo.get('previous') is not None else None
        holding = user_holdings.get(a.asset_id)
        market_value = None
        return_rate = None
        if latest is not None and holding is not None:
            qty = _to_decimal(holding.quantity)
            cost = _to_decimal(holding.cost_price)
            market_value = qty * latest
            if cost > 0:
                return_rate = (latest - cost) / cost
        elif latest is not None and prev is not None and prev > 0:
            return_rate = (latest - prev) / prev

        details.append({
            'assetId': a.asset_id,
            'code': a.asset.code if a.asset else a.symbol,
            'name': a.asset.name if a.asset else a.name,
            'market': (a.asset.display_market if a.asset else '') if a.asset_id else '',
            'weight': float(_to_decimal(a.allocation)),
            'price': float(latest) if latest is not None else None,
            'marketValue': float(market_value) if market_value is not None else None,
            'returnRate': float(return_rate) if return_rate is not None else None,
        })
    return details

class PortfolioListView(APIView):
    """组合列表（GET）和创建（POST）"""
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Portfolio.objects.select_related('owner').prefetch_related(
            'assets', 'assets__asset'
        ).annotate(
            favorites_count=Count('favorites', distinct=True),
            asset_count=Count('assets', distinct=True),
        )

        # 筛选参数
        user_id = request.query_params.get('userId')
        if user_id:
            queryset = queryset.filter(owner_id=user_id)

        is_public = request.query_params.get('isPublic')
        if is_public is not None:
            is_public_bool = is_public.lower() == 'true'
            queryset = queryset.filter(is_public=is_public_bool)
        else:
            # 默认权限过滤
            if not request.user.is_authenticated:
                queryset = queryset.filter(is_public=True)
            else:
                queryset = queryset.filter(
                    Q(is_public=True) | Q(owner=request.user)
                )

        # 排序
        sort_by = request.query_params.get('sortBy', 'new')
        if sort_by == 'returnsYTD':
            queryset = queryset.order_by('-returns_ytd', '-created_at')
        elif sort_by == 'likes':
            queryset = queryset.order_by('-like_count', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')

        # 手动分页
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('pageSize', 20))
        except (ValueError, TypeError):
            page, page_size = 1, 20

        total = queryset.count()
        offset = (page - 1) * page_size
        portfolios = queryset[offset:offset + page_size]

        metrics = _build_portfolio_metrics(portfolios)
        serializer = PortfolioListSerializer(
            portfolios,
            many=True,
            context={'request': request, 'portfolio_metrics': metrics}
        )
        return Response({
            'code': 0,
            'data': {
                'items': serializer.data,
                'page': page,
                'pageSize': page_size,
                'total': total,
            }
        })

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'code': 4010, 'message': '需要登录'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = PortfolioCreateSerializer(data=request.data)
        if serializer.is_valid():
            portfolio = serializer.save(owner=request.user)
            # 刷新关联数据再序列化
            portfolio.refresh_from_db()
            portfolio = Portfolio.objects.select_related('owner').prefetch_related(
                'assets', 'assets__asset'
            ).annotate(
                favorites_count=Count('favorites', distinct=True),
                asset_count=Count('assets', distinct=True),
            ).get(pk=portfolio.pk)
            response_data = PortfolioDetailSerializer(
                portfolio,
                context={
                    'request': request,
                    'portfolio_metrics': _build_portfolio_metrics([portfolio]),
                    'portfolio_holding_details': {portfolio.id: _build_portfolio_holding_details(portfolio)},
                }
            ).data
            if portfolio.is_public:
                write_follow_feed_for_actor(
                    actor_user=request.user,
                    action_type='PORTFOLIO_PUBLISHED',
                    object_type='PORTFOLIO',
                    object_id=portfolio.id,
                )
            return Response({'code': 0, 'data': response_data}, status=status.HTTP_201_CREATED)

        return Response({
            'code': 4001,
            'message': '创建失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def portfolio_top(request):
    """获取 Top 组合"""
    limit = int(request.query_params.get('limit', 5))

    portfolios = Portfolio.objects.filter(is_public=True).select_related('owner').prefetch_related(
        'assets', 'assets__asset'
    ).annotate(
        favorites_count=Count('favorites', distinct=True),
        asset_count=Count('assets', distinct=True),
    ).order_by('-returns_ytd')[:limit]

    metrics = _build_portfolio_metrics(portfolios)
    serializer = PortfolioListSerializer(
        portfolios,
        many=True,
        context={'request': request, 'portfolio_metrics': metrics}
    )

    return Response({
        'code': 0,
        'data': {
            'items': serializer.data
        }
    })


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def portfolio_detail(request, pk):
    """组合详情、更新、删除"""
    portfolio = get_object_or_404(
        Portfolio.objects.select_related('owner').prefetch_related('assets', 'assets__asset').annotate(
            favorites_count=Count('favorites', distinct=True),
            asset_count=Count('assets', distinct=True),
        ),
        pk=pk
    )

    if request.method == 'GET':
        if not portfolio.is_public:
            if not request.user.is_authenticated or portfolio.owner != request.user:
                return Response({
                    'code': 4030,
                    'message': '无权访问此组合'
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = PortfolioDetailSerializer(
            portfolio,
            context={
                'request': request,
                'portfolio_metrics': _build_portfolio_metrics([portfolio]),
                'portfolio_holding_details': {portfolio.id: _build_portfolio_holding_details(portfolio)},
            }
        )
        return Response({'code': 0, 'data': serializer.data})

    elif request.method == 'PATCH':
        if not request.user.is_authenticated:
            return Response({'code': 4010, 'message': '需要登录'}, status=status.HTTP_401_UNAUTHORIZED)

        if portfolio.owner != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({'code': 4030, 'message': '无权修改此组合'}, status=status.HTTP_403_FORBIDDEN)

        old_is_public = portfolio.is_public
        serializer = PortfolioCreateSerializer(portfolio, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # 重新查询以获取最新关联数据
            portfolio = Portfolio.objects.select_related('owner').prefetch_related(
                'assets', 'assets__asset'
            ).annotate(
                favorites_count=Count('favorites', distinct=True),
                asset_count=Count('assets', distinct=True),
            ).get(pk=portfolio.pk)
            response_data = PortfolioDetailSerializer(
                portfolio,
                context={
                    'request': request,
                    'portfolio_metrics': _build_portfolio_metrics([portfolio]),
                    'portfolio_holding_details': {portfolio.id: _build_portfolio_holding_details(portfolio)},
                }
            ).data
            if portfolio.is_public and (not old_is_public):
                write_follow_feed_for_actor(
                    actor_user=portfolio.owner,
                    action_type='PORTFOLIO_PUBLISHED',
                    object_type='PORTFOLIO',
                    object_id=portfolio.id,
                )
            return Response({'code': 0, 'data': response_data})

        return Response({
            'code': 4001,
            'message': '更新失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not request.user.is_authenticated:
            return Response({'code': 4010, 'message': '需要登录'}, status=status.HTTP_401_UNAUTHORIZED)

        if portfolio.owner != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({'code': 4030, 'message': '无权删除此组合'}, status=status.HTTP_403_FORBIDDEN)

        portfolio.delete()
        return Response({'code': 0, 'message': '删除成功'})


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def portfolio_comments(request, pk):
    """
    GET /api/portfolios/{id}/comments/
    POST /api/portfolios/{id}/comments/
    """
    portfolio = get_object_or_404(Portfolio, pk=pk)

    if request.method == 'GET':
        # 仅返回未删除的顶级评论，子回复在序列化器中带出
        comments = (
            PortfolioComment.objects.filter(portfolio=portfolio, is_deleted=False, parent__isnull=True)
            .select_related('author', 'reply_to_user')
            .prefetch_related('replies__author', 'replies__reply_to_user')
            .order_by('created_at')
        )
        serializer = PortfolioCommentSerializer(comments, many=True, context={'request': request})
        return Response({'code': 0, 'data': {'items': serializer.data}})

    # POST 创建评论需要登录
    if not request.user.is_authenticated:
        return Response(
            {'code': 4010, 'message': '需要登录'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    serializer = PortfolioCommentCreateSerializer(
        data=request.data, context={'request': request, 'portfolio': portfolio}
    )
    if serializer.is_valid():
        comment = serializer.save()
        data = PortfolioCommentSerializer(comment, context={'request': request}).data
        return Response({'code': 0, 'data': data}, status=status.HTTP_201_CREATED)

    return Response(
        {'code': 4001, 'message': '发表评论失败', 'errors': serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def portfolio_subscribe(request, pk):
    """
    POST /api/portfolios/{id}/subscribe/
    订阅或取消订阅组合（幂等切换）
    """
    portfolio = get_object_or_404(Portfolio, pk=pk)

    if request.method == 'POST':
        # 简单切换订阅状态
        sub_qs = PortfolioSubscription.objects.filter(portfolio=portfolio, user=request.user)
        if sub_qs.exists():
            sub_qs.delete()
            return Response({'code': 0, 'message': '已取消订阅'})
        PortfolioSubscription.objects.create(portfolio=portfolio, user=request.user)
        return Response({'code': 0, 'message': '订阅成功'})


@api_view(['GET'])
@permission_classes([AllowAny])
def portfolio_updates(request, pk):
    """
    GET /api/portfolios/{id}/updates/
    获取组合更新日志列表
    """
    portfolio = get_object_or_404(Portfolio, pk=pk)
    logs = portfolio.update_logs.all()
    serializer = PortfolioUpdateLogSerializer(logs, many=True)
    return Response({'code': 0, 'data': {'items': serializer.data}})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def portfolio_favorite_toggle(request, pk):
    """
    POST /api/portfolios/{id}/favorite/
    收藏或取消收藏组合（幂等切换）
    """
    portfolio = get_object_or_404(Portfolio, pk=pk)
    qs = PortfolioFavorite.objects.filter(portfolio=portfolio, user=request.user)
    if qs.exists():
        qs.delete()
        return Response({'code': 0, 'message': '已取消收藏'})
    PortfolioFavorite.objects.create(portfolio=portfolio, user=request.user)
    return Response({'code': 0, 'message': '收藏成功'})


@api_view(['GET'])
@permission_classes([AllowAny])
def portfolio_returns_history(request, pk):
    """
    GET /api/portfolios/{id}/returns-history/?range=7d|30d|all
    按组合权重聚合日K close，返回累计收益率曲线
    """
    portfolio = get_object_or_404(
        Portfolio.objects.prefetch_related('assets'),
        pk=pk
    )
    if not portfolio.is_public:
        if not request.user.is_authenticated or request.user != portfolio.owner:
            return Response({'code': 4030, 'message': '无权访问此组合'}, status=status.HTTP_403_FORBIDDEN)

    range_key = request.query_params.get('range', '30d')
    if range_key == '7d':
        days = 7
    elif range_key == '30d':
        days = 30
    else:
        days = 365

    weighted_assets = []
    asset_ids = []
    for asset in portfolio.assets.all():
        if not asset.asset_id:
            continue
        w = _to_decimal(asset.allocation) / Decimal('100')
        if w <= 0:
            continue
        weighted_assets.append((asset.asset_id, w))
        asset_ids.append(asset.asset_id)
    if not weighted_assets:
        return Response({'code': 0, 'data': {'range': range_key, 'items': []}})

    cutoff = timezone.now() - timedelta(days=max(days + 5, 14))
    rows = (
        AssetKline.objects
        .filter(asset_id__in=asset_ids, resolution='D', k_time__gte=cutoff)
        .values('asset_id', 'k_time', 'close')
        .order_by('k_time', 'asset_id')
    )

    by_date = defaultdict(dict)
    for row in rows:
        d = row['k_time'].date()
        by_date[d][row['asset_id']] = _to_decimal(row['close'])
    if not by_date:
        return Response({'code': 0, 'data': {'range': range_key, 'items': []}})

    all_dates = sorted(by_date.keys())
    if range_key in ('7d', '30d'):
        min_date = timezone.now().date() - timedelta(days=days)
        all_dates = [d for d in all_dates if d >= min_date]
        if not all_dates:
            return Response({'code': 0, 'data': {'range': range_key, 'items': []}})

    # 缺失日期采用“前值延续”进行组合净值聚合
    last_price = {}
    points = []
    base_value = None
    for d in all_dates:
        day_map = by_date[d]
        for aid, close in day_map.items():
            last_price[aid] = close
        value = Decimal('0')
        coverage = 0
        for aid, weight in weighted_assets:
            px = last_price.get(aid)
            if px is None:
                continue
            coverage += 1
            value += weight * px
        if coverage == 0:
            continue
        if base_value is None:
            base_value = value
        ret = Decimal('0') if (base_value is None or base_value == 0) else (value - base_value) / base_value
        points.append({
            'date': str(d),
            'totalValue': _fmt(value),
            'returnRate': _fmt4(ret),
            'coverage': coverage,
        })

    return Response({
        'code': 0,
        'data': {
            'range': range_key,
            'portfolioId': portfolio.id,
            'items': points,
        }
    })


# ===========================================================================
# 个人持仓
# ===========================================================================

class UserHoldingListView(APIView):
    """个人持仓列表（GET）和新增/更新（POST）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        holdings = UserHolding.objects.filter(user=request.user).select_related('asset').order_by('-updated_at')

        serializer = UserHoldingSerializer(holdings, many=True)
        return Response({
            'code': 0,
            'data': {
                'items': serializer.data,
                'total': holdings.count(),
            }
        })

    def post(self, request):
        """新增或更新某资产持仓（按 assetId 做 upsert）"""
        serializer = UserHoldingCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            holding = serializer.save()
            return Response({
                'code': 0,
                'data': UserHoldingSerializer(holding).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'code': 4001,
            'message': '操作失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserHoldingDetailView(APIView):
    """单条持仓操作（PATCH 更新 / DELETE 删除）"""
    permission_classes = [IsAuthenticated]

    def _get_holding(self, request, pk):
        return get_object_or_404(UserHolding, pk=pk, user=request.user)

    def get(self, request, pk):
        holding = self._get_holding(request, pk)
        return Response({'code': 0, 'data': UserHoldingSerializer(holding).data})

    def patch(self, request, pk):
        holding = self._get_holding(request, pk)
        serializer = UserHoldingCreateSerializer(
            holding, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            holding = serializer.save()
            return Response({'code': 0, 'data': UserHoldingSerializer(holding).data})

        return Response({
            'code': 4001,
            'message': '更新失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        holding = self._get_holding(request, pk)
        holding.delete()
        return Response({'code': 0, 'message': '持仓已删除'})


# ===========================================================================
# 持仓收益计算
# ===========================================================================

class HoldingPerformanceView(APIView):
    """
    GET /api/holdings/performance/
    基于每日快照计算持仓收益，返回三类口径：
      1) 当日收益（Daily PnL）：昨日估值价 → 今日估值价
      2) 持有收益（Unrealized PnL）：成本价 → 今日估值价
      3) 累计收益（Total PnL）：MVP 阶段等同于持有收益（无交易流水）

    数据前提：需先执行 `python manage.py fill_holding_snapshots` 生成快照。
    若无快照，对应字段返回 null，前端展示"暂无估值数据"。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        holdings = UserHolding.objects.filter(
            user=request.user
        ).select_related('asset').order_by('-updated_at')

        if not holdings.exists():
            return Response({'code': 0, 'data': _empty_performance()})

        items = []
        total_market_value = Decimal('0')
        total_cost_value = Decimal('0')
        total_daily_pnl = Decimal('0')
        total_yesterday_value = Decimal('0')
        as_of_date = None

        for holding in holdings:
            quantity = Decimal(str(holding.quantity))
            cost_price = Decimal(str(holding.cost_price))
            cost_value = quantity * cost_price

            # 取最近 2 条快照（今天 + 昨天）
            snapshots = list(
                HoldingDailySnapshot.objects.filter(holding=holding)
                .order_by('-date')[:2]
            )

            if not snapshots:
                # 无快照 → 所有价格字段返回 null
                items.append({
                    'holdingId': holding.id,
                    'assetId': holding.asset_id,
                    'code': holding.asset.code,
                    'name': holding.asset.name,
                    'market': holding.asset.market,
                    'displayMarket': holding.asset.display_market,
                    'assetType': holding.asset.asset_type,
                    'quantity': str(quantity),
                    'costPrice': str(cost_price),
                    'todayPrice': None,
                    'yesterdayPrice': None,
                    'marketValue': None,
                    'costValue': _fmt(cost_value),
                    'unrealizedPnl': None,
                    'unrealizedReturn': None,
                    'dailyPnl': None,
                    'dailyReturn': None,
                    'snapshotDate': None,
                    'hasData': False,
                })
                total_cost_value += cost_value
                continue

            today_snap = snapshots[0]
            yesterday_snap = snapshots[1] if len(snapshots) > 1 else None

            today_price = today_snap.close_price
            market_value = quantity * today_price
            unrealized_pnl = market_value - cost_value
            unrealized_return = (
                unrealized_pnl / cost_value if cost_value else Decimal('0')
            )

            if yesterday_snap:
                yesterday_price = yesterday_snap.close_price
                daily_pnl = quantity * (today_price - yesterday_price)
                yesterday_value = quantity * yesterday_price
                daily_return = (
                    daily_pnl / yesterday_value if yesterday_value else Decimal('0')
                )
            else:
                yesterday_price = None
                daily_pnl = None
                daily_return = None
                yesterday_value = Decimal('0')

            # 累计汇总
            total_market_value += market_value
            total_cost_value += cost_value
            if daily_pnl is not None:
                total_daily_pnl += daily_pnl
                total_yesterday_value += yesterday_value

            if as_of_date is None or today_snap.date > as_of_date:
                as_of_date = today_snap.date

            items.append({
                'holdingId': holding.id,
                'assetId': holding.asset_id,
                'code': holding.asset.code,
                'name': holding.asset.name,
                'market': holding.asset.market,
                'displayMarket': holding.asset.display_market,
                'assetType': holding.asset.asset_type,
                'quantity': str(quantity),
                'costPrice': _fmt(cost_price),
                'todayPrice': _fmt(today_price),
                'yesterdayPrice': _fmt(yesterday_price) if yesterday_price is not None else None,
                'marketValue': _fmt(market_value),
                'costValue': _fmt(cost_value),
                'unrealizedPnl': _fmt(unrealized_pnl),
                'unrealizedReturn': _fmt4(unrealized_return),
                'dailyPnl': _fmt(daily_pnl) if daily_pnl is not None else None,
                'dailyReturn': _fmt4(daily_return) if daily_return is not None else None,
                'snapshotDate': str(today_snap.date),
                'hasData': True,
            })

        # 全局汇总
        total_unrealized_pnl = total_market_value - total_cost_value
        total_unrealized_return = (
            total_unrealized_pnl / total_cost_value
            if total_cost_value else Decimal('0')
        )
        total_daily_return = (
            total_daily_pnl / total_yesterday_value
            if total_yesterday_value else Decimal('0')
        )

        return Response({
            'code': 0,
            'data': {
                'asOf': str(as_of_date) if as_of_date else None,
                'totalMarketValue': _fmt(total_market_value),
                'totalCostValue': _fmt(total_cost_value),
                'totalUnrealizedPnl': _fmt(total_unrealized_pnl),
                'totalUnrealizedReturn': _fmt4(total_unrealized_return),
                'totalDailyPnl': _fmt(total_daily_pnl),
                'totalDailyReturn': _fmt4(total_daily_return),
                'hasAnyData': any(item['hasData'] for item in items),
                'items': items,
            }
        })


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _fmt(val):
    """保留 2 位小数"""
    if val is None:
        return None
    return str(Decimal(str(val)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def _fmt4(val):
    """保留 4 位小数（收益率）"""
    if val is None:
        return None
    return str(Decimal(str(val)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))


def _empty_performance():
    return {
        'asOf': None,
        'totalMarketValue': '0.00',
        'totalCostValue': '0.00',
        'totalUnrealizedPnl': '0.00',
        'totalUnrealizedReturn': '0.0000',
        'totalDailyPnl': '0.00',
        'totalDailyReturn': '0.0000',
        'hasAnyData': False,
        'items': [],
    }


# ===========================================================================
# 持仓累计收益历史（每日净值曲线）
# ===========================================================================

class HoldingReturnsHistoryView(APIView):
    """
    GET /api/holdings/returns-history/
    返回用户持仓的每日累计收益时间序列，用于前端绘制净值曲线。

    逻辑：
      对每一个有快照数据的日期，汇总所有持仓的市值 = Σ(quantity × close_price)
      累计收益率 = (当日总市值 - 总成本) / 总成本
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from collections import defaultdict

        holdings = UserHolding.objects.filter(
            user=request.user
        ).select_related('asset')

        if not holdings.exists():
            return Response({'code': 0, 'data': {'totalCostValue': '0.00', 'items': []}})

        # 总持仓成本（固定值：不考虑增减仓历史）
        total_cost = sum(
            Decimal(str(h.quantity)) * Decimal(str(h.cost_price))
            for h in holdings
        )

        # 建立 holding_id → UserHolding 的映射
        holding_map = {h.id: h for h in holdings}
        holding_ids = list(holding_map.keys())

        # 拉取所有快照，按日期聚合
        snapshots = (
            HoldingDailySnapshot.objects
            .filter(holding_id__in=holding_ids)
            .values('date', 'holding_id', 'close_price')
            .order_by('date')
        )

        # {date: {holding_id: close_price}}
        date_snap_map = defaultdict(dict)
        for snap in snapshots:
            date_snap_map[snap['date']][snap['holding_id']] = Decimal(str(snap['close_price']))

        items = []
        for date in sorted(date_snap_map.keys()):
            snap = date_snap_map[date]
            day_market_value = Decimal('0')
            for h_id, close_price in snap.items():
                holding = holding_map.get(h_id)
                if holding:
                    day_market_value += Decimal(str(holding.quantity)) * close_price

            unrealized_pnl = day_market_value - total_cost
            unrealized_return = (
                unrealized_pnl / total_cost if total_cost else Decimal('0')
            )

            items.append({
                'date': str(date),
                'totalMarketValue': _fmt(day_market_value),
                'unrealizedPnl': _fmt(unrealized_pnl),
                'unrealizedReturn': _fmt4(unrealized_return),
                'coverage': len(snap),      # 当日有数据的持仓数
            })

        return Response({
            'code': 0,
            'data': {
                'totalCostValue': _fmt(total_cost),
                'holdingsCount': len(holdings),
                'items': items,
            }
        })