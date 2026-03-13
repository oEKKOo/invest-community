from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Portfolio,
    PortfolioAsset,
    UserHolding,
    PortfolioComment,
    PortfolioSubscription,
    PortfolioUpdateLog,
)
from content.models import Like, Asset

User = get_user_model()


# ---------------------------------------------------------------------------
# 资产简要信息（嵌套在组合资产内展示）
# ---------------------------------------------------------------------------
class AssetBriefSerializer(serializers.ModelSerializer):
    """组合/持仓中嵌套的资产简要信息"""
    assetType = serializers.CharField(source='asset_type', read_only=True)
    displayMarket = serializers.CharField(source='display_market', read_only=True)

    class Meta:
        model = Asset
        fields = ['id', 'code', 'name', 'assetType', 'market', 'displayMarket']


# ---------------------------------------------------------------------------
# PortfolioAsset 序列化器
# ---------------------------------------------------------------------------
class PortfolioAssetSerializer(serializers.ModelSerializer):
    """
    组合资产序列化器（读取）
    - 优先从关联 Asset 取 code/name/market 字段
    - 兼容历史无 asset FK 的旧记录（直接读 symbol/name）
    """
    assetId = serializers.IntegerField(source='asset_id', read_only=True)
    symbol = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    market = serializers.SerializerMethodField()
    assetType = serializers.SerializerMethodField()
    displayMarket = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioAsset
        fields = ['assetId', 'symbol', 'name', 'market', 'assetType', 'displayMarket', 'allocation']

    def get_symbol(self, obj):
        return obj.asset.code if obj.asset else obj.symbol

    def get_name(self, obj):
        return obj.asset.name if obj.asset else obj.name

    def get_market(self, obj):
        return obj.asset.market if obj.asset else ''

    def get_assetType(self, obj):
        return obj.asset.asset_type if obj.asset else ''

    def get_displayMarket(self, obj):
        if obj.asset:
            return obj.asset.display_market
        return ''


class PortfolioAssetCreateSerializer(serializers.Serializer):
    """
    组合资产写入序列化器（接受 camelCase 字段）
    支持两种方式：
    1. 新接口：assetId（强关联到 Asset 表）
    2. 旧接口兜底：symbol + name（无 FK，仅供存量数据）
    优先级：assetId > symbol
    """
    assetId = serializers.IntegerField(required=False, allow_null=True)
    symbol = serializers.CharField(required=False, max_length=20, allow_blank=True)
    name = serializers.CharField(required=False, max_length=100, allow_blank=True)
    allocation = serializers.DecimalField(max_digits=5, decimal_places=2)

    def validate(self, attrs):
        asset_id = attrs.get('assetId')
        symbol = attrs.get('symbol', '').strip()

        if not asset_id and not symbol:
            raise serializers.ValidationError('必须提供 assetId 或 symbol')

        if asset_id:
            try:
                attrs['_asset'] = Asset.objects.get(pk=asset_id)
            except Asset.DoesNotExist:
                raise serializers.ValidationError(f'资产 ID {asset_id} 不存在')
        else:
            attrs['_asset'] = None

        allocation = attrs.get('allocation', 0)
        if allocation < 0 or allocation > 100:
            raise serializers.ValidationError('配置比例必须在 0-100 之间')

        return attrs


# ---------------------------------------------------------------------------
# Portfolio 序列化器
# ---------------------------------------------------------------------------
class PortfolioListSerializer(serializers.ModelSerializer):
    """组合列表序列化器（camelCase 字段，对齐接口文档）"""
    userId = serializers.IntegerField(source='owner_id', read_only=True)
    userName = serializers.CharField(source='owner.display_name', read_only=True)
    riskLevel = serializers.CharField(source='risk_level', read_only=True)
    returnsYTD = serializers.FloatField(source='returns_ytd', read_only=True)
    isPublic = serializers.BooleanField(source='is_public', read_only=True)
    likes = serializers.IntegerField(source='like_count', read_only=True)
    isLiked = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    assets = PortfolioAssetSerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            'id', 'userId', 'userName', 'title', 'description',
            'riskLevel', 'returnsYTD', 'isPublic', 'likes',
            'assets', 'isLiked', 'createdAt'
        ]

    def get_isLiked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(
                user=request.user, target_type='PORTFOLIO', target_id=obj.id
            ).exists()
        return False


