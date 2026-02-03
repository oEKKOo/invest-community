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

    username = models.CharField('用户名', max_length=150, unique=True)
    email = models.EmailField('邮箱', unique=True)
    phone = models.CharField('手机号', max_length=20, blank=True, null=True)
    display_name = models.CharField('显示昵称', max_length=100)
    avatar_url = models.URLField('头像链接', blank=True, null=True)
    bio = models.TextField('个人简介', blank=True)
    
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='USER')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='NORMAL')
    
    followers_count = models.PositiveIntegerField('粉丝数', default=0)
    following_count = models.PositiveIntegerField('关注数', default=0)
    
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