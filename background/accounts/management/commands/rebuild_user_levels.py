from django.core.management.base import BaseCommand

from reports.analytics_service import rebuild_user_levels


class Command(BaseCommand):
    help = '按等级规则重建用户等级'

    def handle(self, *args, **options):
        rebuild_user_levels()
        self.stdout.write(self.style.SUCCESS('用户等级重建完成'))
