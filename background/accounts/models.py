from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        """创建并保存一个普通用户"""
        if not username:
            raise ValueError('用户名是必需的')
        if not email:
            raise ValueError('邮箱是必需的')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """创建并保存一个超级用户"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置is_superuser=True')

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """用户模型"""
    ROLE_CHOICES = [
        ('USER', '普通用户'),
        ('MODERATOR', '管理员'),
        ('ADMIN', '超级管理员'),
    ]
    
    STATUS_CHOICES = [
        ('NORMAL', '正常'),
        ('MUTED', '禁言'),
        ('BANNED', '封禁'),
    ]

    IDENTITY_LEVEL_CHOICES = [
        ('UNVERIFIED', '未认证'),
        ('BASIC', '基础认证'),
        ('REAL_NAME', '实名认证'),
        ('PROFESSIONAL', '专业认证'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('NONE', '未提交'),
        ('PENDING', '待审核'),
        ('APPROVED', '已通过'),
        ('REJECTED', '已驳回'),
    ]

    RISK_LEVEL_CHOICES = [
        ('R1', '保守型'),
        ('R2', '稳健型'),
        ('R3', '平衡型'),
        ('R4', '积极型'),
        ('R5', '激进型'),
    ]

    username = models.CharField('用户名', max_length=150, unique=True)
    email = models.EmailField('邮箱', unique=True)
    phone = models.CharField('手机号', max_length=20, blank=True, null=True)
    display_name = models.CharField('显示昵称', max_length=100)
    avatar_url = models.URLField('头像链接', blank=True, null=True)
    bio = models.TextField('个人简介', blank=True)
    investment_experience = models.CharField('投资经验标签', max_length=32, blank=True, default='')
    
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='USER')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='NORMAL')
    
    followers_count = models.PositiveIntegerField('粉丝数', default=0)
    following_count = models.PositiveIntegerField('关注数', default=0)

    # 治理相关字段：禁言截止时间（仅限制发帖/评论），封禁走 status=BANNED + is_active=False
    mute_until = models.DateTimeField('禁言截止时间', null=True, blank=True)

    # 分级认证体系
    phone_verified = models.BooleanField('手机号已验证', default=False)
    email_verified = models.BooleanField('邮箱已验证', default=False)
    identity_level = models.CharField(
        '认证等级', max_length=20, choices=IDENTITY_LEVEL_CHOICES, default='UNVERIFIED'
    )
    real_name_status = models.CharField(
        '实名认证状态', max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='NONE'
    )
    professional_status = models.CharField(
        '专业认证状态', max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='NONE'
    )
    risk_assessment_status = models.CharField(
        '风险评估状态', max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='NONE'
    )
    risk_level = models.CharField(
        '风险等级', max_length=8, choices=RISK_LEVEL_CHOICES, blank=True, null=True
    )
    v_badge = models.BooleanField('加V标识', default=False)

    is_active = models.BooleanField('激活状态', default=True)
    is_staff = models.BooleanField('员工状态', default=False)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username


class UserInvestProfile(models.Model):
    """用户投资偏好表"""
    RISK_LEVEL_CHOICES = [
        (1, '低风险'),
        (2, '中风险'),
        (3, '高风险'),
    ]
    
    HORIZON_CHOICES = [
        (1, '短期'),
        (2, '中期'),
        (3, '长期'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户', related_name='invest_profile')
    risk_level = models.IntegerField('风险等级', choices=RISK_LEVEL_CHOICES, default=2)
    horizon = models.IntegerField('投资期限', choices=HORIZON_CHOICES, default=2)
    focus_market = models.JSONField('关注市场', default=list, blank=True)  # ["A", "US"]
    preferred_assets = models.JSONField('偏好资产', default=list, blank=True)  # ["stock", "etf"]
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_invest_profile'
        verbose_name = '用户投资偏好'
        verbose_name_plural = '用户投资偏好'

    def __str__(self):
        return f"{self.user.username}的投资偏好"


class UserFollow(models.Model):
    """用户关注关系表"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='关注者', related_name='following_set')
    followee = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='被关注者', related_name='followers_set')
    
    created_at = models.DateTimeField('关注时间', default=timezone.now)

    class Meta:
        db_table = 'user_follow'
        verbose_name = '用户关注'
        verbose_name_plural = '用户关注'
        unique_together = ['follower', 'followee']

    def __str__(self):
        return f"{self.follower.username} 关注 {self.followee.username}"


