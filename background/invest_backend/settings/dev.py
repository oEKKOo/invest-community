from .base import *  # noqa: F401,F403

import os


DEBUG = os.environ.get("DJANGO_DEBUG", "true").strip().lower() in ("1", "true", "yes", "on")
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

try:
    import debug_toolbar  # noqa: F401
except ImportError:
    _DEBUG_TOOLBAR_AVAILABLE = False
else:
    _DEBUG_TOOLBAR_AVAILABLE = True

if DEBUG and _DEBUG_TOOLBAR_AVAILABLE:
    INSTALLED_APPS = list(INSTALLED_APPS) + ["debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + list(MIDDLEWARE)

