from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify

User = get_user_model()


class Group(models.Model):
    VISIBILITY_CHOICES = [
        ('PUBLIC', '公开'),
        ('PRIVATE', '私密'),
        ('APPROVAL', '审核加入'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', '活跃'),
        ('DISSOLVED', '已解散'),
    ]

    name = models.CharField('群组名称', max_length=100)
    slug = models.SlugField('唯一标识', max_length=140, unique=True)
    description = models.TextField('群简介', blank=True)
    avatar_url = models.URLField('头像链接', blank=True)
    tags_json = models.JSONField('标签', default=list, blank=True)
    topic_direction = models.CharField('主题方向', max_length=120, blank=True)
    visibility = models.CharField('可见性', max_length=20, choices=VISIBILITY_CHOICES, default='PUBLIC')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_groups', verbose_name='群主'
    )

    member_count = models.PositiveIntegerField('成员数', default=1)
    post_count = models.PositiveIntegerField('讨论数', default=0)
    file_count = models.PositiveIntegerField('资料数', default=0)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'groups'
        verbose_name = '群组'
        verbose_name_plural = '群组'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['visibility', 'status', '-created_at']),
            models.Index(fields=['owner', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or f'group-{int(timezone.now().timestamp())}'
            self.slug = base_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    ROLE_CHOICES = [
        ('OWNER', '群主'),
        ('ADMIN', '管理员'),
        ('MEMBER', '普通成员'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', '在群'),
        ('LEFT', '已退出'),
        ('REMOVED', '被移除'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members', verbose_name='群组')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships', verbose_name='用户')
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    joined_at = models.DateTimeField('加入时间', default=timezone.now)
    left_at = models.DateTimeField('离开时间', null=True, blank=True)

    class Meta:
        db_table = 'group_members'
        verbose_name = '群成员'
        verbose_name_plural = '群成员'
        unique_together = ['group', 'user']
        indexes = [
            models.Index(fields=['group', 'role', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.user_id}@{self.group_id}:{self.role}'


class GroupJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', '待审核'),
        ('APPROVED', '已通过'),
        ('REJECTED', '已拒绝'),
        ('CANCELLED', '已取消'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests', verbose_name='群组')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_join_requests', verbose_name='申请人')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    message = models.CharField('申请说明', max_length=300, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='reviewed_group_join_requests',
        null=True,
        blank=True,
        verbose_name='审核人',
    )
    review_note = models.CharField('审核备注', max_length=300, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    reviewed_at = models.DateTimeField('审核时间', null=True, blank=True)

    class Meta:
        db_table = 'group_join_requests'
        verbose_name = '入群申请'
        verbose_name_plural = '入群申请'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'status', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]


class GroupReviewer(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='reviewers', verbose_name='群组')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_reviewer_roles', verbose_name='审核人')
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'group_reviewers'
        verbose_name = '群审核人'
        verbose_name_plural = '群审核人'
        unique_together = ['group', 'user']
        indexes = [
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'reviewer:{self.user_id}@{self.group_id}'


class GroupInvite(models.Model):
    STATUS_CHOICES = [
        ('PENDING', '待处理'),
        ('ACCEPTED', '已接受'),
        ('REJECTED', '已拒绝'),
        ('CANCELLED', '已取消'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invites', verbose_name='群组')
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_group_invites', verbose_name='邀请人')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_group_invites', verbose_name='被邀请人')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    message = models.CharField('邀请说明', max_length=300, blank=True)
    responded_at = models.DateTimeField('响应时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'group_invites'
        verbose_name = '群邀请'
        verbose_name_plural = '群邀请'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'status', '-created_at']),
            models.Index(fields=['invitee', 'status', '-created_at']),
        ]

    def __str__(self):
        return f'invite:{self.inviter_id}->{self.invitee_id}@{self.group_id}:{self.status}'


class GroupPost(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('NORMAL', '普通讨论'),
        ('LONGFORM', '长文分析'),
        ('POLL', '投票'),
    ]
    STATUS_CHOICES = [
        ('PUBLISHED', '已发布'),
        ('DELETED', '已删除'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts', verbose_name='群组')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_posts', verbose_name='作者')
    title = models.CharField('标题', max_length=200)
    body = models.TextField('正文')
    content_type = models.CharField('内容类型', max_length=20, choices=CONTENT_TYPE_CHOICES, default='NORMAL')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='PUBLISHED')
    like_count = models.PositiveIntegerField('点赞数', default=0)
    comment_count = models.PositiveIntegerField('评论数', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'group_posts'
        verbose_name = '群讨论'
        verbose_name_plural = '群讨论'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'status', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]


class GroupFile(models.Model):
    VISIBILITY_CHOICES = [('GROUP_ONLY', '仅群内')]
    STATUS_CHOICES = [
        ('ACTIVE', '正常'),
        ('DELETED', '已删除'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='files', verbose_name='群组')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_files', verbose_name='上传者')
    file = models.FileField('文件', upload_to='group_files/%Y/%m/')
    original_name = models.CharField('原始文件名', max_length=255, blank=True)
    mime_type = models.CharField('文件类型', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('文件大小', default=0)
    visibility = models.CharField('可见性', max_length=20, choices=VISIBILITY_CHOICES, default='GROUP_ONLY')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'group_files'
        verbose_name = '群资料'
        verbose_name_plural = '群资料'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', '-created_at']),
            models.Index(fields=['uploaded_by', '-created_at']),
        ]
