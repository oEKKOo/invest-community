"""
API 请求耗时日志（便于 grep duration_ms / endpoint，与 Django Debug Toolbar 互补）。
环境变量：DJANGO_API_TIMING_LOG=true|false（未设置时：DEBUG=True 则开启）。
"""
from __future__ import annotations

import logging
import os
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from django.conf import settings

logger = logging.getLogger('investhub.api_timing')

F = TypeVar('F', bound=Callable[..., Any])


def api_timing_enabled() -> bool:
    env = os.environ.get('DJANGO_API_TIMING_LOG', '').lower()
    if env in ('1', 'true', 'yes', 'on'):
        return True
    if env in ('0', 'false', 'no', 'off'):
        return False
    return bool(settings.DEBUG)


def log_api_duration(endpoint: str, duration_ms: float, **extra: Any) -> None:
    if not api_timing_enabled():
        return
    suffix = ' '.join(f'{k}={v}' for k, v in extra.items() if v is not None)
    logger.info('api_timing endpoint=%s duration_ms=%.2f %s', endpoint, duration_ms, suffix)


def timed_api(endpoint: str) -> Callable[[F], F]:
    """用于函数视图：记录整段视图逻辑耗时（毫秒）。"""

    def decorator(view_fn: F) -> F:
        @wraps(view_fn)
        def wrapper(request, *args, **kwargs):
            t0 = time.perf_counter()
            try:
                return view_fn(request, *args, **kwargs)
            finally:
                if api_timing_enabled():
                    ms = (time.perf_counter() - t0) * 1000
                    log_api_duration(endpoint, ms, path=getattr(request, 'path', ''))

        return wrapper  # type: ignore[return-value]

    return decorator
