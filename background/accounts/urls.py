from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # 认证相关
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.logout, name='logout'),  # 新增logout接口

    # 投资偏好
    path('users/me/invest-profile/', views.invest_profile, name='invest_profile'),

    # 关注流 / 社交 Feed
    path('feed/following/', views.following_feed, name='following_feed'),
    path('feed/following-portfolios/', views.following_portfolios_feed, name='following_portfolios_feed'),
]