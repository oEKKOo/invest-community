from django.urls import path
from . import views

urlpatterns = [
    # ── 资产行情接口 ──────────────────────────────────────────────
    # 6.4 单资产最新行情
    path('assets/<int:pk>/quote/', views.asset_quote, name='asset_quote'),
    # 6.5 K 线数据
    path('assets/<int:pk>/kline/', views.asset_kline, name='asset_kline'),
    # 6.6 分时数据
    path('assets/<int:pk>/intraday/', views.asset_intraday, name='asset_intraday'),
    # 6.7 批量行情（collection route，注意路径不带 pk）
    path('assets/quotes/', views.asset_quotes_bulk, name='asset_quotes_bulk'),
    # 6.8 行情 SSE 推送
    path('assets/<int:pk>/quote/stream/', views.asset_quote_stream, name='asset_quote_stream'),
    # 资产内容聚合（通用版，兼容 /posts/）
    path('assets/<int:pk>/contents/', views.asset_contents, name='asset_contents'),

    # ── 行情榜单 ──────────────────────────────────────────────────
    path('market/rankings/', views.market_rankings, name='market_rankings'),

    # ── 后台数据任务监控 ──────────────────────────────────────────
    path('market/status/', views.market_status, name='market_status'),
    path('market/jobs/', views.job_log_list, name='job_log_list'),
    path('market/jobs/trigger/', views.trigger_job, name='trigger_job'),
]
