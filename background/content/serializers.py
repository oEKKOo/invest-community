from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Content, Comment, Asset, Like, Favorite, ContentAsset

User = get_user_model()


class AssetSerializer(serializers.ModelSerializer):
    """资产序列化器"""
    class Meta:
        model = Asset
        fields = ['id', 'code', 'name', 'asset_type', 'market']


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
    """内容创建序列化器"""
    content = serializers.CharField(source='body')  # 接口文档使用content字段
    tags = serializers.JSONField(source='tags_json')  # 接口文档使用tags字段
    assetIds = serializers.ListField(
        child=serializers.IntegerField(), 
        required=False, 
        write_only=True,
        source='asset_ids'
    )

    class Meta:
        model = Content
        fields = ['title', 'content', 'tags', 'status', 'assetIds']

    def validate_status(self, value):
        if value not in ['DRAFT', 'PENDING_REVIEW']:
            raise serializers.ValidationError("创建时状态只能是草稿或待审核")
        return value

    def create(self, validated_data):
        asset_ids = validated_data.pop('asset_ids', [])
        content = Content.objects.create(**validated_data)
        
        # 关联资产
        if asset_ids:
            assets = Asset.objects.filter(id__in=asset_ids)
            for asset in assets:
                ContentAsset.objects.create(content=content, asset=asset)
        
        # 如果是发布状态，设置发布时间
        if content.status == 'PUBLISHED':
            content.published_at = timezone.now()
            content.save()
        
        return content


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    author_name = serializers.CharField(source='author.display_name', read_only=True)
    author_avatar = serializers.URLField(source='author.avatar_url', read_only=True)
    reply_to_username = serializers.CharField(source='reply_to_user.username', read_only=True)
    replies = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'author_id', 'author_name', 'author_avatar',
            'parent_id', 'reply_to_user_id', 'reply_to_username',
            'body', 'like_count', 'created_at', 'replies', 'is_liked'
        ]
        read_only_fields = ['author_id', 'like_count']

    def get_replies(self, obj):
        # 只返回前几条子评论
        replies = obj.replies.filter(status='NORMAL')[:5]
        return CommentSerializer(replies, many=True, context=self.context).data

    def get_is_liked(self, obj):
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


class LikeSerializer(serializers.ModelSerializer):
    """点赞序列化器"""
    class Meta:
        model = Like
        fields = ['target_type', 'target_id']

    def validate(self, attrs):
        target_type = attrs['target_type']
        target_id = attrs['target_id']
        
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