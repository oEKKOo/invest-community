from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Portfolio, PortfolioAsset
from .serializers import (
    PortfolioListSerializer,
    PortfolioCreateSerializer,
    PortfolioDetailSerializer
)


class PortfolioListView(APIView):
    """组合列表（GET）和创建（POST）"""
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Portfolio.objects.select_related('owner').prefetch_related('assets')

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
    """获取Top组合"""
    limit = int(request.query_params.get('limit', 5))

    portfolios = Portfolio.objects.filter(is_public=True).select_related('owner').prefetch_related('assets').order_by('-returns_ytd')[:limit]

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
    portfolio = get_object_or_404(Portfolio, pk=pk)

    if request.method == 'GET':
        # 权限检查：只有公开组合或者自己的组合才能查看
        if not portfolio.is_public:
            if not request.user.is_authenticated or portfolio.owner != request.user:
                return Response({
                    'code': 4030,
                    'message': '无权访问此组合'
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = PortfolioDetailSerializer(portfolio, context={'request': request})
        return Response({'code': 0, 'data': serializer.data})

    elif request.method == 'PATCH':
        # 权限检查：只有组合所有者或管理员才能更新
        if not request.user.is_authenticated:
            return Response({
                'code': 4010,
                'message': '需要登录'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if portfolio.owner != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({
                'code': 4030,
                'message': '无权修改此组合'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = PortfolioCreateSerializer(portfolio, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            response_data = PortfolioDetailSerializer(portfolio, context={'request': request}).data
            return Response({'code': 0, 'data': response_data})

        return Response({
            'code': 4001,
            'message': '更新失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # 权限检查：只有组合所有者或管理员才能删除
        if not request.user.is_authenticated:
            return Response({
                'code': 4010,
                'message': '需要登录'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if portfolio.owner != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({
                'code': 4030,
                'message': '无权删除此组合'
            }, status=status.HTTP_403_FORBIDDEN)

        portfolio.delete()
        return Response({'code': 0, 'message': '删除成功'})
