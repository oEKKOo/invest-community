from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Conversation(models.Model):
    """
    私信会话
    - 支持 2 人或多人会话
    - 通过 ConversationParticipant 维护参与者列表
    """
    title = models.CharField('会话标题', max_length=200, blank=True)
    is_group = models.BooleanField('是否群聊', default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_conversations',
        verbose_name='创建者',
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    last_message_at = models.DateTimeField('最后消息时间', null=True, blank=True)

    class Meta:
        db_table = 'message_conversation'
        verbose_name = '私信会话'
        verbose_name_plural = '私信会话'
        ordering = ['-last_message_at', '-created_at']

    def __str__(self):
        return self.title or f'会话 {self.pk}'


class ConversationParticipant(models.Model):
    """会话参与者"""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='会话',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name='用户',
    )
    joined_at = models.DateTimeField('加入时间', default=timezone.now)

    class Meta:
        db_table = 'message_conversation_participant'
        verbose_name = '会话参与者'
        verbose_name_plural = '会话参与者'
        unique_together = ['conversation', 'user']

    def __str__(self):
        return f'{self.user.username} in {self.conversation_id}'


class Message(models.Model):
    """会话中的具体消息"""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='会话',
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='发送者',
    )
    content = models.TextField('内容')
    is_deleted = models.BooleanField('是否已删除', default=False)
    created_at = models.DateTimeField('发送时间', default=timezone.now)

    class Meta:
        db_table = 'message'
        verbose_name = '私信消息'
        verbose_name_plural = '私信消息'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f'{self.sender.username}: {self.content[:20]}'


class MessageReadLog(models.Model):
    """
    消息阅读记录
    - 一条消息对每个用户仅记录一条已读日志
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_logs',
        verbose_name='消息',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_reads',
        verbose_name='用户',
    )
    read_at = models.DateTimeField('阅读时间', default=timezone.now)

    class Meta:
        db_table = 'message_read_log'
        verbose_name = '消息阅读记录'
        verbose_name_plural = '消息阅读记录'
        unique_together = ['message', 'user']

    def __str__(self):
        return f'{self.user.username} read {self.message_id}'

