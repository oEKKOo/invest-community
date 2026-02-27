from decimal import Decimal, ROUND_HALF_UP

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Portfolio, PortfolioAsset, UserHolding, HoldingDailySnapshot
from .serializers import (
    PortfolioListSerializer,
    PortfolioCreateSerializer,
    PortfolioDetailSerializer,
    UserHoldingSerializer,
    UserHoldingCreateSerializer,
)


# ===========================================================================
# 投资组合
# ===========================================================================

class PortfolioListView(APIView):
    """组合列表（GET）和创建（POST）"""
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Portfolio.objects.select_related('owner').prefetch_related(
            'assets', 'assets__asset'
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

        serializer = PortfolioListSerializer(portfolios, many=True, context={'request': request})
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
            ).get(pk=portfolio.pk)
            response_data = PortfolioDetailSerializer(portfolio, context={'request': request}).data
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
    ).order_by('-returns_ytd')[:limit]

    serializer = PortfolioListSerializer(portfolios, many=True, context={'request': request})

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
        Portfolio.objects.select_related('owner').prefetch_related('assets', 'assets__asset'),
        pk=pk
    )

    if request.method == 'GET':
        if not portfolio.is_public:
            if not request.user.is_authenticated or portfolio.owner != request.user:
                return Response({
                    'code': 4030,
                    'message': '无权访问此组合'
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = PortfolioDetailSerializer(portfolio, context={'request': request})
        return Response({'code': 0, 'data': serializer.data})

    elif request.method == 'PATCH':
        if not request.user.is_authenticated:
            return Response({'code': 4010, 'message': '需要登录'}, status=status.HTTP_401_UNAUTHORIZED)

        if portfolio.owner != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({'code': 4030, 'message': '无权修改此组合'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PortfolioCreateSerializer(portfolio, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # 重新查询以获取最新关联数据
            portfolio = Portfolio.objects.select_related('owner').prefetch_related(
                'assets', 'assets__asset'
            ).get(pk=portfolio.pk)
            response_data = PortfolioDetailSerializer(portfolio, context={'request': request}).data
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