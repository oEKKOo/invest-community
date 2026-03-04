"""
项目级初始化：
- 安装 PyMySQL 以兼容 MySQL
- 暴露 Celery app（若已安装 celery，则可直接 `celery -A invest_backend worker`）
"""

# 使用 PyMySQL 替代 mysqlclient（纯 Python 实现，无需编译）
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    pass

try:
    from .celery import app as celery_app  # type: ignore[F401]
except Exception:
    # 未安装 celery 或 broker 未配置时，不影响 Django 正常启动
    celery_app = None  # type: ignore[assignment]

__all__ = ("celery_app",)

