from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from datetime import timedelta, datetime
from accounts.models import UserBehaviorDaily
from invest_backend.permissions import IsModeratorOrAdmin

from .models import (
    Report, Alert, ModerationQueueItem, ModerationRule, ModerationHit,
    CommunityMetricDaily, TopicMetricDaily,
)
from .serializers import (
    ReportCreateSerializer, ReportListSerializer, AlertSerializer,
    ModerationQueueItemSerializer, ModerationRuleSerializer, ModerationHitSerializer,
    CommunityMetricDailySerializer, TopicMetricDailySerializer,
)


def _ensure_admin_role(request):
    if request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({
            'code': 4030,
            'message': '无权限'
        }, status=status.HTTP_403_FORBIDDEN)
    return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_report(request):
    """创建举报"""
    serializer = ReportCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        report = serializer.save()
        return Response({
            'code': 0, 
            'message': '举报提交成功',
            'data': {'id': report.id}
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'code': 4001, 
        'message': '举报失败',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


class UserReportsView(generics.ListAPIView):
    """用户举报列表"""
    serializer_class = ReportListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(reporter=self.request.user).order_by('-created_at')


# 以下为管理员功能，需要相应权限

class AdminReportsView(generics.ListAPIView):
    """管理员查看举报列表"""
    serializer_class = ReportListSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrAdmin]

    def get_queryset(self):
        # 检查权限
        if self.request.user.role not in ['MODERATOR', 'ADMIN']:
            return Report.objects.none()
        
        queryset = Report.objects.all()
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
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
def handle_report(request, pk):
    """处理举报"""
    # 权限检查
    if request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({
            'code': 4030, 
            'message': '无权限'
        }, status=status.HTTP_403_FORBIDDEN)
    
    report = get_object_or_404(Report, pk=pk)
    
    status_value = request.data.get('status')
    handle_result = request.data.get('handleResult', '')
    result_value = request.data.get('result', '')
    action_taken = request.data.get('actionTaken', '')

    if status_value not in ['PENDING', 'RESOLVED']:
        return Response({
            'code': 4001, 
            'message': '无效的状态'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    report.status = status_value
    report.handle_result = handle_result
    report.handled_by = request.user
    report.handle_time = timezone.now()
    if result_value:
        report.result = result_value
    if action_taken:
        report.action_taken = action_taken

    queue_item = None
    if report.target_type == 'POST' and report.target_id:
        from content.models import Content
        content = Content.objects.filter(id=report.target_id).first()
        if content:
            if action_taken == 'TAKE_DOWN':
                content.status = 'TAKEN_DOWN'
                content.reject_reason = handle_result or '举报成立，管理员下架'
                content.reviewed_by = request.user
                content.save(update_fields=['status', 'reject_reason', 'reviewed_by', 'updated_at'])
            elif action_taken in ['QUEUE_REVIEW', 'REVIEW']:
                queue_item, _ = ModerationQueueItem.objects.get_or_create(
                    content=content,
                    status='PENDING',
                    defaults={
                        'source': 'REPORT',
                        'risk_level': 'MEDIUM',
                        'risk_score': 50,
                        'reason_summary': (handle_result or report.reason)[:255],
                    }
                )
            if queue_item:
                report.linked_queue_item = queue_item
    report.save()
    
    return Response({
        'code': 0, 
        'message': '处理成功'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_stats(request):
    """管理员统计数据"""
    if request.user.role not in ['MODERATOR', 'ADMIN']:
        return Response({
            'code': 4030, 
            'message': '无权限'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from content.models import Content
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from datetime import timedelta
    
    User = get_user_model()
    
    # 统计数据
    pending_posts_count = Content.objects.filter(status='PENDING_REVIEW').count()
    open_reports_count = Report.objects.filter(status='PENDING').count()
    
    # 过去24小时新注册用户
    yesterday = timezone.now() - timedelta(days=1)
    new_users_24h = User.objects.filter(created_at__gte=yesterday).count()
    
    return Response({
        'code': 0,
        'data': {
            'pendingPostsCount': pending_posts_count,
            'openReportsCount': open_reports_count,
            'newUsers24h': new_users_24h
        }
    })


class ModerationQueueView(generics.ListAPIView):
    """可疑内容队列"""
    serializer_class = ModerationQueueItemSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrAdmin]

    def get_queryset(self):
        queryset = ModerationQueueItem.objects.select_related('content', 'decided_by').all()
        status_param = self.request.query_params.get('status', 'PENDING')
        if status_param:
            queryset = queryset.filter(status=status_param)
        risk_level = self.request.query_params.get('riskLevel')
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        return queryset.order_by('-risk_score', '-created_at')

    def list(self, request, *args, **kwargs):
        perm_error = _ensure_admin_role(request)
        if perm_error:
            return perm_error
        queryset = self.get_queryset()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))
        total = queryset.count()
        items = queryset[(page - 1) * page_size: page * page_size]
        serializer = self.get_serializer(items, many=True)
        return Response({
            'code': 0,
            'data': {
                'items': serializer.data,
                'page': page,
                'pageSize': page_size,
                'total': total,
            }
        })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def moderation_queue_decision(request, pk):
    perm_error = _ensure_admin_role(request)
    if perm_error:
        return perm_error
    queue_item = get_object_or_404(ModerationQueueItem.objects.select_related('content'), pk=pk)
    target_status = request.data.get('status')
    if target_status not in ['PUBLISHED', 'REJECTED', 'TAKEN_DOWN']:
        return Response({'code': 4001, 'message': '无效状态'}, status=status.HTTP_400_BAD_REQUEST)

    content = queue_item.content
    content.status = target_status
    content.reviewed_by = request.user
    if target_status == 'PUBLISHED' and not content.published_at:
        content.published_at = timezone.now()
    if target_status == 'REJECTED':
        content.reject_reason = request.data.get('reason', '')
    content.save()

    queue_item.status = 'RESOLVED'
    queue_item.decided_status = target_status
    queue_item.decided_by = request.user
    queue_item.decided_at = timezone.now()
    queue_item.save(update_fields=['status', 'decided_status', 'decided_by', 'decided_at', 'updated_at'])

    return Response({'code': 0, 'message': '处理成功'})


class ModerationRuleView(generics.ListCreateAPIView):
    serializer_class = ModerationRuleSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrAdmin]
    queryset = ModerationRule.objects.all().order_by('rule_type', 'id')

    def list(self, request, *args, **kwargs):
        perm_error = _ensure_admin_role(request)
        if perm_error:
            return perm_error
        data = self.get_serializer(self.get_queryset(), many=True).data
        return Response({'code': 0, 'data': {'items': data, 'total': len(data)}})

    def create(self, request, *args, **kwargs):
        perm_error = _ensure_admin_role(request)
        if perm_error:
            return perm_error
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            return Response({'code': 0, 'data': self.get_serializer(obj).data}, status=status.HTTP_201_CREATED)
        return Response({'code': 4001, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def moderation_rule_update(request, pk):
    perm_error = _ensure_admin_role(request)
    if perm_error:
        return perm_error
    rule = get_object_or_404(ModerationRule, pk=pk)
    serializer = ModerationRuleSerializer(rule, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'code': 0, 'data': serializer.data})
    return Response({'code': 4001, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ModerationHitsView(generics.ListAPIView):
    serializer_class = ModerationHitSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrAdmin]

    def get_queryset(self):
        queryset = ModerationHit.objects.select_related('rule', 'content', 'user').all()
        content_id = self.request.query_params.get('contentId')
        user_id = self.request.query_params.get('userId')
        rule_type = self.request.query_params.get('ruleType')
        if content_id:
            queryset = queryset.filter(content_id=content_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if rule_type:
            queryset = queryset.filter(rule__rule_type=rule_type)
        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        perm_error = _ensure_admin_role(request)
        if perm_error:
            return perm_error
        queryset = self.get_queryset()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))
        total = queryset.count()
        items = queryset[(page - 1) * page_size: page * page_size]
        serializer = self.get_serializer(items, many=True)
        return Response({
            'code': 0,
            'data': {'items': serializer.data, 'page': page, 'pageSize': page_size, 'total': total}
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_activity(request):
    perm_error = _ensure_admin_role(request)
    if perm_error:
        return perm_error
    date_from = request.query_params.get('from')
    date_to = request.query_params.get('to')
    qs = CommunityMetricDaily.objects.all().order_by('stat_date')
    if date_from:
        qs = qs.filter(stat_date__gte=date_from)
    if date_to:
        qs = qs.filter(stat_date__lte=date_to)
    data = CommunityMetricDailySerializer(qs, many=True).data
    return Response({'code': 0, 'data': {'items': data, 'total': len(data)}})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_topics_hot(request):
    perm_error = _ensure_admin_role(request)
    if perm_error:
        return perm_error
    date_from = request.query_params.get('from')
    date_to = request.query_params.get('to')
    top_n = int(request.query_params.get('topN', 20))
    qs = TopicMetricDaily.objects.all()
    if date_from:
        qs = qs.filter(stat_date__gte=date_from)
    if date_to:
        qs = qs.filter(stat_date__lte=date_to)
    agg = (
        qs.values('topic')
        .annotate(
            post_count=Sum('post_count'),
            comment_count=Sum('comment_count'),
            like_count=Sum('like_count'),
            heat_score=Sum('heat_score'),
        )
        .order_by('-heat_score')[:top_n]
    )
    return Response({'code': 0, 'data': {'items': list(agg), 'total': len(agg)}})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_users_engagement(request):
    perm_error = _ensure_admin_role(request)
    if perm_error:
        return perm_error
    range_param = request.query_params.get('range', '30d')
    days = 30 if range_param == '30d' else 7
    start_date = timezone.now().date() - timedelta(days=days - 1)
    rows = (
        UserBehaviorDaily.objects
        .filter(stat_date__gte=start_date)
        .values('user_id', 'user__username', 'user__display_name')
        .annotate(
            post_count=Sum('post_count'),
            comment_count=Sum('comment_count'),
            violation_count=Sum('violation_count'),
            reported_count=Sum('reported_count'),
            received_likes=Sum('received_likes'),
        )
    )
    items = []
    for row in rows:
        score = int((row['post_count'] or 0) * 4 + (row['comment_count'] or 0) * 2 + (row['received_likes'] or 0))
        items.append({
            'userId': row['user_id'],
            'username': row['user__username'],
            'displayName': row['user__display_name'],
            'postCount': row['post_count'] or 0,
            'commentCount': row['comment_count'] or 0,
            'violationCount': row['violation_count'] or 0,
            'reportedCount': row['reported_count'] or 0,
            'receivedLikes': row['received_likes'] or 0,
            'engagementScore': score,
        })
    items.sort(key=lambda x: x['engagementScore'], reverse=True)
    return Response({'code': 0, 'data': {'items': items[:100], 'total': len(items)}})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_dashboard_overview(request):
    perm_error = _ensure_admin_role(request)
    if perm_error:
        return perm_error
    today = timezone.now().date()
    last7 = today - timedelta(days=6)
    metrics = CommunityMetricDaily.objects.filter(stat_date__gte=last7)
    top_topics = (
        TopicMetricDaily.objects.filter(stat_date__gte=last7)
        .values('topic')
        .annotate(heat_score=Sum('heat_score'))
        .order_by('-heat_score')[:10]
    )
    data = {
        'dauAvg7d': round(metrics.aggregate(v=Avg('dau')).get('v') or 0, 2),
        'posts7d': metrics.aggregate(v=Sum('post_count')).get('v') or 0,
        'comments7d': metrics.aggregate(v=Sum('comment_count')).get('v') or 0,
        'reports7d': metrics.aggregate(v=Sum('report_count')).get('v') or 0,
        'reviewPassRateAvg7d': round(metrics.aggregate(v=Avg('review_pass_rate')).get('v') or 0, 2),
        'topTopics': list(top_topics),
    }
    return Response({'code': 0, 'data': data})


class AdminAlertsView(generics.ListAPIView):
    """管理员告警列表"""
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrAdmin]

    def get_queryset(self):
        if self.request.user.role not in ['MODERATOR', 'ADMIN']:
            return Alert.objects.none()
        
        queryset = Alert.objects.all()
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        alert_type = self.request.query_params.get('alertType')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
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
def admin_handle_alert(request, pk):
    """
    管理员处理告警：
    PATCH /api/admin/alerts/{id}/
    body: { "status": "RESOLVED" | "IGNORED", "handleResult": "备注说明" }
    """
    user = request.user
    if user.role not in ['MODERATOR', 'ADMIN']:
        return Response({
            'code': 4030,
            'message': '无权限'
        }, status=status.HTTP_403_FORBIDDEN)

    alert = get_object_or_404(Alert, pk=pk)

    status_value = request.data.get('status')
    handle_result = request.data.get('handleResult', '')

    if status_value not in ['OPEN', 'RESOLVED', 'IGNORED']:
        return Response({
            'code': 4001,
            'message': '无效的状态'
        }, status=status.HTTP_400_BAD_REQUEST)

    alert.status = status_value
    alert.handle_result = handle_result
    alert.handled_by = user
    alert.handle_time = timezone.now()
    alert.save()

    return Response({
        'code': 0,
        'message': '告警已更新'
    })