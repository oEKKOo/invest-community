from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Portfolio, PortfolioAsset
from content.models import Like

User = get_user_model()


class PortfolioAssetSerializer(serializers.ModelSerializer):
    """组合资产序列化器"""
    class Meta:
        model = PortfolioAsset
        fields = ['symbol', 'name', 'allocation']


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
    assets = PortfolioAssetSerializer(many=True)

    class Meta:
        model = Portfolio
        fields = ['title', 'description', 'riskLevel', 'isPublic', 'assets']

    def validate_assets(self, assets):
        """验证资产配置"""
        total_allocation = sum(asset['allocation'] for asset in assets)

        for asset in assets:
            if asset['allocation'] < 0 or asset['allocation'] > 100:
                raise serializers.ValidationError(
                    f"资产 {asset['symbol']} 的配置比例必须在0-100之间"
                )

        if total_allocation > 100:
            raise serializers.ValidationError("总仓位不能超过100%")

        return assets

    def create(self, validated_data):
        assets_data = validated_data.pop('assets')
        portfolio = Portfolio.objects.create(**validated_data)

        for asset_data in assets_data:
            PortfolioAsset.objects.create(portfolio=portfolio, **asset_data)

        return portfolio

    def update(self, instance, validated_data):
        assets_data = validated_data.pop('assets', None)

        # 更新组合基本信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 更新资产配置
        if assets_data is not None:
            instance.assets.all().delete()
            for asset_data in assets_data:
                PortfolioAsset.objects.create(portfolio=instance, **asset_data)

        return instance


class PortfolioDetailSerializer(PortfolioListSerializer):
    """组合详情序列化器"""
    pass
