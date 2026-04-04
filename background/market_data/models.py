from django.db import models
from django.utils import timezone


class AssetQuoteSnapshot(models.Model):
    """
    资产行情快照表（对接 Finnhub /quote）
    保存最新行情数据，用于减少对第三方 API 的直接依赖
    数据保留策略：MVP 阶段保留 7 天内的快照，定期清理
    """
    asset = models.ForeignKey(
        'content.Asset',
        on_delete=models.CASCADE,
        verbose_name='资产',
        related_name='quote_snapshots'
    )
    price = models.DecimalField('最新价', max_digits=18, decimal_places=6, null=True, blank=True)
    change_amount = models.DecimalField('涨跌额', max_digits=18, decimal_places=6, null=True, blank=True)
    change_pct = models.DecimalField('涨跌幅(%)', max_digits=9, decimal_places=4, null=True, blank=True)
    open = models.DecimalField('开盘价', max_digits=18, decimal_places=6, null=True, blank=True)
    high = models.DecimalField('最高价', max_digits=18, decimal_places=6, null=True, blank=True)
    low = models.DecimalField('最低价', max_digits=18, decimal_places=6, null=True, blank=True)
    prev_close = models.DecimalField('昨收价', max_digits=18, decimal_places=6, null=True, blank=True)
    volume = models.BigIntegerField('成交量', null=True, blank=True)
    amount = models.DecimalField('成交额', max_digits=20, decimal_places=2, null=True, blank=True)
    quote_time = models.DateTimeField('行情时间', null=True, blank=True)
    source = models.CharField('数据来源', max_length=16, default='finnhub')
    created_at = models.DateTimeField('写入时间', default=timezone.now)

    class Meta:
        db_table = 'asset_quote_snapshot'
        verbose_name = '行情快照'
        verbose_name_plural = '行情快照'
        ordering = ['-quote_time']
        indexes = [
            # 单资产最新快照：get_or_refresh_quote / 子查询 latest quote_time
            models.Index(fields=['asset', '-quote_time'], name='idx_quote_asset_time'),
            models.Index(fields=['-quote_time'], name='idx_quote_time'),
            # 按写入时间取最新 id 的子查询（如 AssetList withQuote）
            models.Index(fields=['asset', '-created_at'], name='idx_quote_asset_created'),
            # 榜单 market_rankings：ORDER BY change_pct / volume（减轻 filesort）
            models.Index(fields=['-change_pct'], name='idx_quote_change_pct'),
            models.Index(fields=['-volume'], name='idx_quote_volume'),
        ]

    def __str__(self):
        return f"{self.asset.code} @ {self.price} ({self.quote_time})"


class AssetKline(models.Model):
    """
    K 线数据表（对接 Finnhub /stock/candle）
    支持多周期：1/5/15/30/60/D/W/M
    MVP 阶段先做日K（resolution='D'），保留最近 200 根
    """
    RESOLUTION_CHOICES = [
        ('1', '1分钟'),
        ('5', '5分钟'),
        ('15', '15分钟'),
        ('30', '30分钟'),
        ('60', '60分钟'),
        ('D', '日K'),
        ('W', '周K'),
        ('M', '月K'),
    ]

    asset = models.ForeignKey(
        'content.Asset',
        on_delete=models.CASCADE,
        verbose_name='资产',
        related_name='klines'
    )
    resolution = models.CharField('周期', max_length=8, choices=RESOLUTION_CHOICES, default='D')
    k_time = models.DateTimeField('K线时间点')
    open = models.DecimalField('开盘价', max_digits=18, decimal_places=6)
    high = models.DecimalField('最高价', max_digits=18, decimal_places=6)
    low = models.DecimalField('最低价', max_digits=18, decimal_places=6)
    close = models.DecimalField('收盘价', max_digits=18, decimal_places=6)
    volume = models.BigIntegerField('成交量', null=True, blank=True)
    created_at = models.DateTimeField('写入时间', default=timezone.now)

    class Meta:
        db_table = 'asset_kline'
        verbose_name = 'K线数据'
        verbose_name_plural = 'K线数据'
        # 防止同一资产同一周期同一时间点重复写入
        unique_together = [('asset', 'resolution', 'k_time')]
        indexes = [
            # 主查询路径：按资产+周期拉取时序数据
            models.Index(fields=['asset', 'resolution', '-k_time'], name='idx_kline_asset_res_time'),
            # fill_holding_snapshots SQL JOIN 路径：asset_id + resolution + k_time 范围扫描
            # 覆盖：ON ak.asset_id = uh.asset_id AND ak.resolution = 'D' AND DATE(ak.k_time) >= ?
            models.Index(fields=['asset', 'resolution', 'k_time'], name='idx_kline_asset_res_time_asc'),
        ]

    def __str__(self):
        return f"{self.asset.code} [{self.resolution}] {self.k_time}"


class DataJobLog(models.Model):
    """
    数据同步任务日志
    记录每次数据同步任务的开始/结束/成功失败/影响条数/失败原因
    对应 Finnhub 规范中的 DataJobLog 要求
    """
    JOB_TYPE_CHOICES = [
        ('SYMBOLS_SYNC', '标的清单同步'),
        ('KLINE_SYNC', 'K线数据同步'),
        ('QUOTE_REFRESH', '行情快照刷新'),
        ('DQ_CHECK', '数据质量校验'),
    ]
    STATUS_CHOICES = [
        ('RUNNING', '运行中'),
        ('SUCCESS', '成功'),
        ('FAILED', '失败'),
        ('PARTIAL', '部分成功'),
    ]

    job_type = models.CharField('任务类型', max_length=32, choices=JOB_TYPE_CHOICES)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='RUNNING')
    market = models.CharField('目标市场', max_length=16, blank=True, help_text='如 CN/HK/US')
    asset_code = models.CharField('目标资产代码', max_length=32, blank=True, help_text='单资产任务填此字段')
    started_at = models.DateTimeField('开始时间', default=timezone.now)
    finished_at = models.DateTimeField('结束时间', null=True, blank=True)
    affected_rows = models.IntegerField('影响条数', default=0)
    error_message = models.TextField('失败原因', blank=True)
    extra_info = models.JSONField('附加信息', default=dict, blank=True)

    class Meta:
        db_table = 'data_job_log'
        verbose_name = '数据任务日志'
        verbose_name_plural = '数据任务日志'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['job_type', '-started_at'], name='idx_job_type_time'),
            models.Index(fields=['status', '-started_at'], name='idx_job_status_time'),
        ]

    def __str__(self):
        return f"[{self.job_type}] {self.status} @ {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def duration_seconds(self):
        if self.finished_at and self.started_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
