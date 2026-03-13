from django.urls import path
from . import views


urlpatterns = [
    # 用户治理相关（仅 MODERATOR / ADMIN 可用）
    path('users/<int:user_id>/status/', views.admin_update_user_status, name='admin_user_status'),
    path('users/<int:user_id>/mute/', views.admin_mute_user, name='admin_user_mute'),
    path('users/<int:user_id>/ban/', views.admin_ban_user, name='admin_user_ban'),
    path('users/<int:user_id>/unmute/', views.admin_unmute_user, name='admin_user_unmute'),
    path('users/<int:user_id>/unban/', views.admin_unban_user, name='admin_user_unban'),
    path('users/moderation/', views.admin_moderated_users, name='admin_moderated_users'),
]

