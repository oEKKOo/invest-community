from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Content, Comment, Asset, Like, Favorite, ContentAsset
from .serializers import (
    ContentListSerializer, ContentDetailSerializer, ContentCreateSerializer,
    CommentSerializer, CommentCreateSerializer, AssetSerializer, LikeSerializer
)

User = get_user_model()


class ContentListView(generics.ListCreateAPIView):
    """内容列表和创建"""
    serializer_class = ContentListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Content.objects.select_related('author').prefetch_related('assets')
        
        # 权限过滤
        user = self.request.user
        if user.is_authenticated:
            if user.role in ['MODERATOR', 'ADMIN']:
                # 管理员可以看到所有状态
                pass
            else:
                # 普通用户只能看到已发布的内容和自己的内容
                queryset = queryset.filter(
                    Q(status='PUBLISHED') | Q(author=user)
                )
        else:
            # 未登录用户只能看到已发布的内容
            queryset = queryset.filter(status='PUBLISHED')
        
        # 筛选参数
        status_param = self.request.query_params.getlist('status')
        if status_param:
            queryset = queryset.filter(status__in=status_param)
        
        author_id = self.request.query_params.get('authorId')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags_json__contains=[tag])
        
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(body__icontains=q)
            )
        
        # 排序
        sort_param = self.request.query_params.get('sort', 'new')
        if sort_param == 'hot':
            queryset = queryset.order_by('-like_count', '-comment_count', '-created_at')
        else:  # new
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def list(self, request, *args, **kwargs):
        """重写list方法以返回自定义响应格式"""
        # 🔍 调试输出
        print("🔍 开始调试帖子列表查询...")
        
        # 原始查询集（无任何过滤）
        raw_queryset = Content.objects.all()
        print(f"📊 数据库中总帖子数: {raw_queryset.count()}")
        
        if raw_queryset.exists():
            print("📝 前5个帖子:")
            for content in raw_queryset[:5]:
                print(f"  ID:{content.id} | {content.title} | 状态:{content.status} | 作者:{content.author.username}")
        
        # 检查用户状态
        user = request.user
        print(f"👤 当前用户: {user} (认证状态: {user.is_authenticated})")
        if user.is_authenticated:
            print(f"   用户角色: {getattr(user, 'role', 'USER')}")
        
        # 应用权限过滤后
        queryset = self.get_queryset()
        print(f"🔐 权限过滤后帖子数: {queryset.count()}")
        
        # 分页处理
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))
        
        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_queryset = queryset[start:end]
        print(f"📄 分页结果: 第{page}页, 每页{page_size}条, 总共{total}条, 当前页{paginated_queryset.count()}条")
        
        serializer = self.get_serializer(paginated_queryset, many=True)
        
        print("✅ 调试完成，返回响应")
        return Response({
            'code': 0,
            'data': {
                'items': serializer.data,
                'page': page,
                'pageSize': page_size,
                'total': total
            }
        })

    def create(self, request, *args, **kwargs):
        """重写create方法以返回自定义响应格式"""
        serializer = ContentCreateSerializer(data=request.data)
        if serializer.is_valid():
            content = serializer.save(author=request.user)
            
            # 处理资产关联
            asset_ids = request.data.get('assetIds', [])
            if asset_ids:
                assets = Asset.objects.filter(id__in=asset_ids)
                for asset in assets:
                    ContentAsset.objects.create(content=content, asset=asset)
            
            # 返回详细信息
            response_serializer = ContentDetailSerializer(content, context={'request': request})
            return Response({
                'code': 0, 
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'code': 4001, 
            'message': '创建失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ContentCreateSerializer
        return ContentListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]


@api_view(['GET', 'PATCH', 'DELETE'])
def content_detail(request, pk):
    """内容详情、更新、删除"""
    content = get_object_or_404(Content, pk=pk)
    
    # 权限检查
    if request.method == 'GET':
        # 查看权限
        if content.status != 'PUBLISHED':
            if not request.user.is_authenticated:
                return Response({'code': 4010, 'message': '需要登录'}, 
                               status=status.HTTP_401_UNAUTHORIZED)
            
            if content.author != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
                return Response({'code': 4030, 'message': '无权访问'}, 
                               status=status.HTTP_403_FORBIDDEN)
        
        # 增加浏览量
        Content.objects.filter(pk=pk).update(view_count=F('view_count') + 1)
        
        serializer = ContentDetailSerializer(content, context={'request': request})
        return Response({'code': 0, 'data': serializer.data})
    
    elif request.method == 'PATCH':
        # 更新权限
        if not request.user.is_authenticated:
            return Response({'code': 4010, 'message': '需要登录'}, 
                           status=status.HTTP_401_UNAUTHORIZED)
        
        if content.author != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({'code': 4030, 'message': '无权修改'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        serializer = ContentCreateSerializer(content, data=request.data, partial=True)
        if serializer.is_valid():
            # 处理状态变更
            new_status = serializer.validated_data.get('status', content.status)
            if new_status == 'PUBLISHED' and content.published_at is None:
                serializer.validated_data['published_at'] = timezone.now()
            
            serializer.save()
            
            # 处理资产关联
            asset_ids = request.data.get('asset_ids')
            if asset_ids is not None:
                ContentAsset.objects.filter(content=content).delete()
                if asset_ids:
                    assets = Asset.objects.filter(id__in=asset_ids)
                    for asset in assets:
                        ContentAsset.objects.create(content=content, asset=asset)
            
            return Response({'code': 0, 'data': ContentDetailSerializer(content, context={'request': request}).data})
        
        return Response({'code': 4001, 'errors': serializer.errors}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # 删除权限
        if not request.user.is_authenticated:
            return Response({'code': 4010, 'message': '需要登录'}, 
                           status=status.HTTP_401_UNAUTHORIZED)
        
        if content.author != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({'code': 4030, 'message': '无权删除'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        content.status = 'TAKEN_DOWN'
        content.save()
        return Response({'code': 0, 'message': '删除成功'})


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, pk):
    """收藏/取消收藏帖子"""
    content = get_object_or_404(Content, pk=pk)
    
    if request.method == 'POST':
        favorite, created = Favorite.objects.get_or_create(user=request.user, content=content)
        if created:
            return Response({'code': 0, 'message': '收藏成功'})
        else:
            return Response({'code': 4090, 'message': '已收藏过'}, 
                           status=status.HTTP_409_CONFLICT)
    
    elif request.method == 'DELETE':
        try:
            favorite = Favorite.objects.get(user=request.user, content=content)
            favorite.delete()
            return Response({'code': 0, 'message': '取消收藏成功'})
        except Favorite.DoesNotExist:
            return Response({'code': 4040, 'message': '未收藏过'}, 
                           status=status.HTTP_404_NOT_FOUND)


class UserFavoritesView(generics.ListAPIView):
    """用户收藏列表"""
    serializer_class = ContentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        favorites = Favorite.objects.filter(user=self.request.user).select_related('content')
        return [fav.content for fav in favorites]


@api_view(['GET'])
def content_comments(request, pk):
    """获取内容的评论列表"""
    content = get_object_or_404(Content, pk=pk)
    
    # 只返回顶级评论
    comments = Comment.objects.filter(
        content=content, 
        parent__isnull=True, 
        status='NORMAL'
    ).select_related('author', 'reply_to_user').order_by('created_at')
    
    serializer = CommentSerializer(comments, many=True, context={'request': request})
    return Response({'code': 0, 'data': serializer.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request, pk):
    """创建评论"""
    content = get_object_or_404(Content, pk=pk)
    
    serializer = CommentCreateSerializer(
        data=request.data, 
        context={'request': request, 'content_id': content.id}
    )
    
    if serializer.is_valid():
        comment = serializer.save()
        
        # 更新内容的评论数
        Content.objects.filter(pk=pk).update(comment_count=F('comment_count') + 1)
        
        response_data = CommentSerializer(comment, context={'request': request}).data
        return Response({'code': 0, 'data': response_data}, status=status.HTTP_201_CREATED)
    
    return Response({'code': 4001, 'errors': serializer.errors}, 
                   status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    """删除评论"""
    comment = get_object_or_404(Comment, pk=comment_id)
    
    # 权限检查
    if comment.author != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({'code': 4030, 'message': '无权删除'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    with transaction.atomic():
        comment.status = 'DELETED'
        comment.save()
        
        # 更新内容的评论数
        Content.objects.filter(pk=comment.content_id).update(
            comment_count=F('comment_count') - 1
        )
    
    return Response({'code': 0, 'message': '删除成功'})


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def toggle_like(request):
    """点赞/取消点赞"""
    if request.method == 'POST':
        serializer = LikeSerializer(data=request.data)
        if serializer.is_valid():
            target_type = serializer.validated_data['target_type']
            target_id = serializer.validated_data['target_id']
            
            like, created = Like.objects.get_or_create(
                user=request.user,
                target_type=target_type,
                target_id=target_id
            )
            
            if created:
                # 更新点赞计数
                _update_like_count(target_type, target_id, 1)
                return Response({'code': 0, 'message': '点赞成功'})
            else:
                return Response({'code': 4090, 'message': '已点赞过'}, 
                               status=status.HTTP_409_CONFLICT)
        
        return Response({'code': 4001, 'errors': serializer.errors}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        serializer = LikeSerializer(data=request.data)
        if serializer.is_valid():
            target_type = serializer.validated_data['target_type']
            target_id = serializer.validated_data['target_id']
            
            try:
                like = Like.objects.get(
                    user=request.user,
                    target_type=target_type,
                    target_id=target_id
                )
                like.delete()
                
                # 更新点赞计数
                _update_like_count(target_type, target_id, -1)
                return Response({'code': 0, 'message': '取消点赞成功'})
            
            except Like.DoesNotExist:
                return Response({'code': 4040, 'message': '未点赞过'}, 
                               status=status.HTTP_404_NOT_FOUND)
        
        return Response({'code': 4001, 'errors': serializer.errors}, 
                       status=status.HTTP_400_BAD_REQUEST)


def _update_like_count(target_type, target_id, delta):
    """更新点赞计数"""
    if target_type == 'POST':
        Content.objects.filter(id=target_id).update(like_count=F('like_count') + delta)
    elif target_type == 'COMMENT':
        Comment.objects.filter(id=target_id).update(like_count=F('like_count') + delta)
    elif target_type == 'PORTFOLIO':
        from portfolios.models import Portfolio
        Portfolio.objects.filter(id=target_id).update(like_count=F('like_count') + delta)


class AssetListView(generics.ListAPIView):
    """资产列表和搜索"""
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Asset.objects.all()
        
        asset_type = self.request.query_params.get('type')
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)
        
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(code__icontains=q) | Q(name__icontains=q)
            )
        
        return queryset.order_by('code')


@api_view(['GET'])
def asset_detail(request, pk):
    """资产详情"""
    asset = get_object_or_404(Asset, pk=pk)
    serializer = AssetSerializer(asset)
    return Response({'code': 0, 'data': serializer.data})


@api_view(['GET'])
def asset_posts(request, pk):
    """资产相关帖子"""
    asset = get_object_or_404(Asset, pk=pk)
    
    # 获取关联该资产的内容
    queryset = Content.objects.filter(
        assets=asset,
        status='PUBLISHED'
    ).select_related('author').prefetch_related('assets')
    
    sort_param = request.query_params.get('sort', 'new')
    if sort_param == 'hot':
        queryset = queryset.order_by('-like_count', '-comment_count', '-created_at')
    else:
        queryset = queryset.order_by('-created_at')
    
    # 分页处理可以使用DRF的分页器
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('pageSize', 20))
    
    start = (page - 1) * page_size
    end = start + page_size
    
    posts = queryset[start:end]
    total = queryset.count()
    
    serializer = ContentListSerializer(posts, many=True, context={'request': request})
    
    return Response({
        'code': 0,
        'data': {
            'items': serializer.data,
            'page': page,
            'pageSize': page_size,
            'total': total
        }
    })


# Admin 管理接口

class AdminPostsView(generics.ListAPIView):
    """管理员查看帖子列表"""
    serializer_class = ContentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 检查权限
        if self.request.user.role not in ['MODERATOR', 'ADMIN']:
            return Content.objects.none()
        
        queryset = Content.objects.select_related('author').prefetch_related('assets')
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset.order_by('-created_at')


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_post_status(request, pk):
    """管理员修改帖子状态"""
    # 权限检查
    if request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({
            'code': 4030, 
            'message': '无权限'
        }, status=status.HTTP_403_FORBIDDEN)
    
    content = get_object_or_404(Content, pk=pk)
    
    new_status = request.data.get('status')
    reject_reason = request.data.get('rejectReason', '')
    
    if new_status not in ['PUBLISHED', 'REJECTED', 'TAKEN_DOWN']:
        return Response({
            'code': 4001, 
            'message': '无效的状态'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    content.status = new_status
    if reject_reason:
        content.reject_reason = reject_reason
    content.reviewed_by = request.user
    
    if new_status == 'PUBLISHED' and not content.published_at:
        content.published_at = timezone.now()
    
    content.save()
    
    return Response({
        'code': 0, 
        'message': '状态更新成功'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_overview(request):
    """Dashboard概览数据"""
    from portfolios.models import Portfolio
    
    # 热门帖子
    trending_posts = Content.objects.filter(status='PUBLISHED').order_by('-like_count', '-comment_count')[:10]
    trending_serializer = ContentListSerializer(trending_posts, many=True, context={'request': request})
    
    # 热门组合
    top_portfolios = Portfolio.objects.filter(is_public=True).order_by('-returns_ytd')[:5]
    from portfolios.serializers import PortfolioListSerializer
    portfolio_serializer = PortfolioListSerializer(top_portfolios, many=True, context={'request': request})
    
    # 社区统计
    active_investors_count = User.objects.filter(is_active=True).count()
    strategies_shared_count = Portfolio.objects.filter(is_public=True).count()
    
    # 模拟市场数据（实际项目中应该从真实数据源获取）
    market_series = [
        {"name": "Mon", "value": 4200},
        {"name": "Tue", "value": 4150},
        {"name": "Wed", "value": 4300},
        {"name": "Thu", "value": 4250},
        {"name": "Fri", "value": 4400},
    ]
    
    return Response({
        'code': 0,
        'data': {
            'marketSeries': market_series,
            'trendingPosts': trending_serializer.data,
            'topPortfolios': portfolio_serializer.data,
            'communityStats': {
                'activeInvestorsCount': active_investors_count,
                'strategiesSharedCount': strategies_shared_count
            }
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def global_search(request):
    """全局搜索"""
    q = request.query_params.get('q', '')
    search_type = request.query_params.get('type', 'all')
    
    results = {
        'posts': {'items': [], 'total': 0},
        'assets': {'items': [], 'total': 0},
        'portfolios': {'items': [], 'total': 0}
    }
    
    if q:
        if search_type in ['all', 'post']:
            posts = Content.objects.filter(
                Q(title__icontains=q) | Q(body__icontains=q),
                status='PUBLISHED'
            )[:10]
            results['posts'] = {
                'items': ContentListSerializer(posts, many=True, context={'request': request}).data,
                'total': posts.count()
            }
        
        if search_type in ['all', 'asset']:
            assets = Asset.objects.filter(
                Q(code__icontains=q) | Q(name__icontains=q)
            )[:10]
            results['assets'] = {
                'items': AssetSerializer(assets, many=True).data,
                'total': assets.count()
            }
        
        if search_type in ['all', 'portfolio']:
            from portfolios.models import Portfolio
            from portfolios.serializers import PortfolioListSerializer
            portfolios = Portfolio.objects.filter(
                Q(title__icontains=q) | Q(description__icontains=q),
                is_public=True
            )[:10]
            results['portfolios'] = {
                'items': PortfolioListSerializer(portfolios, many=True, context={'request': request}).data,
                'total': portfolios.count()
            }
    
    return Response({
        'code': 0,
        'data': results
    })