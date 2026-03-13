from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from .models import Conversation, ConversationParticipant, Message, MessageReadLog
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
                content=serializer.validated_data['content'],
            )
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

