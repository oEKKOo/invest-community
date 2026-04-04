# 榜单接口 /api/market/rankings/ 对 asset_quote_snapshot 按 change_pct、volume 排序时的索引

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market_data', '0002_add_perf_indexes'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='assetquotesnapshot',
            index=models.Index(fields=['-change_pct'], name='idx_quote_change_pct'),
        ),
        migrations.AddIndex(
            model_name='assetquotesnapshot',
            index=models.Index(fields=['-volume'], name='idx_quote_volume'),
        ),
    ]
