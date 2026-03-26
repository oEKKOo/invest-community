from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
import os
import re

from .models import (
    Content, Comment, Asset, Board, Like, Favorite, ContentAsset, ContentBoard,
    Poll, PollOption, PollVote, Repost, Mention, ContentAttachment, ContentMeta, CommentAttachment
)
from .serializers import (
    ContentListSerializer, ContentDetailSerializer, ContentCreateSerializer,
    CommentSerializer, CommentCreateSerializer, AssetSerializer, LikeSerializer,
    BoardSerializer, BoardCreateUpdateSerializer, ContentAttachmentSerializer, CommentAttachmentSerializer, PollSerializer
)
from notifications.events import publish_event

User = get_user_model()

MENTION_PATTERN = re.compile(r'@([A-Za-z0-9_\u4e00-\u9fa5]{2,30})')


def _extract_mention_users(text: str):
    if not text:
        return []
    usernames = set(MENTION_PATTERN.findall(text))
    if not usernames:
        return []
    users = User.objects.filter(username__in=usernames, is_active=True)
    return list(users)


def _create_mentions(source_type: str, source_id: int, from_user, text: str):
    users = _extract_mention_users(text)
    for u in users:
        if u.id == from_user.id:
            continue
        Mention.objects.get_or_create(
            source_type=source_type,
            source_id=source_id,
            to_user=u,
            defaults={'from_user': from_user}
        )
        publish_event("mention.created", from_user=from_user, to_user=u, source_type=source_type, source_id=source_id)


