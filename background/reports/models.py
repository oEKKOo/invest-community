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
        ('PORTFOLIO', '组合'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '待处理'),
        ('RESOLVED', '已处理'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='举报人', related_name='reports_made')
    target_type = models.CharField('举报目标类型', max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.PositiveIntegerField('举报目标ID')
    
    reason = models.TextField('举报原因')
    report_type_detail = models.CharField('举报类型细分', max_length=100, blank=True)
    evidence_json = models.JSONField('证据内容（截图、链接等）', default=dict, blank=True)
    priority = models.IntegerField('优先级', default=0)
    status = models.CharField('处理状态', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # 处理信息
    result = models.CharField('处理结果类型', max_length=20, blank=True)
    action_taken = models.CharField('处置动作', max_length=32, blank=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name='处理人', related_name='reports_handled')
    handle_result = models.TextField('处理结果', blank=True)
    handle_time = models.DateTimeField('处理时间', null=True, blank=True)
    linked_queue_item = models.ForeignKey(
        'ModerationQueueItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_reports',
        verbose_name='关联审核队列项'
    )
    
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


class ModerationRule(models.Model):
    """审核规则配置"""
    RULE_TYPE_CHOICES = [
        ('SENSITIVE_WORD', '敏感词'),
        ('COMPLIANCE_POLICY', '合规规则'),
        ('REPETITION', '重复检测'),
    ]
    ACTION_CHOICES = [
        ('ALLOW', '放行'),
        ('REVIEW', '转人工审核'),
        ('REJECT', '自动驳回'),
    ]
    LEVEL_CHOICES = [
        ('LOW', '低风险'),
        ('MEDIUM', '中风险'),
        ('HIGH', '高风险'),
    ]

    name = models.CharField('规则名称', max_length=120, unique=True)
    rule_type = models.CharField('规则类型', max_length=32, choices=RULE_TYPE_CHOICES)
    pattern = models.CharField('匹配模式', max_length=255, blank=True)
    config_json = models.JSONField('规则配置', default=dict, blank=True)
    risk_level = models.CharField('风险等级', max_length=16, choices=LEVEL_CHOICES, default='LOW')
    risk_score = models.PositiveIntegerField('风险分', default=10)
    action = models.CharField('命中动作', max_length=16, choices=ACTION_CHOICES, default='REVIEW')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'moderation_rule'
        verbose_name = '审核规则'
        verbose_name_plural = '审核规则'
        ordering = ['rule_type', 'id']
        indexes = [
            models.Index(fields=['is_active', 'rule_type'], name='idx_mrule_active_type'),
        ]

    def __str__(self):
        return self.name


class ModerationQueueItem(models.Model):
    """可疑内容审核队列"""
    STATUS_CHOICES = [
        ('PENDING', '待处理'),
        ('RESOLVED', '已处理'),
    ]
    SOURCE_CHOICES = [
        ('AUTO', '自动规则'),
        ('REPORT', '举报触发'),
        ('MANUAL', '人工添加'),
    ]
    RISK_LEVEL_CHOICES = [
        ('LOW', '低风险'),
        ('MEDIUM', '中风险'),
        ('HIGH', '高风险'),
    ]

    content = models.ForeignKey(
        'content.Content',
        on_delete=models.CASCADE,
        related_name='moderation_queue_items',
        verbose_name='内容'
    )
    source = models.CharField('来源', max_length=16, choices=SOURCE_CHOICES, default='AUTO')
    risk_level = models.CharField('风险等级', max_length=16, choices=RISK_LEVEL_CHOICES, default='LOW')
    risk_score = models.PositiveIntegerField('风险分', default=0)
    reason_summary = models.CharField('原因摘要', max_length=255, blank=True)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='PENDING')
    decided_status = models.CharField('最终状态', max_length=20, blank=True)
    decided_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='decided_moderation_queue_items',
        verbose_name='处理人'
    )
    decided_at = models.DateTimeField('处理时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'moderation_queue_item'
        verbose_name = '审核队列项'
        verbose_name_plural = '审核队列项'
        ordering = ['-risk_score', '-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='idx_mqueue_status_time'),
            models.Index(fields=['source', 'status'], name='idx_mqueue_source_status'),
            models.Index(fields=['risk_level', '-risk_score'], name='idx_mqueue_risk_score'),
        ]

    def __str__(self):
        return f"{self.content_id} {self.risk_level} {self.status}"


class ModerationHit(models.Model):
    """规则命中日志"""
    rule = models.ForeignKey(ModerationRule, on_delete=models.SET_NULL, null=True, blank=True, related_name='hits')
    content = models.ForeignKey('content.Content', on_delete=models.CASCADE, related_name='moderation_hits')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_hits')
    hit_text = models.CharField('命中文本', max_length=255, blank=True)
    evidence_json = models.JSONField('命中证据', default=dict, blank=True)
    risk_score = models.PositiveIntegerField('风险分', default=0)
    risk_level = models.CharField('风险等级', max_length=16, default='LOW')
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'moderation_hit'
        verbose_name = '审核命中记录'
        verbose_name_plural = '审核命中记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content', '-created_at'], name='idx_mhit_content_time'),
            models.Index(fields=['user', '-created_at'], name='idx_mhit_user_time'),
        ]

    def __str__(self):
        return f"{self.content_id} {self.risk_level} {self.risk_score}"


class CommunityMetricDaily(models.Model):
    """社区日指标"""
    stat_date = models.DateField('统计日期', unique=True)
    dau = models.PositiveIntegerField('日活', default=0)
    post_count = models.PositiveIntegerField('发帖数', default=0)
    comment_count = models.PositiveIntegerField('评论数', default=0)
    report_count = models.PositiveIntegerField('举报数', default=0)
    review_pass_rate = models.DecimalField('审核通过率', max_digits=5, decimal_places=2, default=0)
    taken_down_count = models.PositiveIntegerField('下架数', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'community_metric_daily'
        verbose_name = '社区日指标'
        verbose_name_plural = '社区日指标'
        ordering = ['-stat_date']


class TopicMetricDaily(models.Model):
    """话题日指标"""
    stat_date = models.DateField('统计日期')
    topic = models.CharField('话题', max_length=64)
    post_count = models.PositiveIntegerField('帖子数', default=0)
    comment_count = models.PositiveIntegerField('评论数', default=0)
    like_count = models.PositiveIntegerField('点赞数', default=0)
    heat_score = models.DecimalField('热度分', max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'topic_metric_daily'
        verbose_name = '话题日指标'
        verbose_name_plural = '话题日指标'
        unique_together = ['stat_date', 'topic']
        ordering = ['-stat_date', '-heat_score']
        indexes = [
            models.Index(fields=['stat_date', '-heat_score'], name='idx_tmetric_date_heat'),
            models.Index(fields=['topic', '-stat_date'], name='idx_tmetric_topic_date'),
        ]