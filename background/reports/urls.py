from django.urls import path
from . import views

urlpatterns = [
    # 举报相关
    path('reports/', views.create_report, name='create_report'),
    path('users/me/reports/', views.UserReportsView.as_view(), name='user_reports'),
    
    # 管理员功能
    path('admin/reports/', views.AdminReportsView.as_view(), name='admin_reports'),
    path('admin/reports/<int:pk>/', views.handle_report, name='handle_report'),
    path('admin/stats/', views.admin_stats, name='admin_stats'),
    path('admin/alerts/', views.AdminAlertsView.as_view(), name='admin_alerts'),
    path('admin/alerts/<int:pk>/', views.admin_handle_alert, name='admin_handle_alert'),
    path('admin/moderation/queue/', views.ModerationQueueView.as_view(), name='moderation_queue'),
    path('admin/moderation/queue/<int:pk>/decision/', views.moderation_queue_decision, name='moderation_queue_decision'),
    path('admin/moderation/rules/', views.ModerationRuleView.as_view(), name='moderation_rules'),
    path('admin/moderation/rules/<int:pk>/', views.moderation_rule_update, name='moderation_rule_update'),
    path('admin/moderation/hits/', views.ModerationHitsView.as_view(), name='moderation_hits'),
    path('admin/analytics/activity/', views.analytics_activity, name='analytics_activity'),
    path('admin/analytics/topics/hot/', views.analytics_topics_hot, name='analytics_topics_hot'),
    path('admin/analytics/users/engagement/', views.analytics_users_engagement, name='analytics_users_engagement'),
    path('admin/analytics/dashboard/overview/', views.analytics_dashboard_overview, name='analytics_dashboard_overview'),
]