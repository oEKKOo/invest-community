from django.contrib import admin
from .models import (
    Asset, Board, Content, ContentAsset, ContentBoard, Comment, Like, Favorite,
    ContentMeta, Poll, PollOption, PollVote, Repost, Mention, ContentAttachment, CommentAttachment
)
from .cache_utils import invalidate_board_tree_cache


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """资产管理（含 Finnhub 行情接入字段）"""
    list_display = ['code', 'name', 'asset_type', 'market', 'status',
                    'finnhub_symbol', 'currency', 'last_sync_at', 'created_at']
    list_filter = ['asset_type', 'market', 'status', 'currency']
    search_fields = ['code', 'name', 'finnhub_symbol', 'industry']
    ordering = ['market', 'code']
    readonly_fields = ['created_at', 'updated_at', 'last_sync_at']

    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'asset_type', 'market', 'status')
        }),
        ('Finnhub 接入', {
            'fields': ('finnhub_symbol', 'exchange', 'currency', 'isin', 'last_sync_at'),
            'description': 'finnhub_symbol 用于调用 Finnhub API，禁止在此处暴露 API Key'
        }),
        ('公司信息', {
            'fields': ('industry', 'logo_url', 'description', 'meta_json'),
            'classes': ('collapse',),
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """板块管理"""
    list_display = ['id', 'name', 'board_type', 'parent', 'status', 'sort_order', 'is_builtin', 'created_at']
    list_filter = ['board_type', 'status', 'is_builtin']
    search_fields = ['name', 'slug', 'industry_code', 'stock_code']
    ordering = ['board_type', 'sort_order', 'id']
    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        invalidate_board_tree_cache()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        invalidate_board_tree_cache()


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    """内容管理"""
    list_display = ['id', 'title', 'author', 'status', 'like_count', 'comment_count', 'created_at']
    list_filter = ['status', 'created_at', 'published_at']
    search_fields = ['title', 'author__username', 'body']
    ordering = ['-created_at']
    readonly_fields = ['like_count', 'comment_count', 'view_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('author', 'title', 'body', 'tags_json')
        }),
        ('状态信息', {
            'fields': ('status', 'reviewed_by', 'reject_reason', 'published_at')
        }),
        ('统计信息', {
            'fields': ('like_count', 'comment_count', 'view_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(ContentAsset)
class ContentAssetAdmin(admin.ModelAdmin):
    """内容资产关联管理"""
    list_display = ['content', 'asset', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content__title', 'asset__code', 'asset__name']


@admin.register(ContentBoard)
class ContentBoardAdmin(admin.ModelAdmin):
    """内容板块关联管理"""
    list_display = ['content', 'board', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content__title', 'board__name', 'board__slug']


@admin.register(ContentAttachment)
class ContentAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_name', 'uploaded_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['original_name', 'uploaded_by__username']


@admin.register(CommentAttachment)
class CommentAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_name', 'uploaded_by', 'comment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['original_name', 'uploaded_by__username']


@admin.register(ContentMeta)
class ContentMetaAdmin(admin.ModelAdmin):
    list_display = ['content', 'content_type', 'format_type', 'repost_count', 'forward_count']
    list_filter = ['content_type', 'format_type']


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ['content', 'question', 'allow_multiple', 'expires_at', 'is_closed']


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ['poll', 'text', 'vote_count', 'sort_order']


@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ['poll', 'option', 'user', 'created_at']


@admin.register(Repost)
class RepostAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'created_at']


@admin.register(Mention)
class MentionAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'source_id', 'from_user', 'to_user', 'created_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """评论管理"""
    list_display = ['id', 'content', 'author', 'parent', 'status', 'like_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['author__username', 'body']
    ordering = ['-created_at']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """点赞管理"""
    list_display = ['user', 'target_type', 'target_id', 'created_at']
    list_filter = ['target_type', 'created_at']
    search_fields = ['user__username']
    ordering = ['-created_at']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """收藏管理"""
    list_display = ['user', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content__title']
    ordering = ['-created_at']