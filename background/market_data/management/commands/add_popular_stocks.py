"""
Django 管理命令：一键添加热门股票到数据库（美股 + A股 精选）

用法：
  python manage.py add_popular_stocks              # 添加全部热门股票
  python manage.py add_popular_stocks --market US  # 只添加美股
  python manage.py add_popular_stocks --market CN  # 只添加A股
  python manage.py add_popular_stocks --quote      # 添加后立即刷新行情快照

完成后执行：
  python manage.py sync_market_data --task quote   # 刷新所有资产行情

注意：此命令包含 200+ 只精选美股，如需导入全量美股（数千只），请使用：
  python manage.py import_us_stocks --limit 500 --quote
"""
from django.core.management.base import BaseCommand


# ── 美股精选（科技 + 金融 + 消费 + 医疗 + 能源 + ETF，共 200+ 只） ──────────────
US_STOCKS = [
    # ── 科技七巨头 ──
    {'code': 'AAPL',  'name': 'Apple Inc.',              'finnhub_symbol': 'AAPL',  'sector': '科技'},
    {'code': 'MSFT',  'name': 'Microsoft Corporation',   'finnhub_symbol': 'MSFT',  'sector': '科技'},
    {'code': 'GOOGL', 'name': 'Alphabet Inc. (Class A)', 'finnhub_symbol': 'GOOGL', 'sector': '科技'},
    {'code': 'GOOG',  'name': 'Alphabet Inc. (Class C)', 'finnhub_symbol': 'GOOG',  'sector': '科技'},
    {'code': 'AMZN',  'name': 'Amazon.com Inc.',         'finnhub_symbol': 'AMZN',  'sector': '科技'},
    {'code': 'NVDA',  'name': 'NVIDIA Corporation',      'finnhub_symbol': 'NVDA',  'sector': '科技'},
    {'code': 'META',  'name': 'Meta Platforms Inc.',     'finnhub_symbol': 'META',  'sector': '科技'},
    {'code': 'TSLA',  'name': 'Tesla Inc.',              'finnhub_symbol': 'TSLA',  'sector': '科技'},
    # ── 金融 ──
    {'code': 'BRK.B', 'name': 'Berkshire Hathaway B',   'finnhub_symbol': 'BRK.B', 'sector': '金融'},
    {'code': 'JPM',   'name': 'JPMorgan Chase & Co.',   'finnhub_symbol': 'JPM',   'sector': '金融'},
    {'code': 'V',     'name': 'Visa Inc.',               'finnhub_symbol': 'V',     'sector': '金融'},
    {'code': 'MA',    'name': 'Mastercard Inc.',         'finnhub_symbol': 'MA',    'sector': '金融'},
    {'code': 'GS',    'name': 'Goldman Sachs Group',     'finnhub_symbol': 'GS',    'sector': '金融'},
    {'code': 'MS',    'name': 'Morgan Stanley',          'finnhub_symbol': 'MS',    'sector': '金融'},
    {'code': 'BAC',   'name': 'Bank of America Corp.',  'finnhub_symbol': 'BAC',   'sector': '金融'},
    {'code': 'WFC',   'name': 'Wells Fargo & Company',  'finnhub_symbol': 'WFC',   'sector': '金融'},
    {'code': 'C',     'name': 'Citigroup Inc.',          'finnhub_symbol': 'C',     'sector': '金融'},
    {'code': 'AXP',   'name': 'American Express Company','finnhub_symbol': 'AXP',   'sector': '金融'},
    {'code': 'BLK',   'name': 'BlackRock Inc.',          'finnhub_symbol': 'BLK',   'sector': '金融'},
    {'code': 'SCHW',  'name': 'Charles Schwab Corp.',   'finnhub_symbol': 'SCHW',  'sector': '金融'},
    {'code': 'SPGI',  'name': 'S&P Global Inc.',         'finnhub_symbol': 'SPGI',  'sector': '金融'},
    {'code': 'MCO',   'name': "Moody's Corporation",     'finnhub_symbol': 'MCO',   'sector': '金融'},
    # ── 半导体 ──
    {'code': 'TSM',   'name': 'Taiwan Semiconductor',   'finnhub_symbol': 'TSM',   'sector': '半导体'},
    {'code': 'AMD',   'name': 'Advanced Micro Devices',  'finnhub_symbol': 'AMD',   'sector': '半导体'},
    {'code': 'INTC',  'name': 'Intel Corporation',       'finnhub_symbol': 'INTC',  'sector': '半导体'},
    {'code': 'AVGO',  'name': 'Broadcom Inc.',           'finnhub_symbol': 'AVGO',  'sector': '半导体'},
    {'code': 'QCOM',  'name': 'Qualcomm Inc.',           'finnhub_symbol': 'QCOM',  'sector': '半导体'},
    {'code': 'TXN',   'name': 'Texas Instruments Inc.',  'finnhub_symbol': 'TXN',   'sector': '半导体'},
    {'code': 'MU',    'name': 'Micron Technology Inc.',  'finnhub_symbol': 'MU',    'sector': '半导体'},
    {'code': 'AMAT',  'name': 'Applied Materials Inc.',  'finnhub_symbol': 'AMAT',  'sector': '半导体'},
    {'code': 'LRCX',  'name': 'Lam Research Corporation','finnhub_symbol': 'LRCX',  'sector': '半导体'},
    {'code': 'KLAC',  'name': 'KLA Corporation',         'finnhub_symbol': 'KLAC',  'sector': '半导体'},
    {'code': 'MRVL',  'name': 'Marvell Technology Inc.', 'finnhub_symbol': 'MRVL',  'sector': '半导体'},
    {'code': 'ON',    'name': 'ON Semiconductor Corp.',  'finnhub_symbol': 'ON',    'sector': '半导体'},
    # ── 软件 & 云计算 ──
    {'code': 'CRM',   'name': 'Salesforce Inc.',         'finnhub_symbol': 'CRM',   'sector': '软件'},
    {'code': 'ORCL',  'name': 'Oracle Corporation',      'finnhub_symbol': 'ORCL',  'sector': '软件'},
    {'code': 'ADBE',  'name': 'Adobe Inc.',              'finnhub_symbol': 'ADBE',  'sector': '软件'},
    {'code': 'NOW',   'name': 'ServiceNow Inc.',         'finnhub_symbol': 'NOW',   'sector': '软件'},
    {'code': 'INTU',  'name': 'Intuit Inc.',             'finnhub_symbol': 'INTU',  'sector': '软件'},
    {'code': 'SNOW',  'name': 'Snowflake Inc.',          'finnhub_symbol': 'SNOW',  'sector': '软件'},
    {'code': 'DDOG',  'name': 'Datadog Inc.',            'finnhub_symbol': 'DDOG',  'sector': '软件'},
    {'code': 'CRWD',  'name': 'CrowdStrike Holdings',   'finnhub_symbol': 'CRWD',  'sector': '软件'},
    {'code': 'ZS',    'name': 'Zscaler Inc.',            'finnhub_symbol': 'ZS',    'sector': '软件'},
    {'code': 'PANW',  'name': 'Palo Alto Networks',      'finnhub_symbol': 'PANW',  'sector': '软件'},
    {'code': 'FTNT',  'name': 'Fortinet Inc.',           'finnhub_symbol': 'FTNT',  'sector': '软件'},
    {'code': 'NET',   'name': 'Cloudflare Inc.',         'finnhub_symbol': 'NET',   'sector': '软件'},
    {'code': 'TWLO',  'name': 'Twilio Inc.',             'finnhub_symbol': 'TWLO',  'sector': '软件'},
    {'code': 'PLTR',  'name': 'Palantir Technologies',   'finnhub_symbol': 'PLTR',  'sector': '软件'},
    {'code': 'PATH',  'name': 'UiPath Inc.',             'finnhub_symbol': 'PATH',  'sector': '软件'},
    {'code': 'HUBS',  'name': 'HubSpot Inc.',            'finnhub_symbol': 'HUBS',  'sector': '软件'},
    {'code': 'WDAY',  'name': 'Workday Inc.',            'finnhub_symbol': 'WDAY',  'sector': '软件'},
    {'code': 'VEEV',  'name': 'Veeva Systems Inc.',      'finnhub_symbol': 'VEEV',  'sector': '软件'},
    {'code': 'TEAM',  'name': 'Atlassian Corporation',   'finnhub_symbol': 'TEAM',  'sector': '软件'},
    {'code': 'ZM',    'name': 'Zoom Video Communications','finnhub_symbol': 'ZM',   'sector': '软件'},
    {'code': 'DOCU',  'name': 'DocuSign Inc.',           'finnhub_symbol': 'DOCU',  'sector': '软件'},
    # ── 互联网 & 电商 ──
    {'code': 'NFLX',  'name': 'Netflix Inc.',            'finnhub_symbol': 'NFLX',  'sector': '互联网'},
    {'code': 'UBER',  'name': 'Uber Technologies Inc.',  'finnhub_symbol': 'UBER',  'sector': '互联网'},
    {'code': 'LYFT',  'name': 'Lyft Inc.',               'finnhub_symbol': 'LYFT',  'sector': '互联网'},
    {'code': 'ABNB',  'name': 'Airbnb Inc.',             'finnhub_symbol': 'ABNB',  'sector': '互联网'},
    {'code': 'SNAP',  'name': 'Snap Inc.',               'finnhub_symbol': 'SNAP',  'sector': '互联网'},
    {'code': 'PINS',  'name': 'Pinterest Inc.',          'finnhub_symbol': 'PINS',  'sector': '互联网'},
    {'code': 'SHOP',  'name': 'Shopify Inc.',            'finnhub_symbol': 'SHOP',  'sector': '互联网'},
    {'code': 'ETSY',  'name': 'Etsy Inc.',               'finnhub_symbol': 'ETSY',  'sector': '互联网'},
    {'code': 'EBAY',  'name': 'eBay Inc.',               'finnhub_symbol': 'EBAY',  'sector': '互联网'},
    {'code': 'BIDU',  'name': 'Baidu Inc. (ADR)',        'finnhub_symbol': 'BIDU',  'sector': '互联网'},
    {'code': 'JD',    'name': 'JD.com Inc. (ADR)',       'finnhub_symbol': 'JD',    'sector': '互联网'},
    {'code': 'PDD',   'name': 'PDD Holdings Inc.',       'finnhub_symbol': 'PDD',   'sector': '互联网'},
    {'code': 'BABA',  'name': 'Alibaba Group (ADR)',     'finnhub_symbol': 'BABA',  'sector': '互联网'},
    # ── 金融科技 & 支付 ──
    {'code': 'PYPL',  'name': 'PayPal Holdings Inc.',    'finnhub_symbol': 'PYPL',  'sector': '金融科技'},
    {'code': 'SQ',    'name': 'Block Inc.',              'finnhub_symbol': 'SQ',    'sector': '金融科技'},
    {'code': 'COIN',  'name': 'Coinbase Global Inc.',    'finnhub_symbol': 'COIN',  'sector': '金融科技'},
    {'code': 'AFRM',  'name': 'Affirm Holdings Inc.',   'finnhub_symbol': 'AFRM',  'sector': '金融科技'},
    {'code': 'SOFI',  'name': 'SoFi Technologies Inc.', 'finnhub_symbol': 'SOFI',  'sector': '金融科技'},
    # ── 消费 ──
    {'code': 'WMT',   'name': 'Walmart Inc.',            'finnhub_symbol': 'WMT',   'sector': '消费'},
    {'code': 'KO',    'name': 'Coca-Cola Company',       'finnhub_symbol': 'KO',    'sector': '消费'},
    {'code': 'PEP',   'name': 'PepsiCo Inc.',            'finnhub_symbol': 'PEP',   'sector': '消费'},
    {'code': 'MCD',   'name': "McDonald's Corporation",  'finnhub_symbol': 'MCD',   'sector': '消费'},
    {'code': 'SBUX',  'name': 'Starbucks Corporation',   'finnhub_symbol': 'SBUX',  'sector': '消费'},
    {'code': 'NKE',   'name': 'Nike Inc.',               'finnhub_symbol': 'NKE',   'sector': '消费'},
    {'code': 'TGT',   'name': 'Target Corporation',      'finnhub_symbol': 'TGT',   'sector': '消费'},
    {'code': 'COST',  'name': 'Costco Wholesale Corp.',  'finnhub_symbol': 'COST',  'sector': '消费'},
    {'code': 'HD',    'name': 'Home Depot Inc.',         'finnhub_symbol': 'HD',    'sector': '消费'},
    {'code': 'LOW',   'name': "Lowe's Companies Inc.",   'finnhub_symbol': 'LOW',   'sector': '消费'},
    {'code': 'TJX',   'name': 'TJX Companies Inc.',      'finnhub_symbol': 'TJX',   'sector': '消费'},
    {'code': 'AMGN',  'name': 'Amgen Inc.',              'finnhub_symbol': 'AMGN',  'sector': '消费'},
    {'code': 'PG',    'name': 'Procter & Gamble Co.',    'finnhub_symbol': 'PG',    'sector': '消费'},
    {'code': 'CL',    'name': 'Colgate-Palmolive Co.',   'finnhub_symbol': 'CL',    'sector': '消费'},
    {'code': 'PM',    'name': 'Philip Morris International','finnhub_symbol': 'PM',  'sector': '消费'},
    {'code': 'MO',    'name': 'Altria Group Inc.',       'finnhub_symbol': 'MO',    'sector': '消费'},
    # ── 医疗 & 生物科技 ──
    {'code': 'JNJ',   'name': 'Johnson & Johnson',       'finnhub_symbol': 'JNJ',   'sector': '医疗'},
    {'code': 'LLY',   'name': 'Eli Lilly and Company',  'finnhub_symbol': 'LLY',   'sector': '医疗'},
    {'code': 'UNH',   'name': 'UnitedHealth Group',      'finnhub_symbol': 'UNH',   'sector': '医疗'},
    {'code': 'PFE',   'name': 'Pfizer Inc.',             'finnhub_symbol': 'PFE',   'sector': '医疗'},
    {'code': 'MRK',   'name': 'Merck & Co. Inc.',        'finnhub_symbol': 'MRK',   'sector': '医疗'},
    {'code': 'ABBV',  'name': 'AbbVie Inc.',             'finnhub_symbol': 'ABBV',  'sector': '医疗'},
    {'code': 'BMY',   'name': 'Bristol-Myers Squibb Co.','finnhub_symbol': 'BMY',   'sector': '医疗'},
    {'code': 'GILD',  'name': 'Gilead Sciences Inc.',    'finnhub_symbol': 'GILD',  'sector': '医疗'},
    {'code': 'BIIB',  'name': 'Biogen Inc.',             'finnhub_symbol': 'BIIB',  'sector': '医疗'},
    {'code': 'REGN',  'name': 'Regeneron Pharmaceuticals','finnhub_symbol': 'REGN', 'sector': '医疗'},
    {'code': 'VRTX',  'name': 'Vertex Pharmaceuticals',  'finnhub_symbol': 'VRTX',  'sector': '医疗'},
    {'code': 'MRNA',  'name': 'Moderna Inc.',            'finnhub_symbol': 'MRNA',  'sector': '医疗'},
    {'code': 'ISRG',  'name': 'Intuitive Surgical Inc.', 'finnhub_symbol': 'ISRG',  'sector': '医疗'},
    {'code': 'MDT',   'name': 'Medtronic plc',           'finnhub_symbol': 'MDT',   'sector': '医疗'},
    {'code': 'ABT',   'name': 'Abbott Laboratories',     'finnhub_symbol': 'ABT',   'sector': '医疗'},
    {'code': 'TMO',   'name': 'Thermo Fisher Scientific','finnhub_symbol': 'TMO',   'sector': '医疗'},
    {'code': 'DHR',   'name': 'Danaher Corporation',     'finnhub_symbol': 'DHR',   'sector': '医疗'},
    {'code': 'CVS',   'name': 'CVS Health Corporation',  'finnhub_symbol': 'CVS',   'sector': '医疗'},
    {'code': 'CI',    'name': 'Cigna Group',             'finnhub_symbol': 'CI',    'sector': '医疗'},
    # ── 能源 ──
    {'code': 'XOM',   'name': 'Exxon Mobil Corporation', 'finnhub_symbol': 'XOM',   'sector': '能源'},
    {'code': 'CVX',   'name': 'Chevron Corporation',     'finnhub_symbol': 'CVX',   'sector': '能源'},
    {'code': 'COP',   'name': 'ConocoPhillips',          'finnhub_symbol': 'COP',   'sector': '能源'},
    {'code': 'EOG',   'name': 'EOG Resources Inc.',      'finnhub_symbol': 'EOG',   'sector': '能源'},
    {'code': 'SLB',   'name': 'Schlumberger Limited',    'finnhub_symbol': 'SLB',   'sector': '能源'},
    {'code': 'OXY',   'name': 'Occidental Petroleum',    'finnhub_symbol': 'OXY',   'sector': '能源'},
    {'code': 'PSX',   'name': 'Phillips 66',             'finnhub_symbol': 'PSX',   'sector': '能源'},
    {'code': 'VLO',   'name': 'Valero Energy Corporation','finnhub_symbol': 'VLO',  'sector': '能源'},
    # ── 工业 & 航空航天 ──
    {'code': 'BA',    'name': 'Boeing Company',          'finnhub_symbol': 'BA',    'sector': '工业'},
    {'code': 'CAT',   'name': 'Caterpillar Inc.',        'finnhub_symbol': 'CAT',   'sector': '工业'},
    {'code': 'DE',    'name': 'Deere & Company',         'finnhub_symbol': 'DE',    'sector': '工业'},
    {'code': 'GE',    'name': 'GE Aerospace',            'finnhub_symbol': 'GE',    'sector': '工业'},
    {'code': 'HON',   'name': 'Honeywell International', 'finnhub_symbol': 'HON',   'sector': '工业'},
    {'code': 'MMM',   'name': '3M Company',              'finnhub_symbol': 'MMM',   'sector': '工业'},
    {'code': 'RTX',   'name': 'RTX Corporation',         'finnhub_symbol': 'RTX',   'sector': '工业'},
    {'code': 'LMT',   'name': 'Lockheed Martin Corp.',   'finnhub_symbol': 'LMT',   'sector': '工业'},
    {'code': 'NOC',   'name': 'Northrop Grumman Corp.',  'finnhub_symbol': 'NOC',   'sector': '工业'},
    {'code': 'GD',    'name': 'General Dynamics Corp.',  'finnhub_symbol': 'GD',    'sector': '工业'},
    {'code': 'UPS',   'name': 'United Parcel Service',   'finnhub_symbol': 'UPS',   'sector': '工业'},
    {'code': 'FDX',   'name': 'FedEx Corporation',       'finnhub_symbol': 'FDX',   'sector': '工业'},
    {'code': 'DAL',   'name': 'Delta Air Lines Inc.',    'finnhub_symbol': 'DAL',   'sector': '工业'},
    {'code': 'UAL',   'name': 'United Airlines Holdings','finnhub_symbol': 'UAL',   'sector': '工业'},
    {'code': 'AAL',   'name': 'American Airlines Group', 'finnhub_symbol': 'AAL',   'sector': '工业'},
    {'code': 'WM',    'name': 'Waste Management Inc.',   'finnhub_symbol': 'WM',    'sector': '工业'},
    # ── 通信 & 媒体 ──
    {'code': 'DIS',   'name': 'Walt Disney Company',     'finnhub_symbol': 'DIS',   'sector': '通信'},
    {'code': 'CMCSA', 'name': 'Comcast Corporation',     'finnhub_symbol': 'CMCSA', 'sector': '通信'},
    {'code': 'T',     'name': 'AT&T Inc.',               'finnhub_symbol': 'T',     'sector': '通信'},
    {'code': 'VZ',    'name': 'Verizon Communications',  'finnhub_symbol': 'VZ',    'sector': '通信'},
    {'code': 'TMUS',  'name': 'T-Mobile US Inc.',        'finnhub_symbol': 'TMUS',  'sector': '通信'},
    {'code': 'CHTR',  'name': 'Charter Communications',  'finnhub_symbol': 'CHTR',  'sector': '通信'},
    {'code': 'WBD',   'name': 'Warner Bros. Discovery',  'finnhub_symbol': 'WBD',   'sector': '通信'},
    {'code': 'PARA',  'name': 'Paramount Global',        'finnhub_symbol': 'PARA',  'sector': '通信'},
    # ── 房地产 REIT ──
    {'code': 'AMT',   'name': 'American Tower Corp.',    'finnhub_symbol': 'AMT',   'sector': '房地产'},
    {'code': 'PLD',   'name': 'Prologis Inc.',           'finnhub_symbol': 'PLD',   'sector': '房地产'},
    {'code': 'EQIX',  'name': 'Equinix Inc.',            'finnhub_symbol': 'EQIX',  'sector': '房地产'},
    {'code': 'CCI',   'name': 'Crown Castle Inc.',       'finnhub_symbol': 'CCI',   'sector': '房地产'},
    {'code': 'SPG',   'name': 'Simon Property Group',    'finnhub_symbol': 'SPG',   'sector': '房地产'},
    {'code': 'O',     'name': 'Realty Income Corporation','finnhub_symbol': 'O',    'sector': '房地产'},
    # ── 公用事业 ──
    {'code': 'NEE',   'name': 'NextEra Energy Inc.',     'finnhub_symbol': 'NEE',   'sector': '公用事业'},
    {'code': 'DUK',   'name': 'Duke Energy Corporation', 'finnhub_symbol': 'DUK',   'sector': '公用事业'},
    {'code': 'SO',    'name': 'Southern Company',        'finnhub_symbol': 'SO',    'sector': '公用事业'},
    {'code': 'D',     'name': 'Dominion Energy Inc.',    'finnhub_symbol': 'D',     'sector': '公用事业'},
    {'code': 'AEP',   'name': 'American Electric Power', 'finnhub_symbol': 'AEP',   'sector': '公用事业'},
    # ── 新能源 & 电动车 ──
    {'code': 'RIVN',  'name': 'Rivian Automotive Inc.',  'finnhub_symbol': 'RIVN',  'sector': '新能源'},
    {'code': 'LCID',  'name': 'Lucid Group Inc.',        'finnhub_symbol': 'LCID',  'sector': '新能源'},
    {'code': 'NIO',   'name': 'NIO Inc. (ADR)',          'finnhub_symbol': 'NIO',   'sector': '新能源'},
    {'code': 'XPEV',  'name': 'XPeng Inc. (ADR)',        'finnhub_symbol': 'XPEV',  'sector': '新能源'},
    {'code': 'LI',    'name': 'Li Auto Inc. (ADR)',      'finnhub_symbol': 'LI',    'sector': '新能源'},
    {'code': 'ENPH',  'name': 'Enphase Energy Inc.',     'finnhub_symbol': 'ENPH',  'sector': '新能源'},
    {'code': 'SEDG',  'name': 'SolarEdge Technologies',  'finnhub_symbol': 'SEDG',  'sector': '新能源'},
    {'code': 'FSLR',  'name': 'First Solar Inc.',        'finnhub_symbol': 'FSLR',  'sector': '新能源'},
    # ── 指数 ETF ──
    {'code': 'SPY',   'name': 'SPDR S&P 500 ETF',           'finnhub_symbol': 'SPY',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'QQQ',   'name': 'Invesco QQQ (Nasdaq 100)',    'finnhub_symbol': 'QQQ',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'IWM',   'name': 'iShares Russell 2000 ETF',    'finnhub_symbol': 'IWM',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'GLD',   'name': 'SPDR Gold Shares ETF',        'finnhub_symbol': 'GLD',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'TLT',   'name': 'iShares 20+ Year Treasury',   'finnhub_symbol': 'TLT',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'VTI',   'name': 'Vanguard Total Stock Market', 'finnhub_symbol': 'VTI',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'VOO',   'name': 'Vanguard S&P 500 ETF',        'finnhub_symbol': 'VOO',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'IVV',   'name': 'iShares Core S&P 500 ETF',    'finnhub_symbol': 'IVV',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'AGG',   'name': 'iShares Core US Aggregate Bond','finnhub_symbol': 'AGG', 'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'VNQ',   'name': 'Vanguard Real Estate ETF',    'finnhub_symbol': 'VNQ',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'XLK',   'name': 'Technology Select Sector SPDR','finnhub_symbol': 'XLK', 'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'XLF',   'name': 'Financial Select Sector SPDR','finnhub_symbol': 'XLF',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'XLE',   'name': 'Energy Select Sector SPDR',   'finnhub_symbol': 'XLE',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'XLV',   'name': 'Health Care Select Sector',   'finnhub_symbol': 'XLV',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'XLI',   'name': 'Industrial Select Sector SPDR','finnhub_symbol': 'XLI', 'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'ARKK',  'name': 'ARK Innovation ETF',          'finnhub_symbol': 'ARKK', 'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'ARKG',  'name': 'ARK Genomic Revolution ETF',  'finnhub_symbol': 'ARKG', 'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'ARKW',  'name': 'ARK Next Generation Internet','finnhub_symbol': 'ARKW', 'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'SLV',   'name': 'iShares Silver Trust',        'finnhub_symbol': 'SLV',  'sector': 'ETF', 'asset_type': 'ETF'},
    {'code': 'USO',   'name': 'United States Oil Fund',      'finnhub_symbol': 'USO',  'sector': 'ETF', 'asset_type': 'ETF'},
]

