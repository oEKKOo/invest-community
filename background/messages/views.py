from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
import os
from .models import Conversation, ConversationParticipant, Message, MessageReadLog, MessageAttachment
from .serializers import (
    ConversationSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
)


def _user_is_muted_or_banned(user: User) -> bool:
    """被禁言/封禁用户不能发送私信"""
    if user.status == 'BANNED':
        return True
    if user.status == 'MUTED' and user.mute_until and user.mute_until > timezone.now():
        return True
    return False


def _get_conversation_for_user(user: User, conversation_id: int) -> Conversation:
    """确保当前用户是会话参与者"""
    return get_object_or_404(
        Conversation.objects.filter(participants__user=user).distinct(),
        pk=conversation_id,
    )


class ConversationListCreateView(APIView):
    """
    GET /api/messages/conversations/
      - 列出当前用户参与的会话列表
    POST /api/messages/conversations/
      - 创建新会话
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = (
            Conversation.objects.filter(participants__user=request.user)
            .prefetch_related('participants__user')
            .distinct()
        )
        serializer = ConversationSerializer(conversations, many=True, context={'request': request})
        return Response({'code': 0, 'data': {'items': serializer.data}})

    def post(self, request):
        if _user_is_muted_or_banned(request.user):
            return Response(
                {'code': 4030, 'message': '当前账号处于禁言/封禁状态，无法发送私信'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ConversationCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            conversation = serializer.save()
            data = ConversationSerializer(conversation, context={'request': request}).data
            return Response({'code': 0, 'data': data}, status=status.HTTP_201_CREATED)

        return Response(
            {'code': 4001, 'message': '创建会话失败', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ConversationMessagesView(APIView):
    """
    GET /api/messages/conversations/{id}/messages/
    POST /api/messages/conversations/{id}/messages/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        conversation = _get_conversation_for_user(request.user, pk)
        # 简单按时间升序返回最近 N 条，可根据需要增加分页
        messages = conversation.messages.select_related('sender').all()
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response({'code': 0, 'data': {'items': serializer.data}})

    def post(self, request, pk: int):
        if _user_is_muted_or_banned(request.user):
            return Response(
                {'code': 4030, 'message': '当前账号处于禁言/封禁状态，无法发送私信'},
                status=status.HTTP_403_FORBIDDEN,
            )

        conversation = _get_conversation_for_user(request.user, pk)
        serializer = MessageCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=(serializer.validated_data.get('content') or '').strip(),
            )
            attachment_ids = serializer.validated_data.get('attachmentIds', [])
            if attachment_ids:
                MessageAttachment.objects.filter(
                    id__in=attachment_ids,
                    uploaded_by=request.user,
                    message__isnull=True
                ).update(message=message)
            # 更新会话最新消息时间
            Conversation.objects.filter(pk=conversation.pk).update(
                last_message_at=message.created_at
            )
            data = MessageSerializer(message, context={'request': request}).data
            return Response({'code': 0, 'data': data}, status=status.HTTP_201_CREATED)

        return Response(
            {'code': 4001, 'message': '发送消息失败', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_message_read(request, pk: int):
    """
    POST /api/messages/{id}/read/
    标记单条消息为已读（幂等）
    """
    message = get_object_or_404(
        Message.objects.filter(conversation__participants__user=request.user).distinct(),
        pk=pk,
    )
    MessageReadLog.objects.get_or_create(message=message, user=request.user)
    return Response({'code': 0, 'message': '标记成功'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_message_attachment(request):
    if _user_is_muted_or_banned(request.user):
        return Response(
            {'code': 4030, 'message': '当前账号处于禁言/封禁状态，无法上传私信附件'},
            status=status.HTTP_403_FORBIDDEN,
        )

    upload = request.FILES.get('file')
    if not upload:
        return Response({'code': 4001, 'message': '缺少文件'}, status=status.HTTP_400_BAD_REQUEST)

    ext = os.path.splitext(upload.name)[1].lower()
    if ext not in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
        return Response({'code': 4001, 'message': '私信当前仅支持图片附件'}, status=status.HTTP_400_BAD_REQUEST)

    attachment = MessageAttachment.objects.create(
        uploaded_by=request.user,
        file=upload,
        original_name=upload.name,
        mime_type=getattr(upload, 'content_type', '') or '',
        file_size=getattr(upload, 'size', 0) or 0,
    )
    url = request.build_absolute_uri(attachment.file.url) if attachment.file else ''
    return Response({
        'code': 0,
        'data': {
            'id': attachment.id,
            'name': attachment.original_name,
            'mimeType': attachment.mime_type,
            'size': attachment.file_size,
            'url': url,
        }
    }, status=status.HTTP_201_CREATED)

