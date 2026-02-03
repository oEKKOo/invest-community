from django.contrib import admin
from .models import Report, Alert


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """举报管理"""
    list_display = ['id', 'reporter', 'target_type', 'target_id', 'status', 'handled_by', 'created_at']
    list_filter = ['target_type', 'status', 'created_at']
    search_fields = ['reporter__username', 'reason']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'handle_time']
    
    fieldsets = (
        ('举报信息', {
            'fields': ('reporter', 'target_type', 'target_id', 'reason')
        }),
        ('处理信息', {
            'fields': ('status', 'handled_by', 'handle_result', 'handle_time')
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """告警管理"""
    list_display = ['id', 'alert_type', 'title', 'severity', 'status', 'handled_by', 'created_at']
    list_filter = ['alert_type', 'severity', 'status', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'handle_time']