from django.urls import path
from . import views

urlpatterns = [
    # 用户资料
    path('me/', views.manage_current_user, name='manage_current_user'),
    path('me/privacy-settings/', views.manage_privacy_settings, name='manage_privacy_settings'),
    path('me/achievements/', views.my_achievements, name='my_achievements'),
    path('<int:user_id>/', views.get_user_profile, name='user_profile'),
    
    # 关注功能
    path('<int:user_id>/follow/', views.manage_follow, name='manage_follow'),
    path('<int:user_id>/followers/', views.UserFollowersView.as_view(), name='user_followers'),
    path('<int:user_id>/following/', views.UserFollowingView.as_view(), name='user_following'),
    
    # 用户收藏列表
    path('me/favorites/', views.UserFavoritesView.as_view(), name='user_favorites'),
    path('me/reports/', views.UserReportsView.as_view(), name='user_reports'),
    path('me/likes/', views.UserLikesView.as_view(), name='user_likes'),
]