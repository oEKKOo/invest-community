"""
迁移：扩展 Asset 模型字段（适配已部分迁移的数据库）
- 数据库中已存在：finnhub_symbol, isin, exchange, currency, status, last_sync_at, meta_json
- 需要新增：industry, logo_url, description, updated_at
- 需要更新 Django state 以匹配现有数据库列（SeparateDatabaseAndState）
- 需要添加新索引（跳过已不存在的旧索引删除操作）
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        # ── 1. 已存在于数据库的字段：只更新 Django state，不执行 DDL ──────────
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # 对全新库执行真实 DDL；已存在该字段的历史库通常已完成此迁移，不会重复执行
                migrations.AddField(
                    model_name='asset',
                    name='status',
                    field=models.CharField(
                        choices=[('ACTIVE', '正常交易'), ('SUSPENDED', '停牌'), ('DELISTED', '退市')],
                        default='ACTIVE', max_length=16, verbose_name='交易状态'
                    ),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='finnhub_symbol',
                    field=models.CharField(
                        max_length=32, null=True, blank=True, unique=True,
                        verbose_name='Finnhub Symbol',
                        help_text='调用 Finnhub API 使用的唯一标识，如 AAPL / 0700.HK'
                    ),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='exchange',
                    field=models.CharField(
                        blank=True, max_length=32, verbose_name='交易所（供应商侧）',
                        help_text='Finnhub 返回的 exchange 字段'
                    ),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='currency',
                    field=models.CharField(blank=True, max_length=8, verbose_name='币种',
                                          help_text='如 CNY/USD/HKD'),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='isin',
                    field=models.CharField(blank=True, max_length=20, verbose_name='ISIN编码'),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='meta_json',
                    field=models.JSONField(blank=True, default=dict, verbose_name='扩展信息'),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='last_sync_at',
                    field=models.DateTimeField(blank=True, null=True, verbose_name='基础信息同步时间'),
                ),
            ],
            state_operations=[
                # 更新 code 字段 state（去掉 unique=True）
                migrations.AlterField(
                    model_name='asset',
                    name='code',
                    field=models.CharField(max_length=20, verbose_name='资产代码'),
                ),
                # 更新 market 字段 state（添加 choices）
                migrations.AlterField(
                    model_name='asset',
                    name='market',
                    field=models.CharField(
                        blank=True, max_length=20, verbose_name='所属市场',
                        choices=[
                            ('SH', '上交所'), ('SZ', '深交所'), ('BJ', '北交所'),
                            ('HK', '港交所'), ('US', '美股'),
                        ]
                    ),
                ),
                # 注册已存在的字段到 Django state
                migrations.AddField(
                    model_name='asset',
                    name='status',
                    field=models.CharField(
                        choices=[('ACTIVE', '正常交易'), ('SUSPENDED', '停牌'), ('DELISTED', '退市')],
                        default='ACTIVE', max_length=16, verbose_name='交易状态'
                    ),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='finnhub_symbol',
                    field=models.CharField(
                        max_length=32, null=True, blank=True, unique=True,
                        verbose_name='Finnhub Symbol',
                        help_text='调用 Finnhub API 使用的唯一标识，如 AAPL / 0700.HK'
                    ),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='exchange',
                    field=models.CharField(
                        blank=True, max_length=32, verbose_name='交易所（供应商侧）',
                        help_text='Finnhub 返回的 exchange 字段'
                    ),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='currency',
                    field=models.CharField(blank=True, max_length=8, verbose_name='币种',
                                          help_text='如 CNY/USD/HKD'),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='isin',
                    field=models.CharField(blank=True, max_length=20, verbose_name='ISIN编码'),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='meta_json',
                    field=models.JSONField(blank=True, default=dict, verbose_name='扩展信息'),
                ),
                migrations.AddField(
                    model_name='asset',
                    name='last_sync_at',
                    field=models.DateTimeField(blank=True, null=True, verbose_name='基础信息同步时间'),
                ),
            ]
        ),

        # ── 2. 数据库中缺失的字段：正常 AddField（执行真实 DDL）─────────────
        migrations.AddField(
            model_name='asset',
            name='industry',
            field=models.CharField(blank=True, max_length=64, verbose_name='所属行业'),
        ),
        migrations.AddField(
            model_name='asset',
            name='logo_url',
            field=models.URLField(blank=True, verbose_name='Logo URL'),
        ),
        migrations.AddField(
            model_name='asset',
            name='description',
            field=models.TextField(blank=True, verbose_name='公司简介'),
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='asset',
                    name='updated_at',
                    field=models.DateTimeField(auto_now=True, verbose_name='更新时间'),
                ),
            ],
        ),

        # ── 3. unique_together 约束（更新 Django state，旧约束 uk_asset_type_code 已存在）
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name='asset',
                    unique_together={('asset_type', 'code', 'market')},
                ),
            ]
        ),

        # ── 4. 旧索引处理（数据库中 asset_code_eb86ae_idx 等已不存在，只更新 state）
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveIndex(
                    model_name='asset',
                    name='asset_code_eb86ae_idx',
                ),
                migrations.RemoveIndex(
                    model_name='asset',
                    name='asset_asset_t_0df6bb_idx',
                ),
            ]
        ),

        # ── 5. 添加新索引（真实 DDL，数据库中尚未存在）──────────────────────
        migrations.AddIndex(
            model_name='asset',
            index=models.Index(fields=['code'], name='idx_asset_code'),
        ),
        migrations.AddIndex(
            model_name='asset',
            index=models.Index(fields=['asset_type'], name='idx_asset_type'),
        ),
        migrations.AddIndex(
            model_name='asset',
            index=models.Index(fields=['market'], name='idx_asset_market'),
        ),
        migrations.AddIndex(
            model_name='asset',
            index=models.Index(fields=['exchange'], name='idx_asset_exchange'),
        ),
        migrations.AddIndex(
            model_name='asset',
            index=models.Index(fields=['status'], name='idx_asset_status'),
        ),
    ]
