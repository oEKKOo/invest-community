"""
Legacy compatibility module.

The active settings now live in:
- invest_backend.settings.base
- invest_backend.settings.dev
- invest_backend.settings.prod
"""

from invest_backend.settings.dev import *  # noqa: F401,F403