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
        
        # 只显示未读
        unread_only = self.request.query_params.get('unreadOnly', 'false').lower() == 'true'
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        return queryset


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