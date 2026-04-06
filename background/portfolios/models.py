from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Portfolio(models.Model):
    """投资组合表"""
    RISK_LEVEL_CHOICES = [
        ('Low', '低风险'),
        ('Medium', '中风险'),
        ('High', '高风险'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者', related_name='portfolios')
    title = models.CharField('组合名称', max_length=200)
    description = models.TextField('描述', blank=True)
    strategy_note = models.TextField('策略说明', blank=True)
    
    risk_level = models.CharField('风险等级', max_length=20, choices=RISK_LEVEL_CHOICES, default='Medium')
    returns_ytd = models.DecimalField('年初至今回报', max_digits=10, decimal_places=4, default=0.0000)
    
    is_public = models.BooleanField('是否公开', default=True)
    like_count = models.PositiveIntegerField('点赞数', default=0)
    subscription_count = models.PositiveIntegerField('订阅数', default=0)
    
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'portfolio'
        verbose_name = '投资组合'
        verbose_name_plural = '投资组合'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['is_public', '-returns_ytd']),
        ]

    def __str__(self):
        return self.title


class PortfolioAsset(models.Model):
    """
    组合资产表（升级版）
    - asset: 强外键关联 Asset 表（新接口必填）
    - symbol / name: 冗余字段，从 asset 自动同步，保留供历史数据兼容展示
    """
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE,
        verbose_name='所属组合', related_name='assets'
    )
    # ---- 强关联：指向真实资产记录 ----
    asset = models.ForeignKey(
        'content.Asset',
        on_delete=models.PROTECT,
        verbose_name='关联资产',
        null=True, blank=True,
        related_name='portfolio_assets',
        help_text='指向 content_asset 表的真实资产记录'
    )
    # ---- 冗余展示字段（由 asset 自动填充，或历史手动录入）----
    symbol = models.CharField('资产代码', max_length=20, blank=True)
    name = models.CharField('资产名称', max_length=100, blank=True)

    allocation = models.DecimalField('仓位百分比', max_digits=5, decimal_places=2)  # 0-100

    created_at = models.DateTimeField('添加时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'portfolio_asset'
        verbose_name = '组合资产'
        verbose_name_plural = '组合资产'
        # 同一组合内同一资产只能出现一次（优先用 asset FK 保证唯一性）
        unique_together = ['portfolio', 'asset']
        indexes = [
            models.Index(fields=['portfolio', 'asset']),
        ]

    def save(self, *args, **kwargs):
        """保存时若关联了 asset，自动同步 symbol/name 冗余字段"""
        if self.asset_id and self.asset:
            self.symbol = self.asset.code
            self.name = self.asset.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.portfolio.title} - {self.symbol or self.asset_id}"


class UserHolding(models.Model):
    """
    个人持仓表
    记录用户持有的具体资产仓位、成本价等信息，
    与 Asset 强外键关联，支持行情聚合与展示。
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='持有人', related_name='holdings'
    )
    asset = models.ForeignKey(
        'content.Asset',
        on_delete=models.PROTECT,
        verbose_name='持有资产',
        related_name='user_holdings'
    )
    quantity = models.DecimalField(
        '持有数量', max_digits=18, decimal_places=4, default=0,
        help_text='持有股数/份额'
    )
    cost_price = models.DecimalField(
        '成本均价', max_digits=12, decimal_places=4, default=0,
        help_text='买入均价（元/股）'
    )
    notes = models.TextField('备注', blank=True)

    created_at = models.DateTimeField('添加时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_holding'
        verbose_name = '个人持仓'
        verbose_name_plural = '个人持仓'
        unique_together = ['user', 'asset']
        indexes = [
            models.Index(fields=['user', 'asset']),
            # 为 fill_holding_snapshots SQL 中的 JOIN ON asset_id 提供独立索引
            # unique_together(user, asset) 的复合索引无法覆盖单独 asset_id 的 JOIN
            models.Index(fields=['asset'], name='idx_holding_asset'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.asset.code} x{self.quantity}"

    @property
    def market_value(self):
        """持仓市值（需外部传入现价计算，此处仅返回成本市值兜底）"""
        return float(self.quantity) * float(self.cost_price)


class HoldingDailySnapshot(models.Model):
    """
    持仓每日价格快照
    以日K收盘价为唯一估值口径，用于计算日收益/持有收益/累计收益。
    设计原则：
      - 每天固定更新一次（或启动时补缺）
      - 只存 close_price，计算时结合 UserHolding.quantity / cost_price 实时推导
      - unique_together = (holding, date)，防止重复写入
    """
    holding = models.ForeignKey(
        UserHolding,
        on_delete=models.CASCADE,
        verbose_name='关联持仓',
        related_name='daily_snapshots'
    )
    date = models.DateField('快照日期')
    close_price = models.DecimalField(
        '收盘估值价', max_digits=18, decimal_places=6,
        help_text='来源：AssetKline.close（日K收盘价）'
    )
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'holding_daily_snapshot'
        verbose_name = '持仓每日快照'
        verbose_name_plural = '持仓每日快照'
        unique_together = ['holding', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['holding', '-date'], name='idx_holding_snap_date'),
        ]

    def __str__(self):
        return f"{self.holding.asset.code} @ {self.close_price} ({self.date})"


class PortfolioComment(models.Model):
    """组合评论表（结构复用帖子评论模型的关键字段）"""
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='所属组合',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portfolio_comments',
        verbose_name='评论作者',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='父评论',
    )
    reply_to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='portfolio_comment_replies',
        verbose_name='被回复用户',
    )
    body = models.TextField('评论内容')
    is_deleted = models.BooleanField('是否已删除', default=False)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'portfolio_comment'
        verbose_name = '组合评论'
        verbose_name_plural = '组合评论'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['portfolio', 'created_at'], name='idx_portfolio_cmt_port_time'),
            models.Index(fields=['parent', 'created_at'], name='idx_portfolio_cmt_parent_time'),
        ]

    def __str__(self):
        return f"{self.author.username}: {self.body[:20]}"


class PortfolioSubscription(models.Model):
    """组合订阅 / 收藏"""
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='组合',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portfolio_subscriptions',
        verbose_name='用户',
    )
    created_at = models.DateTimeField('订阅时间', default=timezone.now)

    class Meta:
        db_table = 'portfolio_subscription'
        verbose_name = '组合订阅'
        verbose_name_plural = '组合订阅'
        unique_together = ['portfolio', 'user']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_portfolio_sub_user_time'),
            models.Index(fields=['portfolio', '-created_at'], name='idx_portfolio_sub_port_time'),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.portfolio.title}"


class PortfolioFavorite(models.Model):
    """组合收藏"""
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='组合',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portfolio_favorites',
        verbose_name='用户',
    )
    created_at = models.DateTimeField('收藏时间', default=timezone.now)

    class Meta:
        db_table = 'portfolio_favorite'
        verbose_name = '组合收藏'
        verbose_name_plural = '组合收藏'
        unique_together = ['portfolio', 'user']
        indexes = [
            models.Index(fields=['portfolio', 'created_at'], name='idx_portfolio_fav_portfolio'),
            models.Index(fields=['user', 'created_at'], name='idx_portfolio_fav_user'),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.portfolio.title}"


class PortfolioUpdateLog(models.Model):
    """
    组合更新日志：记录调仓说明、收益复盘、策略变更等
    """
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='update_logs',
        verbose_name='组合',
    )
    title = models.CharField('更新标题', max_length=200)
    content = models.TextField('更新内容')
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        db_table = 'portfolio_update_log'
        verbose_name = '组合更新日志'
        verbose_name_plural = '组合更新日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.portfolio.title} - {self.title}"