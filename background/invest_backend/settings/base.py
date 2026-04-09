from pathlib import Path
from datetime import timedelta
import os


def _str_to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _str_to_list(value: str, default: list[str] | None = None) -> list[str]:
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


BASE_DIR = Path(__file__).resolve().parent.parent.parent
_WHITENOISE_AVAILABLE = False
try:
    import whitenoise  # type: ignore  # noqa: F401
except ImportError:
    _WHITENOISE_AVAILABLE = False
else:
    _WHITENOISE_AVAILABLE = True

# Load .env if present; fallback to simple parser.
_env_file = BASE_DIR / ".env"
try:
    from dotenv import load_dotenv as _load_dotenv  # type: ignore

    if _env_file.exists():
        _load_dotenv(str(_env_file), override=True)
except ImportError:
    if _env_file.exists():
        with open(_env_file, encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ[_k.strip()] = _v.strip()


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-your-secret-key-here-change-in-production",
)
DEBUG = _str_to_bool(os.environ.get("DJANGO_DEBUG"), default=False)
ALLOWED_HOSTS = _str_to_list(os.environ.get("DJANGO_ALLOWED_HOSTS"), default=[])
CSRF_TRUSTED_ORIGINS = _str_to_list(os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS"), default=[])

APPEND_SLASH = False

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "accounts",
    "content",
    "portfolios",
    "notifications",
    "reports",
    "market_data",
    "messages",
    "groups",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if _WHITENOISE_AVAILABLE:
    MIDDLEWARE.insert(2, "whitenoise.middleware.WhiteNoiseMiddleware")

INTERNAL_IPS = ["127.0.0.1", "::1"]

ROOT_URLCONF = "invest_backend.urls"
WSGI_APPLICATION = "invest_backend.wsgi.application"
ASGI_APPLICATION = "invest_backend.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

def _db_env(django_key: str, legacy_key: str, default: str = "") -> str:
    """Prefer DJANGO_DB_* (explicit); fall back to README / setup 脚本里的 DB_*。"""
    v = os.environ.get(django_key)
    if v is not None and str(v).strip() != "":
        return v
    return os.environ.get(legacy_key, default)


def _db_ssl_enabled() -> bool:
    value = _db_env("DJANGO_DB_SSL", "DB_SSL", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _db_ssl_mode() -> str:
    return _db_env("DJANGO_DB_SSL_MODE", "DB_SSL_MODE", "").strip().upper()


def _db_ssl_ca() -> str:
    return _db_env("DJANGO_DB_SSL_CA", "DB_SSL_CA", "").strip()


DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    try:
        import dj_database_url  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "DATABASE_URL is set but 'dj-database-url' is not installed. "
            "Run 'pip install dj-database-url' or remove DATABASE_URL."
        ) from exc
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    db_options = {
        "charset": "utf8mb4",
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    }
    db_ssl_mode = _db_ssl_mode()
    db_ssl_ca = _db_ssl_ca()
    if _db_ssl_enabled() or db_ssl_mode or db_ssl_ca:
        # PyMySQL 需要非空 ssl 配置才会真正启用 TLS 连接。
        ssl_options = {"fake_flag_to_enable_tls": True}
        if db_ssl_ca:
            ssl_options["ca"] = db_ssl_ca
        db_options["ssl"] = ssl_options
    if db_ssl_mode in {"VERIFY_CA", "VERIFY_IDENTITY"}:
        db_options["ssl_verify_cert"] = True
    if db_ssl_mode == "VERIFY_IDENTITY":
        db_options["ssl_verify_identity"] = True

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": _db_env("DJANGO_DB_NAME", "DB_NAME", "community_db"),
            "USER": _db_env("DJANGO_DB_USER", "DB_USER", "root"),
            "PASSWORD": _db_env("DJANGO_DB_PASSWORD", "DB_PASSWORD", ""),
            "HOST": _db_env("DJANGO_DB_HOST", "DB_HOST", "127.0.0.1"),
            "PORT": _db_env("DJANGO_DB_PORT", "DB_PORT", "3306"),
            "OPTIONS": db_options,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
if _WHITENOISE_AVAILABLE:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "EXCEPTION_HANDLER": "invest_backend.exception_handler.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
}

WECHAT_APP_ID = os.environ.get("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "")
WECHAT_REDIRECT_URI = os.environ.get("WECHAT_REDIRECT_URI", "")
WEIBO_CLIENT_ID = os.environ.get("WEIBO_CLIENT_ID", "")
WEIBO_CLIENT_SECRET = os.environ.get("WEIBO_CLIENT_SECRET", "")
WEIBO_REDIRECT_URI = os.environ.get("WEIBO_REDIRECT_URI", "")

CORS_ALLOWED_ORIGINS = _str_to_list(os.environ.get("CORS_ALLOWED_ORIGINS"), default=[])
CORS_ALLOW_CREDENTIALS = _str_to_bool(os.environ.get("CORS_ALLOW_CREDENTIALS"), default=True)

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.qq.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 465))
EMAIL_USE_TLS = _str_to_bool(os.environ.get("EMAIL_USE_TLS"), default=False)
EMAIL_USE_SSL = _str_to_bool(os.environ.get("EMAIL_USE_SSL"), default=True)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
EMAIL_FROM = os.environ.get("EMAIL_FROM", DEFAULT_FROM_EMAIL)
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", 10))

SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "MOCK")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_PHONE = os.environ.get("TWILIO_FROM_PHONE", "")
SMS_HTTP_URL = os.environ.get("SMS_HTTP_URL", "")
SMS_HTTP_TOKEN = os.environ.get("SMS_HTTP_TOKEN", "")

