from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Content, Comment, Asset, Like, Favorite, ContentAsset

User = get_user_model()


class AssetSerializer(serializers.ModelSerializer):
    """
    资产序列化器
    遵循 work.mdc §2.4：统一字段命名 assetType/market
    """
    assetType = serializers.CharField(source='asset_type', read_only=True)
    displayMarket = serializers.CharField(source='display_market', read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'code', 'name', 'asset_type', 'assetType',
            'market', 'displayMarket', 'status',
            'currency', 'industry', 'logo_url', 'description',
            'finnhub_symbol', 'last_sync_at',
        ]
        extra_kwargs = {
            'finnhub_symbol': {'read_only': True},
            'last_sync_at': {'read_only': True},
        }


class ContentListSerializer(serializers.ModelSerializer):
    """内容列表序列化器"""
    authorName = serializers.CharField(source='author.display_name', read_only=True)
    authorAvatar = serializers.URLField(source='author.avatar_url', read_only=True)
    content = serializers.CharField(source='body', read_only=True)  # 接口文档要求用content字段
    tags = serializers.JSONField(source='tags_json', read_only=True)  # 接口文档要求用tags字段
    likes = serializers.IntegerField(source='like_count', read_only=True)
    comments = serializers.IntegerField(source='comment_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    assets = AssetSerializer(many=True, read_only=True)
    isLiked = serializers.SerializerMethodField()
    isFavorited = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = [
            'id', 'authorName', 'authorAvatar',
            'title', 'content', 'status', 'tags',
            'likes', 'comments', 'createdAt', 'assets',
            'isLiked', 'isFavorited'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['authorId'] = instance.author_id  # 手动设置authorId
        return data
    
    def get_isLiked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Like.objects.filter(
                user=user, target_type='POST', target_id=obj.id
            ).exists()
        return False
    
    def get_isFavorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, content=obj).exists()
        return False


class ContentDetailSerializer(ContentListSerializer):
    """内容详情序列化器"""
    comments = serializers.SerializerMethodField()

    class Meta(ContentListSerializer.Meta):
        fields = ContentListSerializer.Meta.fields + ['comments']

    def get_comments(self, obj):
        # 只返回顶级评论，前端可以单独加载子评论
        top_comments = obj.comments.filter(parent__isnull=True, status='NORMAL')[:10]
        return CommentSerializer(top_comments, many=True, context=self.context).data


class ContentCreateSerializer(serializers.ModelSerializer):
    """
    内容创建序列化器
    改造（work.mdc §2.3）：同时支持 assetIds（ID数组）和 assetCodes（代码数组）
    - assetIds: 直接用 Asset 主键关联（原有逻辑，向后兼容）
    - assetCodes: 用真实股票代码关联（用户分享时更方便）
    - 两者同时传时：合并去重
    - assetCodes 不存在时：返回 400（严格模式）
    """
    content = serializers.CharField(source='body')  # 接口文档使用 content 字段
    tags = serializers.JSONField(source='tags_json')  # 接口文档使用 tags 字段
    assetIds = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        source='asset_ids',
        help_text='关联资产ID数组（与 assetCodes 可共存，合并去重）'
    )
    assetCodes = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        write_only=True,
        help_text='关联资产代码数组（如 ["000001", "AAPL"]）'
    )

    class Meta:
        model = Content
        fields = ['title', 'content', 'tags', 'status', 'assetIds', 'assetCodes']

    def validate_status(self, value):
        if value not in ['DRAFT', 'PENDING_REVIEW']:
            raise serializers.ValidationError("创建时状态只能是草稿或待审核")
        return value

    def validate(self, attrs):
        # 校验 assetCodes 是否存在于资产库中
        asset_codes = attrs.get('assetCodes', [])
        if asset_codes:
            existing_codes = set(Asset.objects.filter(code__in=asset_codes).values_list('code', flat=True))
            missing = [c for c in asset_codes if c not in existing_codes]
            if missing:
                raise serializers.ValidationError({
                    'assetCodes': f'以下资产代码不存在于系统中: {missing}。请先通过管理员同步资产数据。'
                })
        return attrs

    def create(self, validated_data):
        asset_ids = list(validated_data.pop('asset_ids', []))
        asset_codes = validated_data.pop('assetCodes', [])

        content = Content.objects.create(**validated_data)

        # 解析 assetCodes → asset_ids（合并去重）
        if asset_codes:
            code_assets = Asset.objects.filter(code__in=asset_codes)
            asset_ids.extend(list(code_assets.values_list('id', flat=True)))

        # 去重并关联
        asset_ids = list(set(asset_ids))
        if asset_ids:
            assets = Asset.objects.filter(id__in=asset_ids)
            for asset in assets:
                ContentAsset.objects.get_or_create(content=content, asset=asset)

        # 如果是发布状态，设置发布时间
        if content.status == 'PUBLISHED':
            content.published_at = timezone.now()
            content.save()

        return content


