import json
import time

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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


def _notification_stream(request):
    """
    SSE 流：推送当前用户最新通知与未读数量

    - 间隔 3 秒轮询一次数据库
    - 最长保持 5 分钟（100 次循环）
    """
    user = request.user

    def event_stream():
        if not user.is_authenticated:
            # 未登录直接结束
            yield 'event: error\ndata: {"detail": "unauthorized"}\n\n'
            return

        last_sent_ts = None
        for _ in range(100):
            # 重新获取用户，避免长连接期间用户被删除等情况
            unread_qs = Notification.objects.filter(user=user, is_read=False)
            latest_qs = Notification.objects.filter(user=user).order_by('-created_at')[:10]

            serializer = NotificationSerializer(latest_qs, many=True)
            payload = {
                'unreadCount': unread_qs.count(),
                'items': serializer.data,
            }

            # 使用最新通知的 created_at 作为版本戳，避免无变化时重复发送
            latest_ts = serializer.data[0]['created_at'] if serializer.data else None
            if latest_ts != last_sent_ts:
                last_sent_ts = latest_ts
                data_str = json.dumps(payload, ensure_ascii=False)
                yield f'data: {data_str}\n\n'

            time.sleep(3)

        # 主动告知前端连接已结束，便于前端做重连策略
        yield 'event: close\ndata: {"reason": "timeout"}\n\n'

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    # SSE 推荐关闭缓存
    response['Cache-Control'] = 'no-cache'
    return response


@permission_classes([IsAuthenticated])
def notifications_stream(request):
    """
    GET /api/notifications/stream/

    通知 SSE 长连接：用于前端 MainLayout 实时刷新未读数和通知列表。
    """
    return _notification_stream(request)