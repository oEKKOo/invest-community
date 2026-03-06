from django.urls import path
from . import views

urlpatterns = [
    # 内容相关
    path('posts/', views.ContentListView.as_view(), name='content_list'),
    path('posts/<int:pk>/', views.content_detail, name='content_detail'),
    path('posts/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    # 评论相关 - 同时支持带斜杠和不带斜杠的版本
    path('posts/<int:pk>/comments/', views.post_comments, name='post_comments'),
    path('posts/<int:pk>/comments', views.post_comments, name='post_comments_no_slash'),
    path('comments/<int:comment_id>/', views.comment_detail, name='comment_detail'),
    path('comments/<int:comment_id>/replies/', views.comment_replies, name='comment_replies'),
    path('comments/<int:comment_id>/like/', views.comment_toggle_like, name='comment_toggle_like'),
    
    # 点赞相关
    path('likes/', views.toggle_like, name='toggle_like'),
    
    # 资产相关
    path('assets/', views.AssetListView.as_view(), name='asset_list'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/posts/', views.asset_posts, name='asset_posts'),
    
    # 管理员功能
    path('admin/posts/', views.AdminPostsView.as_view(), name='admin_posts'),
    path('admin/posts/<int:pk>/status/', views.admin_post_status, name='admin_post_status'),
    
    # Dashboard 和搜索
    path('dashboard/overview/', views.dashboard_overview, name='dashboard_overview'),
    path('search/', views.global_search, name='global_search'),
]