class PortfolioCreateSerializer(serializers.ModelSerializer):
    """组合创建/更新序列化器（接受 camelCase 字段）"""
    riskLevel = serializers.CharField(source='risk_level', required=True)
    isPublic = serializers.BooleanField(source='is_public', required=False, default=True)
    assets = PortfolioAssetCreateSerializer(many=True)

    class Meta:
        model = Portfolio
        fields = ['title', 'description', 'riskLevel', 'isPublic', 'assets']

    def validate_assets(self, assets):
        total_allocation = sum(asset['allocation'] for asset in assets)
        if total_allocation > 100:
            raise serializers.ValidationError('总仓位不能超过 100%')
        return assets

    def _build_portfolio_asset(self, portfolio, asset_data):
        """根据 asset_data 构建 PortfolioAsset 实例"""
        asset_obj = asset_data.get('_asset')
        symbol = asset_data.get('symbol', '')
        name = asset_data.get('name', '')
        allocation = asset_data['allocation']

        if asset_obj:
            # 新接口：强外键关联
            return PortfolioAsset(
                portfolio=portfolio,
                asset=asset_obj,
                symbol=asset_obj.code,
                name=asset_obj.name,
                allocation=allocation,
            )
        else:
            # 旧接口兜底：无 FK
            return PortfolioAsset(
                portfolio=portfolio,
                asset=None,
                symbol=symbol,
                name=name,
                allocation=allocation,
            )

    def create(self, validated_data):
        assets_data = validated_data.pop('assets')
        portfolio = Portfolio.objects.create(**validated_data)

        objs = [self._build_portfolio_asset(portfolio, a) for a in assets_data]
        PortfolioAsset.objects.bulk_create(objs)

        return portfolio

    def update(self, instance, validated_data):
        assets_data = validated_data.pop('assets', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if assets_data is not None:
            instance.assets.all().delete()
            objs = [self._build_portfolio_asset(instance, a) for a in assets_data]
            PortfolioAsset.objects.bulk_create(objs)

        return instance


class PortfolioDetailSerializer(PortfolioListSerializer):
    """组合详情序列化器"""
    # 是否已订阅
    isSubscribed = serializers.SerializerMethodField()

    class Meta(PortfolioListSerializer.Meta):
        fields = PortfolioListSerializer.Meta.fields + ['isSubscribed']

    def get_isSubscribed(self, obj: Portfolio) -> bool:
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PortfolioSubscription.objects.filter(
                portfolio=obj, user=request.user
            ).exists()
        return False


# ---------------------------------------------------------------------------
# Portfolio 评论 / 订阅 / 更新日志 序列化器
# ---------------------------------------------------------------------------


class PortfolioCommentSerializer(serializers.ModelSerializer):
    """组合评论读取序列化器（一级+简单楼中楼）"""
    authorId = serializers.IntegerField(source='author_id', read_only=True)
    authorName = serializers.CharField(source='author.display_name', read_only=True)
    authorAvatar = serializers.CharField(source='author.avatar_url', read_only=True)
    parentId = serializers.IntegerField(source='parent_id', read_only=True)
    replyToUserId = serializers.IntegerField(source='reply_to_user_id', read_only=True)
    replyToUsername = serializers.CharField(
        source='reply_to_user.display_name', read_only=True
    )
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioComment
        fields = [
            'id',
            'authorId',
            'authorName',
            'authorAvatar',
            'parentId',
            'replyToUserId',
            'replyToUsername',
            'body',
            'createdAt',
            'replies',
        ]

    def get_replies(self, obj: PortfolioComment):
        # 简单返回直接子回复列表（可按需加限制）
        qs = obj.replies.filter(is_deleted=False).select_related(
            'author', 'reply_to_user'
        )
        return PortfolioCommentSerializer(qs, many=True, context=self.context).data


class PortfolioCommentCreateSerializer(serializers.Serializer):
    """创建组合评论序列化器"""
    body = serializers.CharField()
    parentId = serializers.IntegerField(required=False, allow_null=True)
    replyToUserId = serializers.IntegerField(required=False, allow_null=True)

    def validate_body(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError('评论内容不能为空')
        return value

    def create(self, validated_data):
        request = self.context['request']
        portfolio: Portfolio = self.context['portfolio']

        parent = None
        parent_id = validated_data.get('parentId')
        if parent_id:
            parent = PortfolioComment.objects.filter(
                pk=parent_id, portfolio=portfolio
            ).first()

        reply_to_user = None
        reply_to_user_id = validated_data.get('replyToUserId')
        if reply_to_user_id:
            reply_to_user = User.objects.filter(pk=reply_to_user_id).first()

        return PortfolioComment.objects.create(
            portfolio=portfolio,
            author=request.user,
            parent=parent,
            reply_to_user=reply_to_user,
            body=validated_data['body'].strip(),
        )


class PortfolioUpdateLogSerializer(serializers.ModelSerializer):
    """组合更新日志序列化器"""
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = PortfolioUpdateLog
        fields = ['id', 'title', 'content', 'createdAt']


# ---------------------------------------------------------------------------
# UserHolding 序列化器
# ---------------------------------------------------------------------------
class UserHoldingSerializer(serializers.ModelSerializer):
    """个人持仓读取序列化器"""
    assetId = serializers.IntegerField(source='asset_id', read_only=True)
    code = serializers.CharField(source='asset.code', read_only=True)
    name = serializers.CharField(source='asset.name', read_only=True)
    market = serializers.CharField(source='asset.market', read_only=True)
    assetType = serializers.CharField(source='asset.asset_type', read_only=True)
    displayMarket = serializers.CharField(source='asset.display_market', read_only=True)
    costPrice = serializers.DecimalField(source='cost_price', max_digits=12, decimal_places=4, read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = UserHolding
        fields = [
            'id', 'assetId', 'code', 'name', 'market', 'assetType', 'displayMarket',
            'quantity', 'costPrice', 'notes', 'createdAt', 'updatedAt'
        ]


class UserHoldingCreateSerializer(serializers.Serializer):
    """个人持仓创建/更新序列化器"""
    assetId = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=0)
    costPrice = serializers.DecimalField(max_digits=12, decimal_places=4, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_assetId(self, value):
        try:
            return Asset.objects.get(pk=value)
        except Asset.DoesNotExist:
            raise serializers.ValidationError(f'资产 ID {value} 不存在')

    def create(self, validated_data):
        user = self.context['request'].user
        asset = validated_data['assetId']
        holding, _ = UserHolding.objects.update_or_create(
            user=user,
            asset=asset,
            defaults={
                'quantity': validated_data['quantity'],
                'cost_price': validated_data['costPrice'],
                'notes': validated_data.get('notes', ''),
            }
        )
        return holding

    def update(self, instance, validated_data):
        instance.asset = validated_data.get('assetId', instance.asset)
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.cost_price = validated_data.get('costPrice', instance.cost_price)
        instance.notes = validated_data.get('notes', instance.notes)
        instance.save()
        return instance
