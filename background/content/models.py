from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Asset(models.Model):
    """
    资产标的表（股票、基金、ETF等）
    遵循"真实 code 贯穿全系统"原则：
    - code + market：用户展示/输入层（稳定不变）
    - finnhub_symbol：第三方 API 调用层（允许变更，单独存储）
    - asset_id：业务层引用（content/comment/portfolio 等表关联键）
    """
    ASSET_TYPE_CHOICES = [
        ('STOCK', '股票'),
        ('FUND', '基金'),
        ('ETF', 'ETF'),
        ('BOND', '债券'),
    ]

    MARKET_CHOICES = [
        ('SH', '上交所'),
        ('SZ', '深交所'),
        ('BJ', '北交所'),
        ('HK', '港交所'),
        ('US', '美股'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', '正常交易'),
        ('SUSPENDED', '停牌'),
        ('DELISTED', '退市'),
    ]

    code = models.CharField('资产代码', max_length=20)
    name = models.CharField('资产名称', max_length=100)
    asset_type = models.CharField('资产类型', max_length=20, choices=ASSET_TYPE_CHOICES)
    market = models.CharField('所属市场', max_length=20, blank=True, choices=MARKET_CHOICES)
    status = models.CharField('交易状态', max_length=16, choices=STATUS_CHOICES, default='ACTIVE')

    # ---- Finnhub 接入专用字段 ----
    # 规则：内部标识（code+market）稳定，供应商 symbol 可变
    finnhub_symbol = models.CharField(
        'Finnhub Symbol', max_length=32, null=True, blank=True, unique=True,
        help_text='调用 Finnhub API 使用的唯一标识，如 AAPL / 0700.HK'
    )
    exchange = models.CharField(
        '交易所（供应商侧）', max_length=32, blank=True,
        help_text='Finnhub 返回的 exchange 字段，用于 symbols 导入筛选'
    )
    currency = models.CharField('币种', max_length=8, blank=True, help_text='如 CNY/USD/HKD')
    isin = models.CharField('ISIN编码', max_length=20, blank=True)
    industry = models.CharField('所属行业', max_length=64, blank=True)
    logo_url = models.URLField('Logo URL', blank=True)
    description = models.TextField('公司简介', blank=True)
    meta_json = models.JSONField('扩展信息', default=dict, blank=True,
                                 help_text='存放官网、行业详情等扩展字段')
    last_sync_at = models.DateTimeField('基础信息同步时间', null=True, blank=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'asset'
        verbose_name = '资产标的'
        verbose_name_plural = '资产标的'
        # 同类型同代码同市场唯一（防止重复导入）
        unique_together = [('asset_type', 'code', 'market')]
        indexes = [
            models.Index(fields=['code'], name='idx_asset_code'),
            models.Index(fields=['asset_type'], name='idx_asset_type'),
            models.Index(fields=['market'], name='idx_asset_market'),
            models.Index(fields=['exchange'], name='idx_asset_exchange'),
            models.Index(fields=['status'], name='idx_asset_status'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.market})"

    @property
    def display_market(self):
        """返回可读的市场名称"""
        market_map = {
            'SH': 'A股·上交所', 'SZ': 'A股·深交所', 'BJ': 'A股·北交所',
            'HK': '港股', 'US': '美股'
        }
        return market_map.get(self.market, self.market)


class Content(models.Model):
    """内容表（帖子、文章）"""
    STATUS_CHOICES = [
        ('DRAFT', '草稿'),
        ('PENDING_REVIEW', '待审核'),
        ('PUBLISHED', '已发布'),
        ('REJECTED', '被驳回'),
        ('TAKEN_DOWN', '下架'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者', related_name='contents')
    title = models.CharField('标题', max_length=200)
    body = models.TextField('正文')
    tags_json = models.JSONField('标签', default=list, blank=True)
    
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    verbose_name='审核人', related_name='reviewed_contents')
    reject_reason = models.TextField('驳回原因', blank=True)
    
    like_count = models.PositiveIntegerField('点赞数', default=0)
    comment_count = models.PositiveIntegerField('评论数', default=0)
    view_count = models.PositiveIntegerField('浏览数', default=0)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    published_at = models.DateTimeField('发布时间', null=True, blank=True)

    # 关联资产
    assets = models.ManyToManyField(Asset, through='ContentAsset', verbose_name='关联资产')

    class Meta:
        db_table = 'content'
        verbose_name = '内容'
        verbose_name_plural = '内容'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['-published_at']),
        ]

    def __str__(self):
        return self.title


class ContentAsset(models.Model):
    """内容-资产关联表"""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, verbose_name='内容')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name='资产')
    
    created_at = models.DateTimeField('关联时间', default=timezone.now)

    class Meta:
        db_table = 'content_asset'
        verbose_name = '内容资产关联'
        verbose_name_plural = '内容资产关联'
        unique_together = ['content', 'asset']

    def __str__(self):
        return f"{self.content.title} - {self.asset.code}"


class Comment(models.Model):
    """评论表"""
    STATUS_CHOICES = [
        ('NORMAL', '正常'),
        ('HIDDEN', '屏蔽'),
        ('DELETED', '删除'),
    ]

    content = models.ForeignKey(Content, on_delete=models.CASCADE, verbose_name='所属内容', related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='评论者', related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              verbose_name='父评论', related_name='replies')
    reply_to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='回复用户', related_name='received_replies')
    
    body = models.TextField('评论内容')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='NORMAL')
    
    like_count = models.PositiveIntegerField('点赞数', default=0)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'comment'
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['content', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]

    def __str__(self):
        return f"{self.author.username}的评论"


class Like(models.Model):
    """点赞表（统一点赞：帖子、评论、组合）"""
    TARGET_TYPE_CHOICES = [
        ('POST', '帖子'),
        ('COMMENT', '评论'),
        ('PORTFOLIO', '组合'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', related_name='likes')
    target_type = models.CharField('目标类型', max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.PositiveIntegerField('目标ID')
    
    created_at = models.DateTimeField('点赞时间', default=timezone.now)

    class Meta:
        db_table = 'like'
        verbose_name = '点赞'
        verbose_name_plural = '点赞'
        unique_together = ['user', 'target_type', 'target_id']
        indexes = [
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['user', 'target_type']),
        ]

    def __str__(self):
        return f"{self.user.username}点赞了{self.target_type}#{self.target_id}"


class Favorite(models.Model):
    """收藏表"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', related_name='favorites')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, verbose_name='内容', related_name='favorites')
    
    created_at = models.DateTimeField('收藏时间', default=timezone.now)

    class Meta:
        db_table = 'favorite'
        verbose_name = '收藏'
        verbose_name_plural = '收藏'
        unique_together = ['user', 'content']

    def __str__(self):
        return f"{self.user.username}收藏了{self.content.title}"