from django.contrib import admin
from .models import AssetQuoteSnapshot, AssetKline, DataJobLog


@admin.register(AssetQuoteSnapshot)
class AssetQuoteSnapshotAdmin(admin.ModelAdmin):
    list_display = ['asset', 'price', 'change_amount', 'change_pct', 'quote_time', 'source', 'created_at']
    list_filter = ['source', 'asset__market']
    search_fields = ['asset__code', 'asset__name']
    readonly_fields = ['created_at']
    ordering = ['-quote_time']


@admin.register(AssetKline)
class AssetKlineAdmin(admin.ModelAdmin):
    list_display = ['asset', 'resolution', 'k_time', 'open', 'high', 'low', 'close', 'volume']
    list_filter = ['resolution', 'asset__market']
    search_fields = ['asset__code', 'asset__name']
    readonly_fields = ['created_at']
    ordering = ['asset', 'resolution', '-k_time']


@admin.register(DataJobLog)
class DataJobLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'job_type', 'status', 'market', 'asset_code',
                    'started_at', 'finished_at', 'affected_rows']
    list_filter = ['job_type', 'status']
    search_fields = ['asset_code', 'market', 'error_message']
    readonly_fields = ['started_at', 'finished_at', 'affected_rows', 'error_message', 'extra_info']
    ordering = ['-started_at']
