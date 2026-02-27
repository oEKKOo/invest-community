from django.urls import path
from . import views

urlpatterns = [
    # 投资组合
    path('portfolios/', views.PortfolioListView.as_view(), name='portfolio_list'),
    path('portfolios/top/', views.portfolio_top, name='portfolio_top'),
    path('portfolios/<int:pk>/', views.portfolio_detail, name='portfolio_detail'),

    # 个人持仓
    path('holdings/', views.UserHoldingListView.as_view(), name='holding_list'),
    path('holdings/<int:pk>/', views.UserHoldingDetailView.as_view(), name='holding_detail'),

    # 持仓收益（基于每日快照）
    path('holdings/performance/', views.HoldingPerformanceView.as_view(), name='holding_performance'),

    # 持仓累计收益历史（净值曲线）
    path('holdings/returns-history/', views.HoldingReturnsHistoryView.as_view(), name='holding_returns_history'),
]