# ── A 股精选（上证 SH / 深证 SZ，市场标识分开） ────────────────────────────────
# 注意：600/601/603/605 开头的为上交所 → market='SH'
#       000/002/003/300/301 开头的为深交所 → market='SZ'
SH_STOCKS = [
    {'code': '600519', 'name': '贵州茅台',   'finnhub_symbol': '600519.SS', 'sector': '白酒',   'market': 'SH'},
    {'code': '601318', 'name': '中国平安',   'finnhub_symbol': '601318.SS', 'sector': '金融',   'market': 'SH'},
    {'code': '600036', 'name': '招商银行',   'finnhub_symbol': '600036.SS', 'sector': '银行',   'market': 'SH'},
    {'code': '601166', 'name': '兴业银行',   'finnhub_symbol': '601166.SS', 'sector': '银行',   'market': 'SH'},
    {'code': '600900', 'name': '长江电力',   'finnhub_symbol': '600900.SS', 'sector': '电力',   'market': 'SH'},
    {'code': '601988', 'name': '中国银行',   'finnhub_symbol': '601988.SS', 'sector': '银行',   'market': 'SH'},
    {'code': '600276', 'name': '恒瑞医药',   'finnhub_symbol': '600276.SS', 'sector': '医药',   'market': 'SH'},
    {'code': '601888', 'name': '中国中免',   'finnhub_symbol': '601888.SS', 'sector': '消费',   'market': 'SH'},
    {'code': '603288', 'name': '海天味业',   'finnhub_symbol': '603288.SS', 'sector': '食品',   'market': 'SH'},
    {'code': '601919', 'name': '中远海控',   'finnhub_symbol': '601919.SS', 'sector': '航运',   'market': 'SH'},
]

