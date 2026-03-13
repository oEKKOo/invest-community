from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Report, Alert
from .serializers import ReportCreateSerializer, ReportListSerializer, AlertSerializer


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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 检查权限
        if self.request.user.role not in ['MODERATOR', 'ADMIN']:
            return Report.objects.none()
        
        queryset = Report.objects.all()
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset.order_by('-created_at')


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


class AdminAlertsView(generics.ListAPIView):
    """管理员告警列表"""
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

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