FINNHUB_API_KEY_CONFIGURED = bool(os.environ.get("FINNHUB_API_KEY", ""))
FINNHUB_QUOTE_CACHE_TTL = int(os.environ.get("FINNHUB_QUOTE_CACHE_TTL", 60))
MARKET_DATA_SNAPSHOT_RETENTION_DAYS = int(os.environ.get("MARKET_DATA_SNAPSHOT_RETENTION_DAYS", 7))
QUOTE_REFRESH_POPULAR_TOP_N = int(os.environ.get("QUOTE_REFRESH_POPULAR_TOP_N", 20))
DASHBOARD_OVERVIEW_CACHE_TTL = int(os.environ.get("DASHBOARD_OVERVIEW_CACHE_TTL", 60))
MARKET_RANKINGS_CACHE_TTL = int(os.environ.get("MARKET_RANKINGS_CACHE_TTL", 120))
KLINE_API_CACHE_TTL = int(os.environ.get("KLINE_API_CACHE_TTL", 60))
KLINE_DEFAULT_LIMIT = int(os.environ.get("KLINE_DEFAULT_LIMIT", 90))
KLINE_MAX_LIMIT = int(os.environ.get("KLINE_MAX_LIMIT", 500))
BULK_QUOTES_CACHE_TTL = int(os.environ.get("BULK_QUOTES_CACHE_TTL", 30))
QUOTE_REFRESH_FH_DB_BATCH_SIZE = int(os.environ.get("QUOTE_REFRESH_FH_DB_BATCH_SIZE", 200))
ASSET_DETAIL_STATIC_CACHE_TTL = int(os.environ.get("ASSET_DETAIL_STATIC_CACHE_TTL", 600))
GLOBAL_SEARCH_CACHE_TTL = int(os.environ.get("GLOBAL_SEARCH_CACHE_TTL", 20))
ADMIN_STATS_CACHE_TTL = int(os.environ.get("ADMIN_STATS_CACHE_TTL", 45))
BOARD_TREE_CACHE_TTL = int(os.environ.get("BOARD_TREE_CACHE_TTL", 90))
PORTFOLIO_METRICS_CACHE_TTL = int(os.environ.get("PORTFOLIO_METRICS_CACHE_TTL", 120))
HOLDING_RETURNS_HISTORY_DEFAULT_DAYS = int(os.environ.get("HOLDING_RETURNS_HISTORY_DEFAULT_DAYS", 365))
HOLDING_RETURNS_HISTORY_MAX_DAYS = int(os.environ.get("HOLDING_RETURNS_HISTORY_MAX_DAYS", 3650))

TUSHARE_API_TOKEN_CONFIGURED = bool(os.environ.get("TUSHARE_API_TOKEN", ""))
TUSHARE_QUOTE_CACHE_TTL = int(os.environ.get("TUSHARE_QUOTE_CACHE_TTL", 300))
TUSHARE_REQUEST_DELAY = float(os.environ.get("TUSHARE_REQUEST_DELAY", 0.4))

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1")
USE_REDIS_CONFIGURED = _str_to_bool(os.environ.get("USE_REDIS"), default=False)
VIEW_COUNT_USE_REDIS_BUFFER = (
    _str_to_bool(os.environ.get("VIEW_COUNT_USE_REDIS_BUFFER"), default=False)
    and USE_REDIS_CONFIGURED
)

if USE_REDIS_CONFIGURED:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "invest_market",
            "TIMEOUT": 60,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "invest-market-cache",
        }
    }

LOG_DIR = os.environ.get("DJANGO_LOG_DIR", str(BASE_DIR))
LOG_FILE = os.path.join(LOG_DIR, "django.log")
ENABLE_FILE_LOG = _str_to_bool(os.environ.get("DJANGO_ENABLE_FILE_LOG"), default=False)
LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "INFO")

_handlers = {
    "console": {
        "level": LOG_LEVEL,
        "class": "logging.StreamHandler",
        "formatter": "verbose",
    }
}
if ENABLE_FILE_LOG:
    _handlers["file"] = {
        "level": "INFO",
        "class": "logging.FileHandler",
        "filename": LOG_FILE,
        "formatter": "verbose",
    }

_root_handlers = ["console"] + (["file"] if ENABLE_FILE_LOG else [])

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": _handlers,
    "root": {
        "handlers": _root_handlers,
        "level": LOG_LEVEL,
    },
    "loggers": {
        "investhub.api_timing": {
            "handlers": _root_handlers,
            "level": "INFO",
            "propagate": False,
        },
    },
}

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = _str_to_bool(os.environ.get("CELERY_TASK_ALWAYS_EAGER"), default=False)
CELERY_TIMEZONE = TIME_ZONE

try:
    from datetime import timedelta as _celery_td
    from celery.schedules import crontab as _celery_crontab
except ImportError:
    CELERY_BEAT_SCHEDULE = {}
else:
    CELERY_BEAT_SCHEDULE = {
        "market-quote-popular": {
            "task": "market_data.celery_tasks.quote_refresh_popular_task",
            "schedule": _celery_td(minutes=2),
        },
        "market-kline-sync-daily": {
            "task": "market_data.celery_tasks.kline_sync_daily_task",
            "schedule": _celery_crontab(hour=17, minute=30),
        },
        "portfolios-fill-holding-snapshots": {
            "task": "market_data.celery_tasks.fill_holding_snapshots_task",
            "schedule": _celery_crontab(hour=18, minute=0),
        },
        "market-cleanup-quote-snapshots": {
            "task": "market_data.celery_tasks.cleanup_quote_snapshots_task",
            "schedule": _celery_crontab(hour=3, minute=15),
        },
    }
