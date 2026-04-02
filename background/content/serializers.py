from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum
from .models import (
    Content, Comment, Asset, Board, Like, Favorite, ContentAsset, ContentBoard,
    ContentMeta, Poll, PollOption, PollVote, Repost, ContentAttachment, Mention, CommentAttachment
)
from .moderation_service import evaluate_content_risk, persist_moderation_result

User = get_user_model()


class PollOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollOption
        fields = ['id', 'text', 'sort_order', 'vote_count']


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True)
    totalVotes = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ['id', 'question', 'allow_multiple', 'expires_at', 'is_closed', 'options', 'totalVotes']

    def get_totalVotes(self, obj):
        return obj.options.aggregate(total=Sum('vote_count')).get('total') or 0


class ContentAttachmentSerializer(serializers.ModelSerializer):
    fileUrl = serializers.SerializerMethodField()

    class Meta:
        model = ContentAttachment
        fields = [
            'id', 'original_name', 'mime_type', 'file_size',
            'status', 'reject_reason', 'fileUrl', 'created_at'
        ]

    def get_fileUrl(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else ''


class CommentAttachmentSerializer(serializers.ModelSerializer):
    fileUrl = serializers.SerializerMethodField()

    class Meta:
        model = CommentAttachment
        fields = ['id', 'original_name', 'mime_type', 'file_size', 'fileUrl', 'created_at']

    def get_fileUrl(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else ''


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


class BoardSerializer(serializers.ModelSerializer):
    """板块序列化器（支持树结构）"""
    children = serializers.SerializerMethodField()
    parentId = serializers.IntegerField(source='parent_id', read_only=True)

    class Meta:
        model = Board
        fields = [
            'id', 'name', 'slug', 'board_type', 'parentId',
            'description', 'icon', 'sort_order', 'status',
            'is_builtin', 'market', 'industry_code', 'stock_code',
            'children'
        ]

    def get_children(self, obj):
        request = self.context.get('request')
        children = obj.children.order_by('sort_order', 'id')
        if request and not (request.user.is_authenticated and request.user.role in ['MODERATOR', 'ADMIN']):
            children = children.filter(status='ACTIVE')
        return BoardSerializer(children, many=True, context=self.context).data


class BoardCreateUpdateSerializer(serializers.ModelSerializer):
    """板块创建与更新序列化器"""

    class Meta:
        model = Board
        fields = [
            'name', 'slug', 'board_type', 'parent',
            'description', 'icon', 'sort_order', 'status', 'is_builtin',
            'market', 'industry_code', 'stock_code',
        ]

    def validate_parent(self, parent):
        if not parent:
            return parent
        if parent.parent and parent.parent.parent:
            raise serializers.ValidationError('板块层级最多支持三级')
        return parent

    def validate(self, attrs):
        parent = attrs.get('parent', getattr(self.instance, 'parent', None))
        board_type = attrs.get('board_type', getattr(self.instance, 'board_type', None))
        if parent and board_type and parent.board_type != board_type:
            raise serializers.ValidationError({'board_type': '子板块类型必须与父板块一致'})
        return attrs


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
    boards = BoardSerializer(many=True, read_only=True)
    attachments = ContentAttachmentSerializer(many=True, read_only=True)
    contentType = serializers.SerializerMethodField()
    poll = serializers.SerializerMethodField()
    reposts = serializers.SerializerMethodField()
    isLiked = serializers.SerializerMethodField()
    isFavorited = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = [
            'id', 'authorName', 'authorAvatar',
            'title', 'content', 'status', 'tags',
            'likes', 'comments', 'createdAt', 'assets', 'boards', 'attachments',
            'contentType', 'poll', 'reposts',
            'isLiked', 'isFavorited'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['authorId'] = instance.author_id  # 手动设置authorId
        return data
    
    def get_isLiked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            liked_post_ids = self.context.get('liked_post_ids')
            if liked_post_ids is not None:
                return obj.id in liked_post_ids
            return Like.objects.filter(
                user=user, target_type='POST', target_id=obj.id
            ).exists()
        return False
    
    def get_isFavorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            favorited_post_ids = self.context.get('favorited_post_ids')
            if favorited_post_ids is not None:
                return obj.id in favorited_post_ids
            return Favorite.objects.filter(user=user, content=obj).exists()
        return False

    def get_contentType(self, obj):
        if hasattr(obj, 'meta'):
            return obj.meta.content_type
        return 'NORMAL'

    def get_poll(self, obj):
        if hasattr(obj, 'poll'):
            return PollSerializer(obj.poll).data
        return None

    def get_reposts(self, obj):
        if hasattr(obj, 'meta'):
            return obj.meta.repost_count
        return obj.reposts.count()


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
    boardIds = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        source='board_ids',
        help_text='关联板块ID数组（仅允许叶子节点）'
    )
    contentType = serializers.ChoiceField(
        choices=['NORMAL', 'LONGFORM', 'POLL', 'LIVE'],
        required=False,
        default='NORMAL'
    )
    formatType = serializers.ChoiceField(
        choices=['PLAIN', 'RICH_TEXT'],
        required=False,
        default='PLAIN'
    )
    poll = serializers.DictField(required=False, write_only=True)
    attachmentIds = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text='预上传附件ID列表'
    )

    class Meta:
        model = Content
        fields = [
            'title', 'content', 'tags', 'status',
            'assetIds', 'assetCodes', 'boardIds',
            'contentType', 'formatType', 'poll', 'attachmentIds'
        ]

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

        # 自动审核：规则命中后统一走待审核，最终处置在 create 阶段落表
        body = attrs.get('body', '')
        if body:
            attrs['status'] = 'PENDING_REVIEW'

        board_ids = attrs.get('board_ids', [])
        if board_ids:
            boards = Board.objects.filter(id__in=board_ids, status='ACTIVE')
            if boards.count() != len(set(board_ids)):
                raise serializers.ValidationError({'boardIds': '部分板块不存在或已停用'})
            non_leaf_exists = boards.filter(children__isnull=False).exists()
            if non_leaf_exists:
                raise serializers.ValidationError({'boardIds': '仅允许选择叶子板块'})

        content_type = attrs.get('contentType', 'NORMAL')
        poll_data = attrs.get('poll')
        if content_type == 'POLL':
            if not poll_data:
                raise serializers.ValidationError({'poll': '投票类型内容必须提供 poll 数据'})
            options = poll_data.get('options', [])
            question = (poll_data.get('question') or '').strip()
            if len(question) < 2:
                raise serializers.ValidationError({'poll': '投票问题至少2个字符'})
            if len(options) < 2:
                raise serializers.ValidationError({'poll': '投票至少需要2个选项'})

        attachment_ids = attrs.get('attachmentIds', [])
        if attachment_ids:
            qs = ContentAttachment.objects.filter(id__in=attachment_ids, content__isnull=True)
            if qs.count() != len(set(attachment_ids)):
                raise serializers.ValidationError({'attachmentIds': '存在无效附件或附件已被使用'})

        return attrs

    def create(self, validated_data):
        asset_ids = list(validated_data.pop('asset_ids', []))
        asset_codes = validated_data.pop('assetCodes', [])
        board_ids = list(validated_data.pop('board_ids', []))
        content_type = validated_data.pop('contentType', 'NORMAL')
        format_type = validated_data.pop('formatType', 'PLAIN')
        poll_data = validated_data.pop('poll', None)
        attachment_ids = list(validated_data.pop('attachmentIds', []))

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

        if board_ids:
            boards = Board.objects.filter(id__in=board_ids)
            for board in boards:
                ContentBoard.objects.get_or_create(content=content, board=board)

        ContentMeta.objects.update_or_create(
            content=content,
            defaults={'content_type': content_type, 'format_type': format_type},
        )

        if poll_data and content_type == 'POLL':
            poll = Poll.objects.create(
                content=content,
                question=poll_data.get('question', ''),
                allow_multiple=bool(poll_data.get('allowMultiple', False)),
                expires_at=poll_data.get('expiresAt'),
            )
            options = poll_data.get('options', [])
            for idx, opt in enumerate(options):
                text = (opt.get('text') if isinstance(opt, dict) else opt) or ''
                text = text.strip()
                if text:
                    PollOption.objects.create(poll=poll, text=text, sort_order=idx)

        if attachment_ids:
            ContentAttachment.objects.filter(
                id__in=attachment_ids,
                uploaded_by=self.context['request'].user
            ).update(content=content)

        # 自动审核落地（命中日志 + 可疑队列 + 风险字段）
        decision = evaluate_content_risk(
            text=content.body,
            title=content.title,
            author=self.context['request'].user,
        )
        persist_moderation_result(content=content, decision=decision, author=self.context['request'].user)

        # 如果是发布状态，设置发布时间（保留兼容逻辑）
        if content.status == 'PUBLISHED':
            content.published_at = timezone.now()
            content.save(update_fields=['published_at', 'updated_at'])

        return content

    def update(self, instance, validated_data):
        asset_ids = validated_data.pop('asset_ids', None)
        asset_codes = validated_data.pop('assetCodes', None)
        board_ids = validated_data.pop('board_ids', None)
        content_type = validated_data.pop('contentType', None)
        format_type = validated_data.pop('formatType', None)
        poll_data = validated_data.pop('poll', None)
        attachment_ids = validated_data.pop('attachmentIds', None)

        instance = super().update(instance, validated_data)

        # 兼容 PATCH：如传 assetIds/assetCodes 则重建资产关联
        if asset_ids is not None or asset_codes is not None:
            merged_asset_ids = list(asset_ids or [])
            if asset_codes:
                code_assets = Asset.objects.filter(code__in=asset_codes)
                merged_asset_ids.extend(list(code_assets.values_list('id', flat=True)))
            merged_asset_ids = list(set(merged_asset_ids))
            ContentAsset.objects.filter(content=instance).delete()
            if merged_asset_ids:
                for asset in Asset.objects.filter(id__in=merged_asset_ids):
                    ContentAsset.objects.get_or_create(content=instance, asset=asset)

        # 兼容 PATCH：如传 boardIds 则重建板块关联
        if board_ids is not None:
            ContentBoard.objects.filter(content=instance).delete()
            if board_ids:
                for board in Board.objects.filter(id__in=board_ids):
                    ContentBoard.objects.get_or_create(content=instance, board=board)

        if content_type is not None or format_type is not None:
            meta, _ = ContentMeta.objects.get_or_create(content=instance)
            if content_type is not None:
                meta.content_type = content_type
            if format_type is not None:
                meta.format_type = format_type
            meta.save()

        if poll_data is not None:
            if (content_type or getattr(getattr(instance, 'meta', None), 'content_type', 'NORMAL')) == 'POLL':
                poll, _ = Poll.objects.get_or_create(content=instance, defaults={'question': ''})
                poll.question = poll_data.get('question', poll.question)
                poll.allow_multiple = bool(poll_data.get('allowMultiple', poll.allow_multiple))
                poll.expires_at = poll_data.get('expiresAt', poll.expires_at)
                poll.save()
                options = poll_data.get('options')
                if options is not None:
                    poll.options.all().delete()
                    for idx, opt in enumerate(options):
                        text = (opt.get('text') if isinstance(opt, dict) else opt) or ''
                        text = text.strip()
                        if text:
                            PollOption.objects.create(poll=poll, text=text, sort_order=idx)

        if attachment_ids is not None:
            ContentAttachment.objects.filter(content=instance).update(content=None)
            if attachment_ids:
                ContentAttachment.objects.filter(
                    id__in=attachment_ids,
                    uploaded_by=self.context['request'].user
                ).update(content=instance)

        return instance


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
    attachments = CommentAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'authorId', 'authorName', 'authorAvatar',
            'parentId', 'replyToUserId', 'replyToUsername',
            'body', 'likeCount', 'createdAt',
            'replies', 'isLiked', 'attachments'
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
    text = serializers.CharField(source='body', required=False, allow_blank=True)
    parentId = serializers.IntegerField(source='parent_id', required=False, allow_null=True)
    replyToUserId = serializers.IntegerField(source='reply_to_user_id', required=False, allow_null=True)
    attachmentIds = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Comment
        fields = ['text', 'parentId', 'replyToUserId', 'attachmentIds']

    def validate(self, attrs):
        body = (attrs.get('body') or '').strip()
        attachment_ids = attrs.get('attachmentIds') or []
        if not body and not attachment_ids:
            raise serializers.ValidationError('评论内容和附件不能同时为空')
        if attachment_ids:
            qs = CommentAttachment.objects.filter(id__in=attachment_ids, comment__isnull=True)
            if qs.count() != len(set(attachment_ids)):
                raise serializers.ValidationError({'attachmentIds': '存在无效附件或附件已被使用'})
        return attrs

    def create(self, validated_data):
        attachment_ids = validated_data.pop('attachmentIds', [])
        validated_data['body'] = (validated_data.pop('body', '') or '').strip()
        validated_data['content_id'] = self.context['content_id']
        validated_data['author'] = self.context['request'].user
        comment = Comment.objects.create(**validated_data)
        if attachment_ids:
            CommentAttachment.objects.filter(
                id__in=attachment_ids,
                uploaded_by=self.context['request'].user
            ).update(comment=comment)
        return comment


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