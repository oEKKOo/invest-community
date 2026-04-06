# MySQL FULLTEXT on content(title, body); backfill favorite_count from favorite rows.

from django.db import connection, migrations


def _add_fulltext(apps, schema_editor):
    if connection.vendor != 'mysql':
        return
    with connection.cursor() as cursor:
        cursor.execute(
            'ALTER TABLE content ADD FULLTEXT INDEX ft_content_title_body (title, body)'
        )


def _drop_fulltext(apps, schema_editor):
    if connection.vendor != 'mysql':
        return
    with connection.cursor() as cursor:
        cursor.execute('ALTER TABLE content DROP INDEX ft_content_title_body')


def _backfill_favorite_count(apps, schema_editor):
    Content = apps.get_model('content', 'Content')
    Favorite = apps.get_model('content', 'Favorite')
    from django.db.models import Count

    agg = Favorite.objects.values('content_id').annotate(c=Count('id'))
    for row in agg.iterator(chunk_size=500):
        Content.objects.filter(pk=row['content_id']).update(favorite_count=row['c'])


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0009_db_perf_indexes_and_counts'),
    ]

    operations = [
        migrations.RunPython(_add_fulltext, _drop_fulltext),
        migrations.RunPython(_backfill_favorite_count, migrations.RunPython.noop),
    ]
