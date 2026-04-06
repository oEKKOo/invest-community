from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

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


class Board(models.Model):
    """社区板块（支持三级层级）"""

    BOARD_TYPE_CHOICES = [
        ('MARKET', '市场讨论区'),
        ('THEME', '主题专区'),
        ('COMPANY_RESEARCH', '公司研究专区'),
        ('QA', '问答求助区'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', '启用'),
        ('INACTIVE', '停用'),
    ]

    MARKET_CHOICES = [
        ('A_SHARE', 'A股'),
        ('HK_STOCK', '港股'),
        ('US_STOCK', '美股'),
        ('FUTURES', '期货'),
    ]

    name = models.CharField('板块名称', max_length=100)
    slug = models.SlugField('唯一标识', max_length=120, unique=True)
    board_type = models.CharField('板块类型', max_length=32, choices=BOARD_TYPE_CHOICES)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='父板块'
    )
    description = models.TextField('描述', blank=True)
    icon = models.CharField('图标', max_length=100, blank=True)
    sort_order = models.PositiveIntegerField('排序', default=0)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='ACTIVE')
    is_builtin = models.BooleanField('系统预置', default=False)

    # 扩展字段（用于公司研究专区等扩展场景）
    market = models.CharField('市场维度', max_length=20, blank=True, choices=MARKET_CHOICES)
    industry_code = models.CharField('行业编码', max_length=32, blank=True)
    stock_code = models.CharField('个股代码', max_length=20, blank=True)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'board'
        verbose_name = '板块'
        verbose_name_plural = '板块'
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['board_type', 'status'], name='idx_board_type_status'),
            models.Index(fields=['parent', 'sort_order'], name='idx_board_parent_sort'),
            models.Index(fields=['status', 'sort_order'], name='idx_board_status_sort'),
        ]

    def __str__(self):
        return self.name

    @property
    def level(self):
        level = 1
        node = self.parent
        while node:
            level += 1
            node = node.parent
        return level

    def clean(self):
        if self.parent_id and self.parent_id == self.id:
            raise ValidationError('板块不能将自己设置为父节点')

        if self.parent and self.parent.parent and self.parent.parent.parent:
            raise ValidationError('板块层级最多支持三级')


class Content(models.Model):
    """内容表（帖子、文章）"""
    STATUS_CHOICES = [
        ('DRAFT', '草稿'),
        ('PENDING_REVIEW', '待审核'),
        ('PUBLISHED', '已发布'),
        ('REJECTED', '被驳回'),
        ('TAKEN_DOWN', '下架'),
    ]
    RISK_LEVEL_CHOICES = [
        ('LOW', '低风险'),
        ('MEDIUM', '中风险'),
        ('HIGH', '高风险'),
    ]
    MODERATION_SOURCE_CHOICES = [
        ('MANUAL', '人工'),
        ('AUTO', '自动规则'),
        ('REPORT', '举报触发'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者', related_name='contents')
    title = models.CharField('标题', max_length=200)
    body = models.TextField('正文')
    tags_json = models.JSONField('标签', default=list, blank=True)
    
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    verbose_name='审核人', related_name='reviewed_contents')
    reject_reason = models.TextField('驳回原因', blank=True)
    risk_score = models.PositiveIntegerField('风险分', default=0)
    risk_level = models.CharField('风险等级', max_length=16, choices=RISK_LEVEL_CHOICES, default='LOW')
    moderation_source = models.CharField('审核来源', max_length=16, choices=MODERATION_SOURCE_CHOICES, default='MANUAL')
    
    like_count = models.PositiveIntegerField('点赞数', default=0)
    comment_count = models.PositiveIntegerField('评论数', default=0)
    favorite_count = models.PositiveIntegerField('收藏数', default=0)
    view_count = models.PositiveIntegerField('浏览数', default=0)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    published_at = models.DateTimeField('发布时间', null=True, blank=True)

    # 关联资产
    assets = models.ManyToManyField(Asset, through='ContentAsset', verbose_name='关联资产')
    boards = models.ManyToManyField('Board', through='ContentBoard', verbose_name='关联板块', blank=True)

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
        indexes = [
            models.Index(
                fields=['asset', '-created_at'],
                name='idx_content_asset_time',
            ),
        ]

    def __str__(self):
        return f"{self.content.title} - {self.asset.code}"


class ContentBoard(models.Model):
    """内容-板块关联表（多对多）"""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, verbose_name='内容')
    board = models.ForeignKey(Board, on_delete=models.CASCADE, verbose_name='板块')

    created_at = models.DateTimeField('关联时间', default=timezone.now)

    class Meta:
        db_table = 'content_board'
        verbose_name = '内容板块关联'
        verbose_name_plural = '内容板块关联'
        unique_together = ['content', 'board']
        indexes = [
            models.Index(fields=['board', 'created_at'], name='idx_content_board_board'),
        ]

    def __str__(self):
        return f"{self.content.title} - {self.board.name}"