SZ_STOCKS = [
    {'code': '000858', 'name': '五粮液',     'finnhub_symbol': '000858.SZ', 'sector': '白酒',   'market': 'SZ'},
    {'code': '000333', 'name': '美的集团',   'finnhub_symbol': '000333.SZ', 'sector': '家电',   'market': 'SZ'},
    {'code': '002594', 'name': '比亚迪',     'finnhub_symbol': '002594.SZ', 'sector': '新能源', 'market': 'SZ'},
    {'code': '300750', 'name': '宁德时代',   'finnhub_symbol': '300750.SZ', 'sector': '新能源', 'market': 'SZ'},
    {'code': '000001', 'name': '平安银行',   'finnhub_symbol': '000001.SZ', 'sector': '银行',   'market': 'SZ'},
    {'code': '000651', 'name': '格力电器',   'finnhub_symbol': '000651.SZ', 'sector': '家电',   'market': 'SZ'},
    {'code': '002415', 'name': '海康威视',   'finnhub_symbol': '002415.SZ', 'sector': '科技',   'market': 'SZ'},
    {'code': '300059', 'name': '东方财富',   'finnhub_symbol': '300059.SZ', 'sector': '金融科技', 'market': 'SZ'},
    {'code': '002714', 'name': '牧原股份',   'finnhub_symbol': '002714.SZ', 'sector': '农业',   'market': 'SZ'},
    {'code': '000568', 'name': '泸州老窖',   'finnhub_symbol': '000568.SZ', 'sector': '白酒',   'market': 'SZ'},
]


