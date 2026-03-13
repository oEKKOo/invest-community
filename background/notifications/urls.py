from django.urls import path
from . import views

urlpatterns = [
    # 通知列表与已读操作
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_read, name='mark_all_read'),

    # 通知 SSE 实时流
    path('notifications/stream/', views.notifications_stream, name='notifications_stream'),
]