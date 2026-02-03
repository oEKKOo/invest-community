from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Notification(models.Model):
    """通知表"""
    TYPE_CHOICES = [
        ('LIKE', '点赞通知'),
        ('COMMENT', '评论通知'),
        ('FOLLOW', '关注通知'),
        ('REVIEW_RESULT', '审核结果通知'),
        ('SYSTEM', '系统通知'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='接收用户', related_name='notifications')
    notification_type = models.CharField('通知类型', max_length=20, choices=TYPE_CHOICES)
    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    
    # 关联对象信息
    related_object_type = models.CharField('关联对象类型', max_length=50, blank=True)
    related_object_id = models.PositiveIntegerField('关联对象ID', null=True, blank=True)
    
    is_read = models.BooleanField('是否已读', default=False)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    read_at = models.DateTimeField('阅读时间', null=True, blank=True)

    class Meta:
        db_table = 'notification'
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"