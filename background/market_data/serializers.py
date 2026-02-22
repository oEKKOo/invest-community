from rest_framework import serializers
from .models import AssetQuoteSnapshot, AssetKline, DataJobLog


class QuoteSnapshotSerializer(serializers.ModelSerializer):
    """行情快照序列化器（对外接口响应用）"""
    assetId = serializers.IntegerField(source='asset_id')
    code = serializers.CharField(source='asset.code')
    name = serializers.CharField(source='asset.name')
    market = serializers.CharField(source='asset.market')
    price = serializers.SerializerMethodField()
    changeAmount = serializers.SerializerMethodField()
    changePct = serializers.SerializerMethodField()
    open = serializers.SerializerMethodField()
    high = serializers.SerializerMethodField()
    low = serializers.SerializerMethodField()
    prevClose = serializers.SerializerMethodField()
    volume = serializers.IntegerField()
    amount = serializers.SerializerMethodField()
    quoteTime = serializers.DateTimeField(source='quote_time')
    dataUpdatedAt = serializers.DateTimeField(source='created_at')

    class Meta:
        model = AssetQuoteSnapshot
        fields = [
            'assetId', 'code', 'name', 'market',
            'price', 'changeAmount', 'changePct',
            'open', 'high', 'low', 'prevClose',
            'volume', 'amount', 'quoteTime', 'dataUpdatedAt', 'source'
        ]

    def _to_float(self, value):
        return float(value) if value is not None else None

    def get_price(self, obj):
        return self._to_float(obj.price)

    def get_changeAmount(self, obj):
        return self._to_float(obj.change_amount)

    def get_changePct(self, obj):
        return self._to_float(obj.change_pct)

    def get_open(self, obj):
        return self._to_float(obj.open)

    def get_high(self, obj):
        return self._to_float(obj.high)

    def get_low(self, obj):
        return self._to_float(obj.low)

    def get_prevClose(self, obj):
        return self._to_float(obj.prev_close)

    def get_amount(self, obj):
        return self._to_float(obj.amount)


class KlineItemSerializer(serializers.ModelSerializer):
    """单根 K 线序列化器"""
    time = serializers.SerializerMethodField()
    open = serializers.SerializerMethodField()
    high = serializers.SerializerMethodField()
    low = serializers.SerializerMethodField()
    close = serializers.SerializerMethodField()

    class Meta:
        model = AssetKline
        fields = ['time', 'open', 'high', 'low', 'close', 'volume']

    def _to_float(self, value):
        return float(value) if value is not None else None

    def get_time(self, obj):
        """按接口文档格式返回时间：日K 返回 YYYY-MM-DD，分钟级返回 ISO"""
        if obj.resolution == 'D':
            return obj.k_time.strftime('%Y-%m-%d')
        return obj.k_time.isoformat()

    def get_open(self, obj):
        return self._to_float(obj.open)

    def get_high(self, obj):
        return self._to_float(obj.high)

    def get_low(self, obj):
        return self._to_float(obj.low)

    def get_close(self, obj):
        return self._to_float(obj.close)


class DataJobLogSerializer(serializers.ModelSerializer):
    """数据任务日志序列化器（后台监控接口使用）"""
    durationSeconds = serializers.FloatField(source='duration_seconds', read_only=True)

    class Meta:
        model = DataJobLog
        fields = [
            'id', 'job_type', 'status', 'market', 'asset_code',
            'started_at', 'finished_at', 'affected_rows',
            'error_message', 'extra_info', 'durationSeconds'
        ]
        read_only_fields = fields


class BulkQuoteRequestSerializer(serializers.Serializer):
    """批量行情请求参数校验"""
    assetIds = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        max_length=50,
        help_text='资产ID列表，最多50个'
    )
