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
]