class ContentMeta(models.Model):
    """内容扩展元信息（帖子类型等）"""
    CONTENT_TYPE_CHOICES = [
        ('NORMAL', '普通帖子'),
        ('LONGFORM', '长文分析'),
        ('POLL', '投票调研'),
        ('LIVE', '实时讨论'),
    ]
    FORMAT_TYPE_CHOICES = [
        ('PLAIN', '纯文本'),
        ('RICH_TEXT', '富文本'),
    ]

    content = models.OneToOneField(Content, on_delete=models.CASCADE, related_name='meta', verbose_name='内容')
    content_type = models.CharField('内容类型', max_length=20, choices=CONTENT_TYPE_CHOICES, default='NORMAL')
    format_type = models.CharField('格式类型', max_length=20, choices=FORMAT_TYPE_CHOICES, default='PLAIN')
    repost_count = models.PositiveIntegerField('转发数', default=0)
    forward_count = models.PositiveIntegerField('分享数', default=0)

    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'content_meta'
        verbose_name = '内容扩展'
        verbose_name_plural = '内容扩展'


class Poll(models.Model):
    """投票主题"""
    content = models.OneToOneField(Content, on_delete=models.CASCADE, related_name='poll', verbose_name='内容')
    question = models.CharField('投票问题', max_length=300)
    allow_multiple = models.BooleanField('是否可多选', default=False)
    expires_at = models.DateTimeField('截止时间', null=True, blank=True)
    is_closed = models.BooleanField('是否关闭', default=False)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'poll'
        verbose_name = '投票'
        verbose_name_plural = '投票'


class PollOption(models.Model):
    """投票选项"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options', verbose_name='投票')
    text = models.CharField('选项文本', max_length=200)
    sort_order = models.PositiveIntegerField('排序', default=0)
    vote_count = models.PositiveIntegerField('票数', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'poll_option'
        verbose_name = '投票选项'
        verbose_name_plural = '投票选项'
        ordering = ['sort_order', 'id']


class PollVote(models.Model):
    """投票记录"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes', verbose_name='投票')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes', verbose_name='选项')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes', verbose_name='用户')
    created_at = models.DateTimeField('投票时间', default=timezone.now)

    class Meta:
        db_table = 'poll_vote'
        verbose_name = '投票记录'
        verbose_name_plural = '投票记录'
        unique_together = ['poll', 'option', 'user']
        indexes = [
            models.Index(fields=['poll', 'user'], name='idx_poll_vote_poll_user'),
        ]


class Repost(models.Model):
    """帖子转发"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reposts', verbose_name='用户')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='reposts', verbose_name='内容')
    comment = models.CharField('转发语', max_length=500, blank=True)
    created_at = models.DateTimeField('转发时间', default=timezone.now)

    class Meta:
        db_table = 'repost'
        verbose_name = '转发'
        verbose_name_plural = '转发'
        unique_together = ['user', 'content']
        indexes = [
            models.Index(fields=['content', '-created_at'], name='idx_repost_content_time'),
        ]


class Mention(models.Model):
    """@提及记录"""
    TARGET_TYPE_CHOICES = [
        ('POST', '帖子'),
        ('COMMENT', '评论'),
    ]

    source_type = models.CharField('来源类型', max_length=20, choices=TARGET_TYPE_CHOICES)
    source_id = models.PositiveIntegerField('来源ID')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentions_sent', verbose_name='提及者')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentions_received', verbose_name='被提及者')
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'mention'
        verbose_name = '提及记录'
        verbose_name_plural = '提及记录'
        unique_together = ['source_type', 'source_id', 'to_user']
        indexes = [
            models.Index(fields=['to_user', '-created_at'], name='idx_mention_to_user_time'),
        ]


class ContentAttachment(models.Model):
    """帖子附件（需审核）"""
    STATUS_CHOICES = [
        ('PENDING', '待审核'),
        ('APPROVED', '已通过'),
        ('REJECTED', '已驳回'),
    ]

    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='内容',
        null=True,
        blank=True,
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_attachments', verbose_name='上传者')
    file = models.FileField('附件文件', upload_to='content_attachments/%Y/%m/')
    thumb = models.FileField(
        '缩略图',
        upload_to='content_attachments/thumbs/%Y/%m/',
        blank=True,
        null=True,
        help_text='图片附件生成的小图，供列表等场景使用',
    )
    original_name = models.CharField('原始文件名', max_length=255, blank=True)
    mime_type = models.CharField('文件类型', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('文件大小', default=0)
    status = models.CharField('审核状态', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_attachments',
        verbose_name='审核人'
    )
    reject_reason = models.TextField('驳回原因', blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'content_attachment'
        verbose_name = '内容附件'
        verbose_name_plural = '内容附件'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='idx_attachment_status_time'),
            models.Index(fields=['uploaded_by', '-created_at'], name='idx_attachment_uploader_time'),
        ]


class CommentAttachment(models.Model):
    """评论附件（无需审核）"""
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='评论',
        null=True,
        blank=True,
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_attachments', verbose_name='上传者')
    file = models.FileField('附件文件', upload_to='comment_attachments/%Y/%m/')
    thumb = models.FileField(
        '缩略图',
        upload_to='comment_attachments/thumbs/%Y/%m/',
        blank=True,
        null=True,
    )
    original_name = models.CharField('原始文件名', max_length=255, blank=True)
    mime_type = models.CharField('文件类型', max_length=100, blank=True)
    file_size = models.PositiveBigIntegerField('文件大小', default=0)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'comment_attachment'
        verbose_name = '评论附件'
        verbose_name_plural = '评论附件'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['uploaded_by', '-created_at'], name='idx_cmtatt_uploader_time'),
        ]


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
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_favorite_user_time'),
        ]

    def __str__(self):
        return f"{self.user.username}收藏了{self.content.title}"