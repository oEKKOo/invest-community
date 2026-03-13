from django.urls import path

from . import views

urlpatterns = [
    # 会话列表 / 创建
    path('messages/conversations/', views.ConversationListCreateView.as_view(), name='conversation_list'),
    # 某个会话下的消息列表 / 发送
    path(
        'messages/conversations/<int:pk>/messages/',
        views.ConversationMessagesView.as_view(),
        name='conversation_messages',
    ),
    # 标记消息已读
    path('messages/<int:pk>/read/', views.mark_message_read, name='mark_message_read'),
]

