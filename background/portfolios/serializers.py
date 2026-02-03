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
    """组合列表序列化器"""
    user_name = serializers.CharField(source='owner.display_name', read_only=True)
    assets = PortfolioAssetSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = [
            'id', 'owner_id', 'user_name', 'title', 'description',
            'risk_level', 'returns_ytd', 'is_public', 'like_count',
            'assets', 'is_liked', 'created_at'
        ]

    def get_is_liked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Like.objects.filter(
                user=user, target_type='PORTFOLIO', target_id=obj.id
            ).exists()
        return False


class PortfolioCreateSerializer(serializers.ModelSerializer):
    """组合创建序列化器"""
    assets = PortfolioAssetSerializer(many=True)

    class Meta:
        model = Portfolio
        fields = ['title', 'description', 'risk_level', 'is_public', 'assets']

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
            # 删除旧的资产配置
            instance.assets.all().delete()
            
            # 创建新的资产配置
            for asset_data in assets_data:
                PortfolioAsset.objects.create(portfolio=instance, **asset_data)
        
        return instance


class PortfolioDetailSerializer(PortfolioListSerializer):
    """组合详情序列化器"""
    pass