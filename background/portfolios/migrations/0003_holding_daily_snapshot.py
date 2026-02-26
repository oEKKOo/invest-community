# Generated migration - 持仓每日快照表

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolios', '0002_add_asset_fk_and_user_holding'),
    ]

    operations = [
        migrations.CreateModel(
            name='HoldingDailySnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='快照日期')),
                ('close_price', models.DecimalField(
                    decimal_places=6, max_digits=18,
                    help_text='来源：AssetKline.close（日K收盘价）',
                    verbose_name='收盘估值价'
                )),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('holding', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_snapshots',
                    to='portfolios.userholding',
                    verbose_name='关联持仓'
                )),
            ],
            options={
                'verbose_name': '持仓每日快照',
                'verbose_name_plural': '持仓每日快照',
                'db_table': 'holding_daily_snapshot',
                'ordering': ['-date'],
            },
        ),
        migrations.AddIndex(
            model_name='holdingdailysnapshot',
            index=models.Index(fields=['holding', '-date'], name='idx_holding_snap_date'),
        ),
        migrations.AlterUniqueTogether(
            name='holdingdailysnapshot',
            unique_together={('holding', 'date')},
        ),
    ]
