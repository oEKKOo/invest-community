from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserInvestProfile, UserFollow, UserModerationLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理后台"""
    list_display = ['id', 'username', 'email', 'display_name', 'role', 'status', 'is_active', 'created_at']
    list_filter = ['role', 'status', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'display_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email', 'phone', 'display_name', 'avatar_url', 'bio')}),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'role',
                'status',
                'mute_until',
                'groups',
                'user_permissions',
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'created_at')}),
        (_('Statistics'), {'fields': ('followers_count', 'following_count')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['created_at']


@admin.register(UserInvestProfile)
class UserInvestProfileAdmin(admin.ModelAdmin):
    """用户投资偏好管理"""
    list_display = ['user', 'risk_level', 'horizon', 'created_at']
    list_filter = ['risk_level', 'horizon', 'created_at']
    search_fields = ['user__username', 'user__display_name']
    ordering = ['-created_at']


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    """用户关注关系管理"""
    list_display = ['follower', 'followee', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'followee__username']
    ordering = ['-created_at']


@admin.register(UserModerationLog)
class UserModerationLogAdmin(admin.ModelAdmin):
    """用户治理日志管理"""
    list_display = ['id', 'user', 'action', 'operator', 'expire_at', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'operator__username', 'reason']
    ordering = ['-created_at']