class UserPrivacySettings(models.Model):
    """用户隐私设置"""
    PROFILE_VISIBILITY_CHOICES = [
        ('PUBLIC', '公开'),
        ('FOLLOWERS', '仅关注者可见'),
        ('PRIVATE', '仅自己可见'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='privacy_settings', verbose_name='用户'
    )
    profile_visibility = models.CharField(
        '主页可见性', max_length=16, choices=PROFILE_VISIBILITY_CHOICES, default='PUBLIC'
    )
    show_invest_profile = models.BooleanField('展示投资偏好', default=True)
    allow_search = models.BooleanField('允许被搜索', default=True)
    show_email = models.BooleanField('展示邮箱', default=False)
    show_phone = models.BooleanField('展示手机号', default=False)
    allow_stranger_dm = models.BooleanField('允许陌生人私信', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_privacy_settings'
        verbose_name = '用户隐私设置'
        verbose_name_plural = '用户隐私设置'

    def __str__(self):
        return f"{self.user.username} 隐私设置"


class UserModerationLog(models.Model):
    """
    用户治理操作日志
    记录禁言/解禁/封禁/解封等关键动作，用于“社区治理留痕”
    """
    ACTION_CHOICES = [
        ('MUTE', '禁言'),
        ('UNMUTE', '解除禁言'),
        ('BAN', '封禁'),
        ('UNBAN', '解除封禁'),
        ('STATUS_CHANGE', '状态变更'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderation_logs', verbose_name='被处理用户')
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_actions',
        verbose_name='操作人',
    )
    action = models.CharField('动作类型', max_length=32, choices=ACTION_CHOICES)
    reason = models.TextField('原因说明', blank=True)
    expire_at = models.DateTimeField('到期时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'user_moderation_log'
        verbose_name = '用户治理日志'
        verbose_name_plural = '用户治理日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.action} @ {self.created_at}"


class UserSocialAccount(models.Model):
    """第三方账号绑定表（微信/微博）"""
    PROVIDER_CHOICES = [
        ('WECHAT', '微信'),
        ('WEIBO', '微博'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts', verbose_name='用户')
    provider = models.CharField('平台', max_length=20, choices=PROVIDER_CHOICES)
    provider_uid = models.CharField('平台用户ID', max_length=128)
    unionid = models.CharField('UnionID', max_length=128, blank=True, null=True)
    openid = models.CharField('OpenID', max_length=128, blank=True, null=True)
    access_token = models.TextField('访问令牌', blank=True)
    refresh_token = models.TextField('刷新令牌', blank=True)
    expires_at = models.DateTimeField('过期时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_social_account'
        verbose_name = '第三方账号绑定'
        verbose_name_plural = '第三方账号绑定'
        unique_together = ['provider', 'provider_uid']

    def __str__(self):
        return f"{self.user.username} {self.provider}:{self.provider_uid}"


class UserVerificationCode(models.Model):
    """验证码记录"""
    CHANNEL_CHOICES = [
        ('EMAIL', '邮箱'),
        ('PHONE', '手机'),
    ]
    PURPOSE_CHOICES = [
        ('REGISTER', '注册'),
        ('LOGIN', '登录'),
        ('PASSWORD_RESET', '找回密码'),
        ('VERIFY_CONTACT', '验证联系方式'),
    ]
    STATUS_CHOICES = [
        ('SENT', '已发送'),
        ('VERIFIED', '已验证'),
        ('EXPIRED', '已过期'),
        ('INVALID', '已作废'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='verification_codes',
        verbose_name='用户', null=True, blank=True
    )
    channel = models.CharField('渠道', max_length=16, choices=CHANNEL_CHOICES)
    target = models.CharField('目标地址', max_length=255)
    purpose = models.CharField('用途', max_length=32, choices=PURPOSE_CHOICES)
    code = models.CharField('验证码', max_length=16)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='SENT')
    expires_at = models.DateTimeField('过期时间')
    verified_at = models.DateTimeField('验证时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'user_verification_code'
        verbose_name = '验证码'
        verbose_name_plural = '验证码'
        indexes = [
            models.Index(fields=['target', 'purpose', 'created_at']),
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.target} {self.purpose} {self.status}"


class UserRealNameVerification(models.Model):
    """实名认证申请"""
    STATUS_CHOICES = [
        ('PENDING', '待审核'),
        ('APPROVED', '已通过'),
        ('REJECTED', '已驳回'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='real_name_verifications', verbose_name='用户')
    real_name = models.CharField('真实姓名', max_length=100)
    id_card_no_masked = models.CharField('身份证号(脱敏)', max_length=32)
    id_card_hash = models.CharField('身份证号哈希', max_length=128)
    face_score = models.DecimalField('人脸分数', max_digits=5, decimal_places=2, null=True, blank=True)
    ocr_passed = models.BooleanField('OCR通过', default=False)
    liveness_passed = models.BooleanField('活体通过', default=False)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='PENDING')
    reject_reason = models.TextField('驳回原因', blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='reviewed_real_name_records',
        null=True, blank=True, verbose_name='审核人'
    )
    reviewed_at = models.DateTimeField('审核时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_real_name_verification'
        verbose_name = '实名认证'
        verbose_name_plural = '实名认证'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} {self.status}"


class UserProfessionalVerification(models.Model):
    """专业认证申请"""
    STATUS_CHOICES = [
        ('PENDING', '待审核'),
        ('APPROVED', '已通过'),
        ('REJECTED', '已驳回'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='professional_verifications', verbose_name='用户')
    qualification_doc_url = models.URLField('从业资格证明', blank=True)
    education_doc_url = models.URLField('学历证明', blank=True)
    additional_doc_url = models.URLField('附加材料', blank=True)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='PENDING')
    reject_reason = models.TextField('驳回原因', blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='reviewed_professional_records',
        null=True, blank=True, verbose_name='审核人'
    )
    reviewed_at = models.DateTimeField('审核时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_professional_verification'
        verbose_name = '专业认证'
        verbose_name_plural = '专业认证'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} {self.status}"


class RiskQuestionnaireTemplate(models.Model):
    """风险问卷模板"""
    version = models.CharField('版本号', max_length=32, unique=True)
    title = models.CharField('标题', max_length=120)
    description = models.TextField('说明', blank=True)
    questions = models.JSONField('题目JSON', default=list)
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'risk_questionnaire_template'
        verbose_name = '风险问卷模板'
        verbose_name_plural = '风险问卷模板'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.version} {self.title}"


class RiskQuestionnaireSubmission(models.Model):
    """用户风险问卷提交记录"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risk_submissions', verbose_name='用户')
    template = models.ForeignKey(
        RiskQuestionnaireTemplate, on_delete=models.PROTECT, related_name='submissions', verbose_name='模板'
    )
    answers = models.JSONField('答案JSON', default=dict)
    score = models.IntegerField('总分', default=0)
    risk_level = models.CharField('风险等级', max_length=8, choices=User.RISK_LEVEL_CHOICES)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'risk_questionnaire_submission'
        verbose_name = '风险问卷提交'
        verbose_name_plural = '风险问卷提交'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f"{self.user.username} {self.risk_level} {self.score}"