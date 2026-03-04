from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """通知列表"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)

        # 按类型过滤（LIKE / COMMENT / FOLLOW / REVIEW_RESULT / SYSTEM）
        type_param = self.request.query_params.get('type')
        if type_param:
            queryset = queryset.filter(notification_type=type_param)

        # 只显示未读
        unread_only = self.request.query_params.get('unreadOnly', 'false').lower() == 'true'
        if unread_only:
            queryset = queryset.filter(is_read=False)

        return queryset.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """
        返回分页结构：items / page / pageSize / total
        与接口文档中其他列表接口保持一致。
        """
        queryset = self.get_queryset()

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 20))

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = queryset[start:end]
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    """标记通知为已读"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
    
    return Response({'code': 0, 'message': '标记成功'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    """标记所有通知为已读"""
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    
    count = notifications.update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return Response({
        'code': 0, 
        'message': f'标记了{count}条通知为已读'
    })