from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Python 包路径
    name = 'messages'
    # 避免与 Django 内置 `django.contrib.messages` 冲突的应用标签
    label = 'private_messages'
    verbose_name = '私信与会话'