class ContentListView(generics.ListCreateAPIView):
    """内容列表和创建"""
    serializer_class = ContentListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Content.objects.select_related('author').prefetch_related('assets', 'boards', 'attachments', 'meta', 'poll__options')
        
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

        board_id = self.request.query_params.get('boardId')
        if board_id:
            queryset = queryset.filter(boards__id=board_id)

        board_ids = self.request.query_params.getlist('boardIds')
        if board_ids:
            queryset = queryset.filter(boards__id__in=board_ids).distinct()
        
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
        queryset = self.get_queryset()

        # 分页处理（保持与前端约定的 page / pageSize / total 响应结构）
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))
        
        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_queryset = queryset[start:end]
        serializer = self.get_serializer(paginated_queryset, many=True)

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
        """
        重写 create 方法以返回自定义响应格式
        支持 assetIds（ID数组）和 assetCodes（代码数组）两种关联方式
        """
        # 禁言/封禁用户不允许发帖
        if not request.user.is_authenticated:
            return Response({'code': 4010, 'message': '需要登录'}, status=status.HTTP_401_UNAUTHORIZED)
        if getattr(request.user, 'status', 'NORMAL') in ['MUTED', 'BANNED']:
            return Response({'code': 4030, 'message': '当前账户已被限制发帖或封禁'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ContentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            content = serializer.save(author=request.user)
            _create_mentions('POST', content.id, request.user, content.body)

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
    content = get_object_or_404(Content.objects.prefetch_related('attachments', 'poll__options', 'meta'), pk=pk)
    
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
        
        serializer = ContentCreateSerializer(content, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            # 处理状态变更
            new_status = serializer.validated_data.get('status', content.status)
            if new_status == 'PUBLISHED' and content.published_at is None:
                serializer.validated_data['published_at'] = timezone.now()
            
            serializer.save()
            _create_mentions('POST', content.id, request.user, content.body)
            
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


@api_view(['GET', 'POST'])
def post_comments(request, pk):
    """
    处理帖子评论
    - GET: 获取评论列表（仅顶级评论，每条附带少量子回复预览）
    - POST: 创建评论
    """
    content = get_object_or_404(Content, pk=pk)
    
    if request.method == 'GET':
        # 获取顶级评论列表（按时间升序）
        qs = Comment.objects.filter(
            content=content,
            parent__isnull=True,
            status='NORMAL'
        ).select_related('author', 'reply_to_user').prefetch_related('attachments').order_by('created_at')

        # 可选分页参数（不改变原有返回结构，仍然返回数组）
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('pageSize', 50))
        except (TypeError, ValueError):
            page, page_size = 1, 50

        start = (page - 1) * page_size
        end = start + page_size
        comments = qs[start:end]

        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response({'code': 0, 'data': serializer.data})
    
    elif request.method == 'POST':
        # 创建评论 - 需要认证
        if not request.user.is_authenticated:
            return Response({'code': 4010, 'message': '需要登录'}, 
                          status=status.HTTP_401_UNAUTHORIZED)

        # 禁言/封禁用户不允许发表评论
        if getattr(request.user, 'status', 'NORMAL') in ['MUTED', 'BANNED']:
            return Response({'code': 4030, 'message': '当前账户已被限制评论或封禁'},
                            status=status.HTTP_403_FORBIDDEN)
        
        serializer = CommentCreateSerializer(
            data=request.data,
            context={'request': request, 'content_id': content.id}
        )

        if serializer.is_valid():
            comment = serializer.save()

            # 更新内容的评论数
            Content.objects.filter(pk=pk).update(comment_count=F('comment_count') + 1)

            # 事件：评论已创建（用于通知 / 积分 / 推荐特征等扩展）
            publish_event("comment.created", comment=comment)
            _create_mentions('COMMENT', comment.id, request.user, comment.body)

            response_data = CommentSerializer(comment, context={'request': request}).data
            return Response({'code': 0, 'data': response_data}, status=status.HTTP_201_CREATED)

        return Response({'code': 4001, 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def comment_detail(request, comment_id):
    """
    评论详情：
    - PATCH：编辑评论内容（仅作者在限定时间内可编辑）
    - DELETE：删除评论（软删除）
    """
    comment = get_object_or_404(Comment, pk=comment_id)

    # 公共权限检查：作者或管理员
    if comment.author != request.user and request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({'code': 4030, 'message': '无权操作该评论'},
                        status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PATCH':
        # 可选：仅允许在创建后 10 分钟内编辑
        from datetime import timedelta

        time_delta = timezone.now() - comment.created_at
        if time_delta > timedelta(minutes=10) and request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response(
                {'code': 4001, 'message': '评论已超过可编辑时间'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_text = request.data.get('text', '').strip()
        if not new_text:
            return Response(
                {'code': 4001, 'message': '评论内容不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment.body = new_text
        comment.updated_at = timezone.now()
        comment.save()

        data = CommentSerializer(comment, context={'request': request}).data
        return Response({'code': 0, 'data': data})

    # DELETE
    with transaction.atomic():
        comment.status = 'DELETED'
        comment.save()

        # 更新内容的评论数（简单减一，复杂场景可根据实际可见评论数调整）
        Content.objects.filter(pk=comment.content_id).update(
            comment_count=F('comment_count') - 1
        )

    return Response({'code': 0, 'message': '删除成功'})


@api_view(['GET'])
@permission_classes([AllowAny])
def comment_replies(request, comment_id):
    """
    获取某条评论的子回复列表（分页）
    GET /api/comments/{id}/replies/
    """
    parent_comment = get_object_or_404(Comment, pk=comment_id)

    qs = parent_comment.replies.filter(status='NORMAL').select_related('author', 'reply_to_user').prefetch_related('attachments').order_by('created_at')

    try:
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))
    except (TypeError, ValueError):
        page, page_size = 1, 20

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    items = qs[start:end]

    serializer = CommentSerializer(items, many=True, context={'request': request})
    return Response({
        'code': 0,
        'data': {
            'items': serializer.data,
            'page': page,
            'pageSize': page_size,
            'total': total,
        }
    })


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def toggle_like(request):
    """点赞/取消点赞"""
    if request.method == 'POST':
        serializer = LikeSerializer(data=request.data)
        if serializer.is_valid():
            target_type = serializer.validated_data['targetType']
            target_id = serializer.validated_data['targetId']

            like, created = Like.objects.get_or_create(
                user=request.user,
                target_type=target_type,
                target_id=target_id
            )

            if created:
                # 更新点赞计数
                _update_like_count(target_type, target_id, 1)

                # 事件：点赞已创建
                publish_event(
                    "like.created",
                    user=request.user,
                    target_type=target_type,
                    target_id=target_id,
                    like=like,
                )

                return Response({'code': 0, 'message': '点赞成功', 'data': {'id': like.id}})
            else:
                return Response({'code': 4090, 'message': '已点赞过'},
                                status=status.HTTP_409_CONFLICT)

        return Response({'code': 4001, 'message': '参数错误', 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        serializer = LikeSerializer(data=request.data)
        if serializer.is_valid():
            target_type = serializer.validated_data['targetType']
            target_id = serializer.validated_data['targetId']
            
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
        
        return Response({'code': 4001, 'message': '参数错误', 'errors': serializer.errors}, 
                       status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def comment_toggle_like(request, comment_id):
    """
    点赞/取消点赞评论的语义化别名接口：
    - POST   /api/comments/{id}/like/
    - DELETE /api/comments/{id}/like/
    内部复用通用点赞逻辑。
    """
    # 构造针对 COMMENT 目标的参数
    data = {
        'targetType': 'COMMENT',
        'targetId': comment_id,
    }

    if request.method == 'POST':
        serializer = LikeSerializer(data=data)
        if serializer.is_valid():
            target_type = serializer.validated_data['targetType']
            target_id = serializer.validated_data['targetId']

            like, created = Like.objects.get_or_create(
                user=request.user,
                target_type=target_type,
                target_id=target_id
            )

            if created:
                _update_like_count(target_type, target_id, 1)
                publish_event(
                    "like.created",
                    user=request.user,
                    target_type=target_type,
                    target_id=target_id,
                    like=like,
                )
                return Response({'code': 0, 'message': '点赞成功', 'data': {'id': like.id}})

            return Response({'code': 4090, 'message': '已点赞过'},
                            status=status.HTTP_409_CONFLICT)

        return Response({'code': 4001, 'message': '参数错误', 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    serializer = LikeSerializer(data=data)
    if serializer.is_valid():
        target_type = serializer.validated_data['targetType']
        target_id = serializer.validated_data['targetId']

        try:
            like = Like.objects.get(
                user=request.user,
                target_type=target_type,
                target_id=target_id
            )
            like.delete()
            _update_like_count(target_type, target_id, -1)
            return Response({'code': 0, 'message': '取消点赞成功'})
        except Like.DoesNotExist:
            return Response({'code': 4040, 'message': '未点赞过'},
                            status=status.HTTP_404_NOT_FOUND)

    return Response({'code': 4001, 'message': '参数错误', 'errors': serializer.errors},
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
    """
    资产列表和搜索
    新增 withQuote=1 参数：附带最新行情快照（来自数据库快照，不实时调 Finnhub）
    新增 market 参数：按市场筛选（SH/SZ/BJ/HK/US）
    新增 status 参数：按交易状态筛选（ACTIVE/SUSPENDED/DELISTED）
    """
    serializer_class = AssetSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Asset.objects.all()

        asset_type = self.request.query_params.get('type')
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)

        market = self.request.query_params.get('market')
        if market:
            queryset = queryset.filter(market=market)

        asset_status = self.request.query_params.get('status')
        if asset_status:
            queryset = queryset.filter(status=asset_status)
        else:
            # 默认只显示正常交易标的
            queryset = queryset.filter(status='ACTIVE')

        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(code__icontains=q) | Q(name__icontains=q) | Q(industry__icontains=q)
            )

        return queryset.order_by('code')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        with_quote = request.query_params.get('withQuote', '0') == '1'

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))
        total = queryset.count()
        start = (page - 1) * page_size
        items = queryset[start:start + page_size]

        serializer = AssetSerializer(items, many=True)
        data = serializer.data

        # 附带行情快照（withQuote=1）
        if with_quote:
            asset_ids = [a['id'] for a in data]
            # 批量获取最新快照（按 created_at DESC 取每资产最新一条，避免 quote_time 相同时歧义）
            from market_data.models import AssetQuoteSnapshot
            from django.db.models import Subquery, OuterRef
            latest_snapshot_id = AssetQuoteSnapshot.objects.filter(
                asset_id=OuterRef('asset_id')
            ).order_by('-created_at').values('id')[:1]

            snapshots = AssetQuoteSnapshot.objects.filter(
                asset_id__in=asset_ids,
                id=Subquery(latest_snapshot_id)
            ).values(
                'asset_id', 'price', 'change_amount', 'change_pct',
                'volume', 'quote_time', 'created_at'
            )

            snapshot_map = {s['asset_id']: s for s in snapshots}

            for item in data:
                snap = snapshot_map.get(item['id'])
                if snap:
                    item['price'] = float(snap['price']) if snap['price'] is not None else None
                    item['change'] = float(snap['change_amount']) if snap['change_amount'] is not None else None
                    item['changePct'] = float(snap['change_pct']) if snap['change_pct'] is not None else None
                    item['volume'] = int(snap['volume']) if snap['volume'] is not None else None
                    item['quoteTime'] = snap['quote_time'].isoformat() if snap['quote_time'] else None
                    item['dataUpdatedAt'] = snap['created_at'].isoformat() if snap['created_at'] else None
                else:
                    item['price'] = None
                    item['change'] = None
                    item['changePct'] = None
                    item['volume'] = None
                    item['quoteTime'] = None
                    item['dataUpdatedAt'] = None

        return Response({
            'code': 0,
            'data': {
                'items': data,
                'page': page,
                'pageSize': page_size,
                'total': total,
            }
        })


@api_view(['GET'])
def asset_detail(request, pk):
    """
    资产详情
    改造：直接附带最新行情 quote 字段（减少前端额外请求）
    """
    asset = get_object_or_404(Asset, pk=pk)
    serializer = AssetSerializer(asset)
    data = serializer.data

    # 附带 quote 字段（camelCase，与 /assets/{id}/quote/ 接口格式保持一致）
    try:
        from market_data.tasks import get_or_refresh_quote
        quote = get_or_refresh_quote(asset)
        if quote:
            data['quote'] = {
                'assetId': quote['asset_id'],
                'code': quote['code'],
                'name': quote['name'],
                'market': quote['market'],
                'quoteTime': quote['quote_time'],
                'price': quote['price'],
                'change': quote['change_amount'],
                'changePct': quote['change_pct'],
                'open': quote['open'],
                'high': quote['high'],
                'low': quote['low'],
                'prevClose': quote['prev_close'],
                'volume': quote['volume'],
                'amount': quote['amount'],
                'dataUpdatedAt': quote['data_updated_at'],
                'isStale': quote.get('is_stale', False),
            }
        else:
            data['quote'] = None
    except Exception:
        data['quote'] = None

    return Response({'code': 0, 'data': data})


@api_view(['GET'])
def asset_posts(request, pk):
    """资产相关帖子"""
    asset = get_object_or_404(Asset, pk=pk)
    
    # 获取关联该资产的内容
    queryset = Content.objects.filter(
        assets=asset,
        status='PUBLISHED'
    ).select_related('author').prefetch_related('assets', 'boards')
    
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
        
        queryset = Content.objects.select_related('author').prefetch_related('assets', 'boards', 'attachments', 'meta')
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        board_id = self.request.query_params.get('boardId')
        if board_id:
            queryset = queryset.filter(boards__id=board_id)
        
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """重写list方法，返回统一的响应格式"""
        # 权限检查
        if request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({
                'code': 4030,
                'message': '无权限'
            }, status=status.HTTP_403_FORBIDDEN)

        queryset = self.get_queryset()

        # 手动分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size

        paginated_queryset = queryset[start:end]
        serializer = self.get_serializer(paginated_queryset, many=True)

        return Response({
            'code': 0,
            'data': {
                'items': serializer.data,
                'page': page,
                'pageSize': page_size,
                'total': total
            }
        })


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

    # 事件：帖子审核结果
    publish_event(
        "content.reviewed",
        content=content,
        new_status=new_status,
        reject_reason=reject_reason,
        reviewer=request.user,
    )

    return Response({
        'code': 0,
        'message': '状态更新成功'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_content_attachment(request):
    """上传帖子附件（multipart）"""
    if getattr(request.user, 'status', 'NORMAL') in ['MUTED', 'BANNED']:
        return Response({'code': 4030, 'message': '当前账户状态不可上传附件'}, status=status.HTTP_403_FORBIDDEN)
    upload = request.FILES.get('file')
    if not upload:
        return Response({'code': 4001, 'message': '缺少文件'}, status=status.HTTP_400_BAD_REQUEST)

    ext = os.path.splitext(upload.name)[1].lower()
    allowed = {'.pdf', '.xls', '.xlsx', '.csv', '.png', '.jpg', '.jpeg', '.webp'}
    if ext not in allowed:
        return Response({'code': 4001, 'message': '不支持的文件类型'}, status=status.HTTP_400_BAD_REQUEST)

    attachment = ContentAttachment.objects.create(
        uploaded_by=request.user,
        file=upload,
        original_name=upload.name,
        mime_type=getattr(upload, 'content_type', '') or '',
        file_size=getattr(upload, 'size', 0) or 0,
        status='PENDING'
    )
    data = ContentAttachmentSerializer(attachment, context={'request': request}).data
    return Response({'code': 0, 'data': data}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_comment_attachment(request):
    """上传评论附件（multipart，无需审核）"""
    if getattr(request.user, 'status', 'NORMAL') in ['MUTED', 'BANNED']:
        return Response({'code': 4030, 'message': '当前账户状态不可上传附件'}, status=status.HTTP_403_FORBIDDEN)
    upload = request.FILES.get('file')
    if not upload:
        return Response({'code': 4001, 'message': '缺少文件'}, status=status.HTTP_400_BAD_REQUEST)

    ext = os.path.splitext(upload.name)[1].lower()
    allowed = {'.pdf', '.xls', '.xlsx', '.csv', '.png', '.jpg', '.jpeg', '.webp'}
    if ext not in allowed:
        return Response({'code': 4001, 'message': '不支持的文件类型'}, status=status.HTTP_400_BAD_REQUEST)

    attachment = CommentAttachment.objects.create(
        uploaded_by=request.user,
        file=upload,
        original_name=upload.name,
        mime_type=getattr(upload, 'content_type', '') or '',
        file_size=getattr(upload, 'size', 0) or 0,
    )
    data = CommentAttachmentSerializer(attachment, context={'request': request}).data
    return Response({'code': 0, 'data': data}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_content_attachment(request, attachment_id):
    attachment = get_object_or_404(ContentAttachment, pk=attachment_id)
    if attachment.status != 'APPROVED':
        if request.user.role not in ['MODERATOR', 'ADMIN'] and request.user != attachment.uploaded_by:
            return Response({'code': 4030, 'message': '附件审核中或未通过，无法下载'}, status=status.HTTP_403_FORBIDDEN)
    if not attachment.file:
        return Response({'code': 4040, 'message': '附件不存在'}, status=status.HTTP_404_NOT_FOUND)
    return Response({
        'code': 0,
        'data': {
            'id': attachment.id,
            'url': request.build_absolute_uri(attachment.file.url),
            'name': attachment.original_name or os.path.basename(attachment.file.name),
            'status': attachment.status,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_poll_vote(request, pk):
    content = get_object_or_404(Content, pk=pk)
    if not hasattr(content, 'poll'):
        return Response({'code': 4001, 'message': '该帖子不是投票类型'}, status=status.HTTP_400_BAD_REQUEST)
    poll = content.poll
    if poll.is_closed or (poll.expires_at and poll.expires_at < timezone.now()):
        return Response({'code': 4001, 'message': '投票已截止'}, status=status.HTTP_400_BAD_REQUEST)

    option_ids = request.data.get('optionIds') or []
    if not isinstance(option_ids, list) or not option_ids:
        return Response({'code': 4001, 'message': '请选择投票选项'}, status=status.HTTP_400_BAD_REQUEST)
    if not poll.allow_multiple and len(option_ids) > 1:
        return Response({'code': 4001, 'message': '该投票仅支持单选'}, status=status.HTTP_400_BAD_REQUEST)

    already = PollVote.objects.filter(poll=poll, user=request.user).exists()
    if already:
        return Response({'code': 4090, 'message': '你已投过票'}, status=status.HTTP_409_CONFLICT)

    options = list(PollOption.objects.filter(poll=poll, id__in=option_ids))
    if len(options) != len(set(option_ids)):
        return Response({'code': 4001, 'message': '存在无效选项'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        for opt in options:
            PollVote.objects.create(poll=poll, option=opt, user=request.user)
            PollOption.objects.filter(id=opt.id).update(vote_count=F('vote_count') + 1)
    publish_event("poll.voted", poll=poll, user=request.user, content=content)
    return Response({'code': 0, 'message': '投票成功'})


@api_view(['GET'])
@permission_classes([AllowAny])
def post_poll_result(request, pk):
    content = get_object_or_404(Content, pk=pk)
    if not hasattr(content, 'poll'):
        return Response({'code': 4001, 'message': '该帖子不是投票类型'}, status=status.HTTP_400_BAD_REQUEST)
    poll = Poll.objects.prefetch_related('options').get(pk=content.poll.id)
    return Response({'code': 0, 'data': PollSerializer(poll).data})


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def toggle_repost(request, pk):
    content = get_object_or_404(Content, pk=pk)
    meta, _ = ContentMeta.objects.get_or_create(content=content)
    if request.method == 'POST':
        repost, created = Repost.objects.get_or_create(
            user=request.user,
            content=content,
            defaults={'comment': request.data.get('comment', '').strip()},
        )
        if not created:
            return Response({'code': 4090, 'message': '已转发过该帖子'}, status=status.HTTP_409_CONFLICT)
        ContentMeta.objects.filter(id=meta.id).update(repost_count=F('repost_count') + 1)
        publish_event("repost.created", repost=repost, user=request.user, content=content)
        return Response({'code': 0, 'message': '转发成功'})
    deleted, _ = Repost.objects.filter(user=request.user, content=content).delete()
    if deleted:
        ContentMeta.objects.filter(id=meta.id).update(repost_count=F('repost_count') - 1)
    return Response({'code': 0, 'message': '取消转发成功'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_attachment_list(request):
    if request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({'code': 4030, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    qs = ContentAttachment.objects.select_related('uploaded_by', 'content', 'reviewed_by').order_by('-created_at')
    status_param = request.query_params.get('status')
    if status_param:
        qs = qs.filter(status=status_param)
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('pageSize', 20))
    total = qs.count()
    items = qs[(page - 1) * page_size: page * page_size]
    serializer = ContentAttachmentSerializer(items, many=True, context={'request': request})
    return Response({'code': 0, 'data': {'items': serializer.data, 'page': page, 'pageSize': page_size, 'total': total}})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_attachment_status(request, attachment_id):
    if request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({'code': 4030, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    attachment = get_object_or_404(ContentAttachment, pk=attachment_id)
    new_status = request.data.get('status')
    if new_status not in ['APPROVED', 'REJECTED']:
        return Response({'code': 4001, 'message': '无效状态'}, status=status.HTTP_400_BAD_REQUEST)
    attachment.status = new_status
    attachment.reject_reason = request.data.get('rejectReason', '') if new_status == 'REJECTED' else ''
    attachment.reviewed_by = request.user
    attachment.save(update_fields=['status', 'reject_reason', 'reviewed_by', 'updated_at'])
    publish_event("attachment.reviewed", attachment=attachment, reviewer=request.user, new_status=new_status)
    return Response({'code': 0, 'message': '附件状态更新成功'})


class BoardListView(generics.ListAPIView):
    """前台板块树查询（只读）"""
    serializer_class = BoardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Board.objects.select_related('parent').prefetch_related('children')

        board_type = self.request.query_params.get('type')
        if board_type:
            queryset = queryset.filter(board_type=board_type)

        parent_id = self.request.query_params.get('parentId')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        else:
            queryset = queryset.filter(parent__isnull=True)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        else:
            queryset = queryset.filter(status='ACTIVE')

        return queryset.order_by('sort_order', 'id')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'code': 0, 'data': {'items': serializer.data, 'total': queryset.count()}})


class AdminBoardListCreateView(generics.ListCreateAPIView):
    """管理员板块列表与创建"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BoardCreateUpdateSerializer
        return BoardSerializer

    def get_queryset(self):
        if self.request.user.role not in ['MODERATOR', 'ADMIN']:
            return Board.objects.none()
        queryset = Board.objects.select_related('parent').prefetch_related('children')
        board_type = self.request.query_params.get('type')
        if board_type:
            queryset = queryset.filter(board_type=board_type)
        parent_id = self.request.query_params.get('parentId')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset.order_by('board_type', 'sort_order', 'id')

    def list(self, request, *args, **kwargs):
        if request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({'code': 4030, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'code': 0, 'data': {'items': serializer.data, 'total': queryset.count()}})

    def create(self, request, *args, **kwargs):
        if request.user.role not in ['MODERATOR', 'ADMIN']:
            return Response({'code': 4030, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            board = serializer.save()
            return Response({'code': 0, 'data': BoardSerializer(board, context={'request': request}).data}, status=status.HTTP_201_CREATED)
        return Response({'code': 4001, 'message': '创建失败', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_board_detail(request, pk):
    """管理员板块详情、编辑、删除"""
    if request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({'code': 4030, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    board = get_object_or_404(Board, pk=pk)

    if request.method == 'GET':
        return Response({'code': 0, 'data': BoardSerializer(board, context={'request': request}).data})

    if request.method == 'PATCH':
        serializer = BoardCreateUpdateSerializer(board, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'code': 0, 'data': BoardSerializer(board, context={'request': request}).data})
        return Response({'code': 4001, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    if board.children.exists():
        return Response({'code': 4001, 'message': '存在子板块，无法删除'}, status=status.HTTP_400_BAD_REQUEST)
    if ContentBoard.objects.filter(board=board).exists():
        return Response({'code': 4001, 'message': '板块已关联内容，建议先停用或迁移'}, status=status.HTTP_400_BAD_REQUEST)
    board.delete()
    return Response({'code': 0, 'message': '删除成功'})


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_overview(request):
    """Dashboard概览数据"""
    from portfolios.models import Portfolio
    
    # 热门帖子
    trending_posts = Content.objects.filter(status='PUBLISHED').prefetch_related('boards', 'assets').order_by('-like_count', '-comment_count')[:10]
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
            ).prefetch_related('boards', 'assets')[:10]
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