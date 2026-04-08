from django.contrib import admin

from .models import (
    Group,
    GroupFile,
    GroupInvite,
    GroupJoinRequest,
    GroupMember,
    GroupPost,
    GroupReviewer,
)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'visibility', 'status', 'owner',
        'member_count', 'post_count', 'file_count', 'created_at',
    ]
    list_filter = ['visibility', 'status', 'created_at']
    search_fields = ['name', 'slug', 'description', 'owner__username', 'owner__display_name']
    ordering = ['-created_at']


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'user', 'role', 'status', 'joined_at', 'left_at']
    list_filter = ['role', 'status', 'joined_at']
    search_fields = ['group__name', 'user__username', 'user__display_name']
    ordering = ['-joined_at']


@admin.register(GroupJoinRequest)
class GroupJoinRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'user', 'status', 'reviewed_by', 'created_at', 'reviewed_at']
    list_filter = ['status', 'created_at', 'reviewed_at']
    search_fields = ['group__name', 'user__username', 'user__display_name', 'message', 'review_note']
    ordering = ['-created_at']


@admin.register(GroupReviewer)
class GroupReviewerAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['group__name', 'user__username', 'user__display_name']
    ordering = ['-created_at']


@admin.register(GroupInvite)
class GroupInviteAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'inviter', 'invitee', 'status', 'created_at', 'responded_at']
    list_filter = ['status', 'created_at', 'responded_at']
    search_fields = ['group__name', 'inviter__username', 'invitee__username', 'message']
    ordering = ['-created_at']


@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'author', 'content_type', 'status', 'like_count', 'comment_count', 'created_at']
    list_filter = ['content_type', 'status', 'created_at']
    search_fields = ['group__name', 'author__username', 'title', 'body']
    ordering = ['-created_at']


@admin.register(GroupFile)
class GroupFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'uploaded_by', 'original_name', 'status', 'file_size', 'created_at']
    list_filter = ['status', 'visibility', 'created_at']
    search_fields = ['group__name', 'uploaded_by__username', 'original_name', 'mime_type']
    ordering = ['-created_at']
