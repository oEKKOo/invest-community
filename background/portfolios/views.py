from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Portfolio, PortfolioAsset
from .serializers import (
    PortfolioListSerializer, 
    PortfolioCreateSerializer, 
    PortfolioDetailSerializer
)


class PortfolioListView(generics.ListCreateAPIView):
    """组合列表和创建"""
    serializer_class = PortfolioListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Portfolio.objects.select_related('owner').prefetch_related('assets')
        
        # 筛选参数
        user_id = self.request.query_params.get('userId')
        if user_id:
            queryset = queryset.filter(owner_id=user_id)
        
        is_public = self.request.query_params.get('isPublic')
        if is_public is not None:
            is_public_bool = is_public.lower() == 'true'
            queryset = queryset.filter(is_public=is_public_bool)
        else:
            # 默认只显示公开的组合
            if not self.request.user.is_authenticated:
                queryset = queryset.filter(is_public=True)
            else:
                # 登录用户可以看到公开组合和自己的私有组合
                queryset = queryset.filter(
                    Q(is_public=True) | Q(owner=self.request.user)
                )
        
        # 排序
        sort_by = self.request.query_params.get('sortBy', 'new')
        if sort_by == 'returnsYTD':
            queryset = queryset.order_by('-returns_ytd', '-created_at')
        else:  # new
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PortfolioCreateSerializer
        return PortfolioListSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]


@api_view(['GET'])
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