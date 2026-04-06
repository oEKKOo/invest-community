"""Print EXPLAIN for common content-related querysets (validate index usage)."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection

from content.models import Asset, Content, Favorite
from content.search_helpers import filter_assets_by_keyword, filter_posts_by_keyword


class Command(BaseCommand):
    help = 'Run EXPLAIN on hot-path querysets (posts list, asset posts, favorites, search filters).'

    def handle(self, *args, **options):
        vendor = connection.vendor
        self.stdout.write(self.style.NOTICE(f'Database vendor: {vendor}\n'))

        def show(label, qs):
            self.stdout.write(self.style.WARNING(f'=== {label} ==='))
            try:
                self.stdout.write(qs.explain(format='text'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'explain failed: {exc}'))
            self.stdout.write('')

        show(
            'content feed PUBLISHED -created_at',
            Content.objects.filter(status='PUBLISHED').order_by('-created_at')[:20],
        )
        show(
            'content hot sort',
            Content.objects.filter(status='PUBLISHED').order_by(
                '-like_count', '-comment_count', '-created_at'
            )[:20],
        )
        asset = Asset.objects.order_by('id').first()
        if asset:
            show(
                'asset discussion posts',
                Content.objects.filter(assets=asset, status='PUBLISHED').order_by(
                    '-created_at'
                )[:20],
            )

        User = get_user_model()
        user = User.objects.order_by('id').first()
        if user:
            show(
                'user favorites by time',
                Favorite.objects.filter(user=user).order_by('-created_at')[:20],
            )

        show(
            'post keyword filter (FULLTEXT on MySQL, icontains fallback)',
            filter_posts_by_keyword(Content.objects.filter(status='PUBLISHED'), '银行')[:20],
        )
        show(
            'asset keyword filter',
            filter_assets_by_keyword(Asset.objects.all(), '000')[:20],
        )

        self.stdout.write(self.style.SUCCESS('Done. Compare key / rows with expectations for your DB.'))
