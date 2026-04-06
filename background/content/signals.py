from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .asset_cache import invalidate_asset_detail_cache
from .models import Asset


@receiver(post_save, sender=Asset)
def _asset_changed_invalidate_cache(sender, instance, **kwargs):
    invalidate_asset_detail_cache(instance.pk)


@receiver(post_delete, sender=Asset)
def _asset_deleted_invalidate_cache(sender, instance, **kwargs):
    invalidate_asset_detail_cache(instance.pk)
