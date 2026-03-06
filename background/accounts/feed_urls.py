from django.urls import path
from . import views

urlpatterns = [
    # 关注流 / 社交 Feed（统一挂载到 /api/feed/ 前缀下）
    path('following/', views.following_feed, name='following_feed'),
    path('following-portfolios/', views.following_portfolios_feed, name='following_portfolios_feed'),
    path('following/recommendations/', views.following_recommendations, name='following_recommendations'),
]

