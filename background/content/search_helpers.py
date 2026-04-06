"""Keyword filters for list/search: MySQL FULLTEXT (MATCH) where available, else icontains."""
from __future__ import annotations

from django.db import connection
from django.db.models import Q, QuerySet


def filter_posts_by_keyword(queryset: QuerySet, q: str) -> QuerySet:
    q = (q or '').strip()
    if not q:
        return queryset
    if connection.vendor == 'mysql':
        # Requires FULLTEXT index ft_content_title_body on content(title, body); see migration 0010.
        return queryset.extra(
            where=['MATCH(title, body) AGAINST (%s IN NATURAL LANGUAGE MODE)'],
            params=[q],
        )
    return queryset.filter(Q(title__icontains=q) | Q(body__icontains=q))


def filter_assets_by_keyword(queryset: QuerySet, q: str) -> QuerySet:
    q = (q or '').strip()
    if not q:
        return queryset
    return queryset.filter(
        Q(code__istartswith=q) | Q(name__icontains=q) | Q(industry__icontains=q)
    )
