from django.urls import path
from . import views


urlpatterns = [
    # 用户治理相关（仅 MODERATOR / ADMIN 可用）
    path('users/<int:user_id>/status/', views.admin_update_user_status, name='admin_user_status'),
    path('users/<int:user_id>/mute/', views.admin_mute_user, name='admin_user_mute'),
    path('users/<int:user_id>/ban/', views.admin_ban_user, name='admin_user_ban'),
    path('users/<int:user_id>/unmute/', views.admin_unmute_user, name='admin_user_unmute'),
    path('users/<int:user_id>/unban/', views.admin_unban_user, name='admin_user_unban'),
    path('users/<int:user_id>/warning/', views.admin_warning_user, name='admin_user_warning'),
    path('users/<int:user_id>/points/logs/', views.admin_user_points_logs, name='admin_user_points_logs'),
    path('users/<int:user_id>/points/adjust/', views.admin_adjust_user_points, name='admin_user_points_adjust'),
    path('users/<int:user_id>/behavior-report/', views.admin_user_behavior_report, name='admin_user_behavior_report'),
    path('users/risk/', views.admin_users_risk, name='admin_users_risk'),
    path('users/moderation/', views.admin_moderated_users, name='admin_moderated_users'),
    path('verifications/pending/', views.admin_pending_verifications, name='admin_pending_verifications'),
    path('verifications/real-name/<int:verification_id>/review/', views.admin_review_real_name, name='admin_review_real_name'),
    path('verifications/professional/<int:verification_id>/review/', views.admin_review_professional, name='admin_review_professional'),
]

