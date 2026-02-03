from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Report(models.Model):
    """举报表"""
    TARGET_TYPE_CHOICES = [
        ('POST', '帖子'),
        ('COMMENT', '评论'),
        ('USER', '用户'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '待处理'),
        ('RESOLVED', '已处理'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='举报人', related_name='reports_made')
    target_type = models.CharField('举报目标类型', max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.PositiveIntegerField('举报目标ID')
    
    reason = models.TextField('举报原因')
    status = models.CharField('处理状态', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # 处理信息
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name='处理人', related_name='reports_handled')
    handle_result = models.TextField('处理结果', blank=True)
    handle_time = models.DateTimeField('处理时间', null=True, blank=True)
    
    created_at = models.DateTimeField('举报时间', default=timezone.now)

    class Meta:
        db_table = 'report'
        verbose_name = '举报'
        verbose_name_plural = '举报'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        return f"{self.reporter.username} 举报 {self.target_type}#{self.target_id}"


class Alert(models.Model):
    """风控告警表（扩展功能）"""
    ALERT_TYPE_CHOICES = [
        ('CONTENT_RISK', '内容风险'),
        ('USER_BEHAVIOR', '用户行为'),
        ('SYSTEM', '系统异常'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', '待处理'),
        ('RESOLVED', '已处理'),
        ('IGNORED', '已忽略'),
    ]

    alert_type = models.CharField('告警类型', max_length=50, choices=ALERT_TYPE_CHOICES)
    title = models.CharField('告警标题', max_length=200)
    description = models.TextField('告警描述')
    
    # 相关对象
    related_object_type = models.CharField('关联对象类型', max_length=50, blank=True)
    related_object_id = models.PositiveIntegerField('关联对象ID', null=True, blank=True)
    
    severity = models.CharField('严重程度', max_length=20, default='MEDIUM')
    status = models.CharField('处理状态', max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # 处理信息
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name='处理人', related_name='alerts_handled')
    handle_result = models.TextField('处理结果', blank=True)
    handle_time = models.DateTimeField('处理时间', null=True, blank=True)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'alert'
        verbose_name = '风控告警'
        verbose_name_plural = '风控告警'
        ordering = ['-created_at']

    def __str__(self):
        return self.title