from django.contrib import admin
from .models import Asset, Content, ContentAsset, Comment, Like, Favorite


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """资产管理"""
    list_display = ['code', 'name', 'asset_type', 'market', 'created_at']
    list_filter = ['asset_type', 'market', 'created_at']
    search_fields = ['code', 'name']
    ordering = ['code']


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