class Command(BaseCommand):
    help = '一键添加热门股票到数据库（美股精选 + A股蓝筹，市场标识精确为 SH/SZ/US）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--market',
            type=str,
            default='ALL',
            choices=['ALL', 'US', 'CN'],
            help='添加范围：ALL（全部）/ US（仅美股）/ CN（仅A股）'
        )
        parser.add_argument(
            '--quote',
            action='store_true',
            help='添加后立即拉取 Finnhub 行情快照'
        )

    def handle(self, *args, **options):
        from content.models import Asset
        from django.utils import timezone as dj_tz

        market_filter = options['market']
        do_quote = options['quote']

        stocks_to_add = []
        if market_filter in ('ALL', 'US'):
            for s in US_STOCKS:
                stocks_to_add.append({
                    **s,
                    'market': 'US',
                    'currency': 'USD',
                    'exchange': 'NASDAQ/NYSE',
                    'asset_type': s.get('asset_type', 'STOCK'),
                })
        if market_filter in ('ALL', 'CN'):
            for s in SH_STOCKS:
                stocks_to_add.append({
                    **s,
                    'currency': 'CNY',
                    'exchange': 'SSE',
                    'asset_type': s.get('asset_type', 'STOCK'),
                })
            for s in SZ_STOCKS:
                stocks_to_add.append({
                    **s,
                    'currency': 'CNY',
                    'exchange': 'SZSE',
                    'asset_type': s.get('asset_type', 'STOCK'),
                })

        created_count = 0
        updated_count = 0
        asset_objs = []

        for stock in stocks_to_add:
            try:
                obj, created = Asset.objects.update_or_create(
                    code=stock['code'],
                    market=stock['market'],
                    defaults={
                        'name': stock['name'],
                        'asset_type': stock['asset_type'],
                        'finnhub_symbol': stock['finnhub_symbol'],
                        'currency': stock['currency'],
                        'exchange': stock['exchange'],
                        'status': 'ACTIVE',
                        'last_sync_at': dj_tz.now(),
                    }
                )
                asset_objs.append(obj)
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  [NEW] [{stock["market"]}] {stock["code"]} - {stock["name"]}'
                    ))
                else:
                    updated_count += 1
                    self.stdout.write(
                        f'  [UPD] [{stock["market"]}] {stock["code"]} - {stock["name"]}'
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  [ERR] {stock["code"]} - {str(e)}'
                ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'[DONE] 新增 {created_count} 只，更新 {updated_count} 只，共 {len(stocks_to_add)} 只股票'
        ))
        self.stdout.write(f'  其中：US={sum(1 for s in stocks_to_add if s["market"]=="US")}'
                          f'  SH={sum(1 for s in stocks_to_add if s["market"]=="SH")}'
                          f'  SZ={sum(1 for s in stocks_to_add if s["market"]=="SZ")}')

        if do_quote:
            self.stdout.write('\n[INFO] 正在拉取行情快照...')
            from market_data import finnhub_service as fh
            if not fh.is_api_key_configured():
                self.stdout.write(self.style.WARNING(
                    '[WARN] FINNHUB_API_KEY 未配置，跳过行情刷新'
                ))
                return

            from market_data.tasks import get_or_refresh_quote
            success_count = 0
            for asset in asset_objs:
                if not asset.finnhub_symbol:
                    continue
                quote = get_or_refresh_quote(asset)
                if quote:
                    price = quote.get('price', 'N/A')
                    change_pct = quote.get('change_pct', 0) or 0
                    sign = '+' if change_pct >= 0 else ''
                    self.stdout.write(
                        f'  {asset.code:10s}  [{asset.market}]  price={price}  pct={sign}{change_pct:.2f}%'
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  [NO DATA] {asset.code} ({asset.market})')
                    )

            self.stdout.write(self.style.SUCCESS(
                f'\n[DONE] 行情刷新完成！成功 {success_count}/{len(asset_objs)} 只'
            ))
        else:
            self.stdout.write('')
            self.stdout.write('[TIP] 运行以下命令刷新行情：')
            self.stdout.write('   python manage.py add_popular_stocks --quote')
            self.stdout.write('   python manage.py sync_market_data --task quote')