class CommentSerializer(serializers.ModelSerializer):
    """
    评论序列化器

    说明：
    - 对外字段统一采用 camelCase，保持与接口文档及前端 `types.Comment` 一致；
    - 内部通过 source 映射到模型字段，避免打破现有模型设计。
    """
    authorId = serializers.IntegerField(source='author_id', read_only=True)
    authorName = serializers.CharField(source='author.display_name', read_only=True)
    authorAvatar = serializers.URLField(source='author.avatar_url', read_only=True)
    parentId = serializers.IntegerField(source='parent_id', allow_null=True, read_only=True)
    replyToUserId = serializers.IntegerField(source='reply_to_user_id', allow_null=True, read_only=True)
    replyToUsername = serializers.CharField(source='reply_to_user.username', allow_null=True, read_only=True)
    likeCount = serializers.IntegerField(source='like_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    replies = serializers.SerializerMethodField()
    isLiked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'authorId', 'authorName', 'authorAvatar',
            'parentId', 'replyToUserId', 'replyToUsername',
            'body', 'likeCount', 'createdAt',
            'replies', 'isLiked',
        ]
        read_only_fields = ['authorId', 'likeCount']

    def get_replies(self, obj):
        # 只返回前几条子评论，完整列表通过 /api/comments/{id}/replies/ 分页加载
        replies = obj.replies.filter(status='NORMAL')[:5]
        return CommentSerializer(replies, many=True, context=self.context).data

    def get_isLiked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Like.objects.filter(
                user=user, target_type='COMMENT', target_id=obj.id
            ).exists()
        return False


class CommentCreateSerializer(serializers.ModelSerializer):
    """评论创建序列化器"""
    text = serializers.CharField(source='body')

    class Meta:
        model = Comment
        fields = ['text', 'parent_id', 'reply_to_user_id']

    def create(self, validated_data):
        validated_data['body'] = validated_data.pop('body')
        validated_data['content_id'] = self.context['content_id']
        validated_data['author'] = self.context['request'].user
        return Comment.objects.create(**validated_data)


class LikeSerializer(serializers.Serializer):
    """点赞序列化器（接受 camelCase 字段）"""
    targetType = serializers.ChoiceField(choices=['POST', 'COMMENT', 'PORTFOLIO'])
    targetId = serializers.IntegerField()

    def validate(self, attrs):
        target_type = attrs['targetType']
        target_id = attrs['targetId']
        
        # 验证目标是否存在
        if target_type == 'POST':
            if not Content.objects.filter(id=target_id).exists():
                raise serializers.ValidationError("帖子不存在")
        elif target_type == 'COMMENT':
            if not Comment.objects.filter(id=target_id).exists():
                raise serializers.ValidationError("评论不存在")
        elif target_type == 'PORTFOLIO':
            from portfolios.models import Portfolio
            if not Portfolio.objects.filter(id=target_id).exists():
                raise serializers.ValidationError("组合不存在")
        
        return attrs


class LikeRecordSerializer(serializers.ModelSerializer):
    """用户点赞记录序列化器"""
    class Meta:
        model = Like
        fields = ['id', 'target_type', 'target_id', 'created_at']