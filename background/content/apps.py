from django.apps import AppConfig


class ContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content'

    def ready(self):
        # noqa: F401 — 注册 Asset 缓存失效信号
        from . import signals  # noqa: F401