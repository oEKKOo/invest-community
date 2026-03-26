from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conversation, ConversationParticipant, Message, MessageReadLog, MessageAttachment

User = get_user_model()


class ConversationParticipantSerializer(serializers.ModelSerializer):
  """会话参与者简要信息"""
  userId = serializers.IntegerField(source='user_id', read_only=True)
  username = serializers.CharField(source='user.username', read_only=True)
  displayName = serializers.CharField(source='user.display_name', read_only=True)
  avatar = serializers.CharField(source='user.avatar_url', read_only=True)

  class Meta:
    model = ConversationParticipant
    fields = ['userId', 'username', 'displayName', 'avatar']


class MessageSerializer(serializers.ModelSerializer):
  """消息序列化器（读取）"""
  senderId = serializers.IntegerField(source='sender_id', read_only=True)
  senderName = serializers.CharField(source='sender.display_name', read_only=True)
  senderAvatar = serializers.CharField(source='sender.avatar_url', read_only=True)
  createdAt = serializers.DateTimeField(source='created_at', read_only=True)
  isRead = serializers.SerializerMethodField()
  attachments = serializers.SerializerMethodField()

  class Meta:
    model = Message
    fields = [
      'id',
      'conversation_id',
      'senderId',
      'senderName',
      'senderAvatar',
      'content',
      'is_deleted',
      'createdAt',
      'isRead',
      'attachments',
    ]

  def get_isRead(self, obj: Message) -> bool:
    user = self.context.get('request').user
    if not user or not user.is_authenticated:
      return False
    return MessageReadLog.objects.filter(message=obj, user=user).exists()

  def get_attachments(self, obj: Message):
    request = self.context.get('request')
    items = []
    for att in obj.attachments.all():
      url = att.file.url if att.file else ''
      if request and url:
        url = request.build_absolute_uri(url)
      items.append({
        'id': att.id,
        'name': att.original_name,
        'mimeType': att.mime_type,
        'size': att.file_size,
        'url': url,
      })
    return items


class MessageCreateSerializer(serializers.ModelSerializer):
  """发送消息序列化器"""

  class Meta:
    model = Message
    fields = ['content', 'attachmentIds']
    extra_kwargs = {
      'content': {'required': False, 'allow_blank': True}
    }

  attachmentIds = serializers.ListField(
    child=serializers.IntegerField(),
    required=False,
    write_only=True,
  )

  def validate_content(self, value: str) -> str:
    if value is None:
      return ''
    return value

  def validate(self, attrs):
    content = (attrs.get('content') or '').strip()
    attachment_ids = attrs.get('attachmentIds') or []
    if not content and not attachment_ids:
      raise serializers.ValidationError('消息内容和附件不能同时为空')
    return attrs


class ConversationSerializer(serializers.ModelSerializer):
  """会话列表/详情序列化器"""
  participants = ConversationParticipantSerializer(many=True, read_only=True)
  lastMessageAt = serializers.DateTimeField(source='last_message_at', read_only=True)
  createdAt = serializers.DateTimeField(source='created_at', read_only=True)

  class Meta:
    model = Conversation
    fields = ['id', 'title', 'is_group', 'createdAt', 'lastMessageAt', 'participants']


class ConversationCreateSerializer(serializers.Serializer):
  """
  创建会话序列化器
  - participants: 参与者用户 ID 列表（必须包含至少 1 个除自己的用户）
  - title: 可选，会话标题（群聊使用）
  """
  participantIds = serializers.ListField(
    child=serializers.IntegerField(), allow_empty=False
  )
  title = serializers.CharField(required=False, allow_blank=True, max_length=200)

  def validate_participantIds(self, value):
    request = self.context['request']
    user_ids = set(value)
    # 移除自己，后续会自动加入
    user_ids.discard(request.user.id)
    if not user_ids:
      raise serializers.ValidationError('会话至少需要包含一个其他用户')

    users = list(User.objects.filter(id__in=user_ids, is_active=True))
    if len(users) != len(user_ids):
      raise serializers.ValidationError('部分参与者不存在或已被禁用')

    self._participants = users
    return value

  def create(self, validated_data):
    request = self.context['request']
    title = validated_data.get('title', '').strip()
    participants = getattr(self, '_participants', [])

    is_group = len(participants) > 1
    if not title and is_group:
      # 默认群聊标题：取前两个用户显示名
      names = [u.display_name for u in participants[:2]]
      more = ' 等' if len(participants) > 2 else ''
      title = '、'.join(names) + more

    conversation = Conversation.objects.create(
      title=title,
      is_group=is_group,
      created_by=request.user,
    )

    # 创建参与者记录（包括自己）
    ConversationParticipant.objects.bulk_create(
      [
        ConversationParticipant(conversation=conversation, user=request.user),
        *[ConversationParticipant(conversation=conversation, user=u) for u in participants],
      ]
    )

    return conversation

