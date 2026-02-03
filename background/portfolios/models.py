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
    
    risk_level = models.CharField('风险等级', max_length=20, choices=RISK_LEVEL_CHOICES, default='Medium')
    returns_ytd = models.DecimalField('年初至今回报', max_digits=10, decimal_places=4, default=0.0000)
    
    is_public = models.BooleanField('是否公开', default=True)
    like_count = models.PositiveIntegerField('点赞数', default=0)
    
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
    """组合资产表"""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, verbose_name='所属组合', related_name='assets')
    symbol = models.CharField('资产代码', max_length=20)
    name = models.CharField('资产名称', max_length=100)
    allocation = models.DecimalField('仓位百分比', max_digits=5, decimal_places=2)  # 0-100
    
    created_at = models.DateTimeField('添加时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'portfolio_asset'
        verbose_name = '组合资产'
        verbose_name_plural = '组合资产'
        unique_together = ['portfolio', 'symbol']

    def __str__(self):
        return f"{self.portfolio.title} - {self.symbol}"