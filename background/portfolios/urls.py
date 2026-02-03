from django.urls import path
from . import views

urlpatterns = [
    # 组合相关
    path('portfolios/', views.PortfolioListView.as_view(), name='portfolio_list'),
    path('portfolios/top/', views.portfolio_top, name='portfolio_top'),
    path('portfolios/<int:pk>/', views.portfolio_detail, name='portfolio_detail'),
]