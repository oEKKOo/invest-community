from django.urls import path
from . import views

urlpatterns = [
    # 用户资料
    path('me/', views.get_current_user, name='current_user'),
    path('me/', views.update_profile, name='update_profile'),  # 同一URL，不同HTTP方法
    path('<int:user_id>/', views.get_user_profile, name='user_profile'),
    
    # 关注功能
    path('<int:user_id>/follow/', views.follow_user, name='follow_user'),
    path('<int:user_id>/follow/', views.unfollow_user, name='unfollow_user'),  # 同一URL，不同HTTP方法
    path('<int:user_id>/followers/', views.UserFollowersView.as_view(), name='user_followers'),
    path('<int:user_id>/following/', views.UserFollowingView.as_view(), name='user_following'),
    
    # 用户收藏列表
    path('me/favorites/', views.UserFavoritesView.as_view(), name='user_favorites'),
    path('me/reports/', views.UserReportsView.as_view(), name='user_reports'),
]