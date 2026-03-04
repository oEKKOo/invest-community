from __future__ import annotations

"""
Celery 应用入口（定时任务 / 异步任务基础骨架）

说明：
- 当前项目的行情同步、数据任务逻辑主要集中在 `market_data.tasks` 中，
  这些函数本身是幂等的、可被管理命令 / API / Celery 等多种方式调用。
- 这里提供一个「安全的 Celery 骨架」：
  - 未安装 celery 时不会影响 Django 启动
  - 安装并配置好 broker 后即可直接运行 worker / beat
"""

import os

from django.conf import settings

try:
    from celery import Celery  # type: ignore
except ImportError:
    Celery = None  # type: ignore


if Celery is not None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "invest_backend.settings")

    app = Celery("invest_backend")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()

    @app.task(bind=True)
    def debug_task(self):  # type: ignore[no-redef]
        print(f"Request: {self.request!r}")
else:
    # 提供一个占位符，避免 import 错误
    app = None


__all__ = ("app",)

