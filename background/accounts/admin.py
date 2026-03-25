from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, UserInvestProfile, UserFollow, UserModerationLog,
    UserSocialAccount, UserVerificationCode, UserRealNameVerification,
    UserProfessionalVerification, RiskQuestionnaireTemplate, RiskQuestionnaireSubmission,
)


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
                'phone_verified',
                'email_verified',
                'identity_level',
                'real_name_status',
                'professional_status',
                'risk_assessment_status',
                'risk_level',
                'v_badge',
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


@admin.register(UserSocialAccount)
class UserSocialAccountAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'provider', 'provider_uid', 'created_at']
    list_filter = ['provider', 'created_at']
    search_fields = ['user__username', 'provider_uid', 'unionid', 'openid']
    ordering = ['-created_at']


@admin.register(UserVerificationCode)
class UserVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'target', 'channel', 'purpose', 'status', 'expires_at', 'created_at']
    list_filter = ['channel', 'purpose', 'status', 'created_at']
    search_fields = ['target', 'code']
    ordering = ['-created_at']


@admin.register(UserRealNameVerification)
class UserRealNameVerificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'real_name', 'status', 'reviewed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'real_name', 'id_card_no_masked']
    ordering = ['-created_at']


@admin.register(UserProfessionalVerification)
class UserProfessionalVerificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'reviewed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'reject_reason']
    ordering = ['-created_at']


@admin.register(RiskQuestionnaireTemplate)
class RiskQuestionnaireTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'version', 'title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['version', 'title']
    ordering = ['-created_at']


@admin.register(RiskQuestionnaireSubmission)
class RiskQuestionnaireSubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'template', 'risk_level', 'score', 'created_at']
    list_filter = ['risk_level', 'created_at']
    search_fields = ['user__username', 'template__version']
    ordering = ['-created_at']