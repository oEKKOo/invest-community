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
    path('posts/<int:pk>/repost/', views.toggle_repost, name='toggle_repost'),
    path('posts/<int:pk>/poll/vote/', views.post_poll_vote, name='post_poll_vote'),
    path('posts/<int:pk>/poll/result/', views.post_poll_result, name='post_poll_result'),
    
    # 资产相关
    path('assets/', views.AssetListView.as_view(), name='asset_list'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/posts/', views.asset_posts, name='asset_posts'),
    path('boards/', views.BoardListView.as_view(), name='board_list'),
    
    # 管理员功能
    path('admin/posts/', views.AdminPostsView.as_view(), name='admin_posts'),
    path('admin/posts/<int:pk>/status/', views.admin_post_status, name='admin_post_status'),
    path('admin/boards/', views.AdminBoardListCreateView.as_view(), name='admin_board_list_create'),
    path('admin/boards/<int:pk>/', views.admin_board_detail, name='admin_board_detail'),
    path('admin/attachments/', views.admin_attachment_list, name='admin_attachment_list'),
    path('admin/attachments/<int:attachment_id>/status/', views.admin_attachment_status, name='admin_attachment_status'),
    path('uploads/content/', views.upload_content_attachment, name='upload_content_attachment'),
    path('uploads/comment/', views.upload_comment_attachment, name='upload_comment_attachment'),
    path('attachments/<int:attachment_id>/download/', views.download_content_attachment, name='download_content_attachment'),
    
    # Dashboard 和搜索
    path('dashboard/overview/', views.dashboard_overview, name='dashboard_overview'),
    path('search/', views.global_search, name='global_search'),
]