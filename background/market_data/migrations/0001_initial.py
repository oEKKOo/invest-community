"""
市场数据初始迁移（适配已部分建表的数据库）
asset_quote_snapshot / asset_kline / data_job_log 表已在数据库中存在，
使用 SeparateDatabaseAndState 只更新 Django 迁移状态，不重复执行 DDL。
"""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('content', '0002_asset_finnhub_fields'),
    ]

    operations = [
        # 三张表已存在，仅更新 Django state，不执行 DDL
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='DataJobLog',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('job_type', models.CharField(choices=[
                            ('SYMBOLS_SYNC', '标的清单同步'),
                            ('KLINE_SYNC', 'K线数据同步'),
                            ('QUOTE_REFRESH', '行情快照刷新'),
                            ('DQ_CHECK', '数据质量校验'),
                        ], max_length=32, verbose_name='任务类型')),
                        ('status', models.CharField(choices=[
                            ('RUNNING', '运行中'),
                            ('SUCCESS', '成功'),
                            ('FAILED', '失败'),
                            ('PARTIAL', '部分成功'),
                        ], default='RUNNING', max_length=16, verbose_name='状态')),
                        ('market', models.CharField(blank=True, help_text='如 CN/HK/US', max_length=16, verbose_name='目标市场')),
                        ('asset_code', models.CharField(blank=True, help_text='单资产任务填此字段', max_length=32, verbose_name='目标资产代码')),
                        ('started_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='开始时间')),
                        ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='结束时间')),
                        ('affected_rows', models.IntegerField(default=0, verbose_name='影响条数')),
                        ('error_message', models.TextField(blank=True, verbose_name='失败原因')),
                        ('extra_info', models.JSONField(blank=True, default=dict, verbose_name='附加信息')),
                    ],
                    options={
                        'verbose_name': '数据任务日志',
                        'verbose_name_plural': '数据任务日志',
                        'db_table': 'data_job_log',
                        'ordering': ['-started_at'],
                    },
                ),
                migrations.CreateModel(
                    name='AssetQuoteSnapshot',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('price', models.DecimalField(blank=True, decimal_places=6, max_digits=18, null=True, verbose_name='最新价')),
                        ('change_amount', models.DecimalField(blank=True, decimal_places=6, max_digits=18, null=True, verbose_name='涨跌额')),
                        ('change_pct', models.DecimalField(blank=True, decimal_places=4, max_digits=9, null=True, verbose_name='涨跌幅(%)')),
                        ('open', models.DecimalField(blank=True, decimal_places=6, max_digits=18, null=True, verbose_name='开盘价')),
                        ('high', models.DecimalField(blank=True, decimal_places=6, max_digits=18, null=True, verbose_name='最高价')),
                        ('low', models.DecimalField(blank=True, decimal_places=6, max_digits=18, null=True, verbose_name='最低价')),
                        ('prev_close', models.DecimalField(blank=True, decimal_places=6, max_digits=18, null=True, verbose_name='昨收价')),
                        ('volume', models.BigIntegerField(blank=True, null=True, verbose_name='成交量')),
                        ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name='成交额')),
                        ('quote_time', models.DateTimeField(blank=True, null=True, verbose_name='行情时间')),
                        ('source', models.CharField(default='finnhub', max_length=16, verbose_name='数据来源')),
                        ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='写入时间')),
                        ('asset', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='quote_snapshots',
                            to='content.asset',
                            verbose_name='资产'
                        )),
                    ],
                    options={
                        'verbose_name': '行情快照',
                        'verbose_name_plural': '行情快照',
                        'db_table': 'asset_quote_snapshot',
                        'ordering': ['-quote_time'],
                    },
                ),
                migrations.CreateModel(
                    name='AssetKline',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('resolution', models.CharField(choices=[
                            ('1', '1分钟'), ('5', '5分钟'), ('15', '15分钟'), ('30', '30分钟'),
                            ('60', '60分钟'), ('D', '日K'), ('W', '周K'), ('M', '月K'),
                        ], default='D', max_length=8, verbose_name='周期')),
                        ('k_time', models.DateTimeField(verbose_name='K线时间点')),
                        ('open', models.DecimalField(decimal_places=6, max_digits=18, verbose_name='开盘价')),
                        ('high', models.DecimalField(decimal_places=6, max_digits=18, verbose_name='最高价')),
                        ('low', models.DecimalField(decimal_places=6, max_digits=18, verbose_name='最低价')),
                        ('close', models.DecimalField(decimal_places=6, max_digits=18, verbose_name='收盘价')),
                        ('volume', models.BigIntegerField(blank=True, null=True, verbose_name='成交量')),
                        ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='写入时间')),
                        ('asset', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='klines',
                            to='content.asset',
                            verbose_name='资产'
                        )),
                    ],
                    options={
                        'verbose_name': 'K线数据',
                        'verbose_name_plural': 'K线数据',
                        'db_table': 'asset_kline',
                    },
                ),
                # 注册已存在的索引到 Django state（使用数据库实际的索引名）
                migrations.AddIndex(
                    model_name='assetquotesnapshot',
                    index=models.Index(fields=['asset', '-quote_time'], name='idx_aqs_asset_time'),
                ),
                migrations.AddIndex(
                    model_name='assetquotesnapshot',
                    index=models.Index(fields=['-quote_time'], name='idx_aqs_time'),
                ),
                migrations.AddIndex(
                    model_name='assetkline',
                    index=models.Index(fields=['asset', 'resolution', '-k_time'], name='idx_kline_asset_res_time'),
                ),
                migrations.AlterUniqueTogether(
                    name='assetkline',
                    unique_together={('asset', 'resolution', 'k_time')},
                ),
            ]
        ),

        # data_job_log 索引：数据库中没有，正常添加
        migrations.AddIndex(
            model_name='datajoblog',
            index=models.Index(fields=['job_type', '-started_at'], name='idx_job_type_time'),
        ),
        migrations.AddIndex(
            model_name='datajoblog',
            index=models.Index(fields=['status', '-started_at'], name='idx_job_status_time'),
        ),
    ]
