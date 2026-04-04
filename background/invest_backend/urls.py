"""invest_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass

urlpatterns += [
    # API endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/users/', include('accounts.user_urls')),
    path('api/feed/', include('accounts.feed_urls')),

    # 管理员专用用户治理接口：/api/admin/...
    path('api/admin/', include('accounts.admin_urls')),

    path('api/', include('content.urls')),
    path('api/', include('portfolios.urls')),
    path('api/', include('notifications.urls')),
    path('api/', include('reports.urls')),
    path('api/', include('messages.urls')),
    path('api/', include('groups.urls')),

    # 行情数据模块（Finnhub 接入）
    # 路由优先级说明：
    #   market_data.urls 中的 /api/assets/<pk>/quote/ 等路由
    #   与 content.urls 中的 /api/assets/<pk>/ 共存，通过不同后缀区分
    path('api/', include('market_data.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)