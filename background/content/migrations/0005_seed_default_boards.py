from django.db import migrations


def seed_default_boards(apps, schema_editor):
    Board = apps.get_model('content', 'Board')

    def create_board(name, slug, board_type, parent=None, sort_order=0, **extra):
        board, _ = Board.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'board_type': board_type,
                'parent': parent,
                'sort_order': sort_order,
                'status': 'ACTIVE',
                'is_builtin': True,
                **extra,
            }
        )
        return board

    market_root = create_board('市场讨论区', 'market-discussion', 'MARKET', sort_order=10)
    create_board('A股', 'market-a-share', 'MARKET', parent=market_root, sort_order=11, market='A_SHARE')
    create_board('港股', 'market-hk-stock', 'MARKET', parent=market_root, sort_order=12, market='HK_STOCK')
    create_board('美股', 'market-us-stock', 'MARKET', parent=market_root, sort_order=13, market='US_STOCK')
    create_board('期货', 'market-futures', 'MARKET', parent=market_root, sort_order=14, market='FUTURES')

    theme_root = create_board('主题专区', 'theme-zone', 'THEME', sort_order=20)
    create_board('价值投资专区', 'theme-value-investing', 'THEME', parent=theme_root, sort_order=21)
    create_board('量化投资专区', 'theme-quant-investing', 'THEME', parent=theme_root, sort_order=22)
    create_board('基金投资专区', 'theme-fund-investing', 'THEME', parent=theme_root, sort_order=23)
    create_board('新股/新债讨论', 'theme-ipo-bond', 'THEME', parent=theme_root, sort_order=24)
    create_board('宏观策略研讨', 'theme-macro-strategy', 'THEME', parent=theme_root, sort_order=25)

    company_root = create_board('公司研究专区', 'company-research', 'COMPANY_RESEARCH', sort_order=30)
    industry_root = create_board('按行业分类', 'company-by-industry', 'COMPANY_RESEARCH', parent=company_root, sort_order=31)
    stock_root = create_board('按个股分类', 'company-by-stock', 'COMPANY_RESEARCH', parent=company_root, sort_order=32)
    create_board('科技行业', 'industry-tech', 'COMPANY_RESEARCH', parent=industry_root, sort_order=311, industry_code='TECH')
    create_board('金融行业', 'industry-finance', 'COMPANY_RESEARCH', parent=industry_root, sort_order=312, industry_code='FINANCE')
    create_board('白酒行业', 'industry-consumer-liquor', 'COMPANY_RESEARCH', parent=industry_root, sort_order=313, industry_code='LIQUOR')
    create_board('贵州茅台', 'stock-600519', 'COMPANY_RESEARCH', parent=stock_root, sort_order=321, stock_code='600519')
    create_board('宁德时代', 'stock-300750', 'COMPANY_RESEARCH', parent=stock_root, sort_order=322, stock_code='300750')
    create_board('Apple', 'stock-aapl', 'COMPANY_RESEARCH', parent=stock_root, sort_order=323, stock_code='AAPL')

    qa_root = create_board('问答求助区', 'qa-help-zone', 'QA', sort_order=40)
    create_board('新手提问', 'qa-beginner', 'QA', parent=qa_root, sort_order=41)
    create_board('投资解惑', 'qa-investing-qa', 'QA', parent=qa_root, sort_order=42)


def reverse_seed_default_boards(apps, schema_editor):
    Board = apps.get_model('content', 'Board')
    built_in_slugs = [
        'market-discussion', 'market-a-share', 'market-hk-stock', 'market-us-stock', 'market-futures',
        'theme-zone', 'theme-value-investing', 'theme-quant-investing', 'theme-fund-investing',
        'theme-ipo-bond', 'theme-macro-strategy',
        'company-research', 'company-by-industry', 'company-by-stock', 'industry-tech', 'industry-finance',
        'industry-consumer-liquor', 'stock-600519', 'stock-300750', 'stock-aapl',
        'qa-help-zone', 'qa-beginner', 'qa-investing-qa',
    ]
    Board.objects.filter(slug__in=built_in_slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0004_board_contentboard_content_boards_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_default_boards, reverse_seed_default_boards),
    ]
