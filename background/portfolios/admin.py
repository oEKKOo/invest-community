from django.contrib import admin
from .models import Portfolio, PortfolioAsset


class PortfolioAssetInline(admin.TabularInline):
    """组合资产内联编辑"""
    model = PortfolioAsset
    extra = 1


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """组合管理"""
    list_display = ['id', 'title', 'owner', 'risk_level', 'returns_ytd', 'is_public', 'like_count', 'created_at']
    list_filter = ['risk_level', 'is_public', 'created_at']
    search_fields = ['title', 'owner__username', 'description']
    ordering = ['-created_at']
    readonly_fields = ['like_count', 'created_at', 'updated_at']
    
    inlines = [PortfolioAssetInline]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('owner', 'title', 'description')
        }),
        ('配置信息', {
            'fields': ('risk_level', 'returns_ytd', 'is_public')
        }),
        ('统计信息', {
            'fields': ('like_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(PortfolioAsset)
class PortfolioAssetAdmin(admin.ModelAdmin):
    """组合资产管理"""
    list_display = ['portfolio', 'symbol', 'name', 'allocation', 'created_at']
    list_filter = ['created_at']
    search_fields = ['portfolio__title', 'symbol', 'name']
    ordering = ['-created_at']