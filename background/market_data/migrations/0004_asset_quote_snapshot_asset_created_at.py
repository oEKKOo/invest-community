# AssetList withQuote 子查询按 created_at 取最新快照时的覆盖索引

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market_data', '0003_quote_snapshot_ranking_indexes'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='assetquotesnapshot',
            index=models.Index(fields=['asset', '-created_at'], name='idx_quote_asset_created'),
        ),
    ]
