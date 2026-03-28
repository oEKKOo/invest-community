"""
Tushare 服务层 —— A 股行情数据接入

遵循与 finnhub-api.mdc 相同的设计规范：
1. Token 从环境变量 TUSHARE_API_TOKEN 读取，禁止明文出现在代码/日志中
2. 所有请求在后端执行，禁止前端直接调用
3. 限流/网络异常 → 指数退避重试
4. 日志脱敏：不打印 Token，只记录"是否已配置"

支持的数据：
- 股票基础信息   (pro.stock_basic)
- 日线行情 K 线  (pro.daily)  — 字段：开/高/低/收/量/额/涨跌幅
- 最新行情快照   (get_latest_daily_quote) — 取最近交易日 daily 数据
- 港股基础/日线 (pro.hk_basic / pro.hk_daily)，ts_code 形如 00001.HK

Tushare A 股 ts_code 格式：{6位代码}.{市场后缀}
  600519.SH  (上交所)
  000001.SZ  (深交所)
  837566.BJ  (北交所)

内部 market 与 Tushare 后缀映射：
  SH → SH  /  SZ → SZ  /  BJ → BJ
"""
import os
import time
import logging
from datetime import datetime, timedelta, timezone as _tz
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# ── A 股市场集合（供 tasks/views 判断是否走 Tushare）──────────────────────
CN_MARKETS = {'SH', 'SZ', 'BJ'}

# 港股：日 K 走 Tushare hk_daily（与 Finnhub 分时/实时行情可并存）
HK_MARKET = 'HK'

# 市场 → Tushare 后缀
MARKET_TO_SUFFIX: Dict[str, str] = {
    'SH': 'SH',
    'SZ': 'SZ',
    'BJ': 'BJ',
}

# ── 限流保护 ──────────────────────────────────────────────────────────────
MAX_RETRIES = 3
BACKOFF_BASE = 2          # 指数退避基数（秒）
REQUEST_DELAY = 0.4       # 每次成功请求后的保护等待（秒）
RATE_LIMIT_WAIT = 30      # 触发 Tushare 限流后的额外等待（秒）


# ═══════════════════════════════════════════════════════════════════════════
# 配置读取
# ═══════════════════════════════════════════════════════════════════════════

def _get_api_token() -> str:
    """从环境变量读取 Tushare API Token（绝对不写入日志）"""
    return os.environ.get('TUSHARE_API_TOKEN', '')


def is_api_token_configured() -> bool:
    """仅用于启动检查：返回 Token 是否已配置（不返回 Token 本身）"""
    return bool(_get_api_token())


# ═══════════════════════════════════════════════════════════════════════════
# 代码格式转换
# ═══════════════════════════════════════════════════════════════════════════

def get_tushare_code(code: str, market: str) -> Optional[str]:
    """
    将内部 code + market 转换为 Tushare ts_code
    例：code='600519', market='SH' → '600519.SH'
         code='000001', market='SZ' → '000001.SZ'
    仅支持 A 股市场（SH/SZ/BJ），其他市场返回 None
    """
    suffix = MARKET_TO_SUFFIX.get(market)
    if not suffix:
        return None
    return f"{code}.{suffix}"


def parse_tushare_code(ts_code: str) -> Optional[Dict[str, str]]:
    """
    将 Tushare ts_code 解析回内部 code + market
    例：'600519.SH' → {'code': '600519', 'market': 'SH'}
    """
    parts = ts_code.strip().split('.')
    if len(parts) != 2:
        return None
    code, suffix = parts
    # 仅处理 A 股后缀
    if suffix not in MARKET_TO_SUFFIX.values():
        return None
    return {'code': code, 'market': suffix}


def normalize_hk_listing_code(code: str) -> str:
    """港股代码与 hk_daily 路由键：纯数字则左补零至 5 位，否则原样 strip。"""
    s = str(code).strip()
    if s.isdigit():
        return s.zfill(5)
    return s


def parse_hk_ts_code(ts_code: str) -> Optional[Dict[str, str]]:
    """
    解析港股 Tushare 代码，如 '00001.HK' → code（五位数字串）+ market 'HK'
    """
    parts = ts_code.strip().split('.')
    if len(parts) != 2:
        return None
    code, suf = parts
    if suf.upper() != 'HK':
        return None
    return {'code': normalize_hk_listing_code(code), 'market': HK_MARKET}


def get_hk_tushare_code(code: str) -> Optional[str]:
    """
    内部展示码 → Tushare 港股 ts_code（00001.HK）。
    非纯数字无法与 hk_daily 对齐时返回 None。
    """
    s = str(code).strip()
    if not s:
        return None
    if not s.isdigit():
        return None
    return f'{normalize_hk_listing_code(s)}.HK'


# ═══════════════════════════════════════════════════════════════════════════
# 核心：Pro API 实例（懒初始化）
# ═══════════════════════════════════════════════════════════════════════════

_pro_instance = None   # 进程内单例，避免重复初始化


def _get_pro_api():
    """
    获取 Tushare Pro API 实例（懒初始化）
    若 Token 未配置或 tushare 包未安装，返回 None
    """
    global _pro_instance
    if _pro_instance is not None:
        return _pro_instance

    token = _get_api_token()
    if not token:
        logger.error('[Tushare] TUSHARE_API_TOKEN 未配置，跳过请求')
        return None

    try:
        import tushare as ts
        pro = ts.pro_api(token)
        _pro_instance = pro
        logger.info('[Tushare] Pro API 初始化成功（Token 已配置）')
        return pro
    except ImportError:
        logger.error('[Tushare] tushare 包未安装，请运行: pip install tushare')
        return None
    except Exception as exc:
        logger.error('[Tushare] Pro API 初始化失败: %s', str(exc))
        return None


def _call_with_retry(func, *args, retries: int = MAX_RETRIES, **kwargs):
    """
    带重试的 Tushare API 调用
    - 限流异常 → 长等待后重试
    - 网络/其他异常 → 指数退避重试
    - 全部失败 → 返回 None
    """
    for attempt in range(1, retries + 1):
        try:
            result = func(*args, **kwargs)
            time.sleep(REQUEST_DELAY)  # 保护等待，避免触发限流
            return result
        except Exception as exc:
            err_str = str(exc)
            is_rate_limit = any(kw in err_str for kw in (
                'limit', '每分钟', 'rate', '频率', '积分', 'permission', '权限'
            ))
            if is_rate_limit:
                wait = RATE_LIMIT_WAIT * attempt
                logger.warning(
                    '[Tushare] 触发限流/权限限制, attempt=%d/%d, 等待 %ds: %s',
                    attempt, retries, wait, err_str
                )
                time.sleep(wait)
            else:
                wait = BACKOFF_BASE ** attempt
                logger.warning(
                    '[Tushare] API 异常, attempt=%d/%d, 退避 %ds: %s',
                    attempt, retries, wait, err_str
                )
                time.sleep(wait)

    logger.error('[Tushare] 重试耗尽，放弃本次请求')
    return None


# ═══════════════════════════════════════════════════════════════════════════
# A 股基础信息
# ═══════════════════════════════════════════════════════════════════════════

def get_stock_basic(list_status: str = 'L') -> Optional[List[Dict]]:
    """
    获取 A 股上市股票基础信息
    list_status: L(上市) D(退市) P(暂停上市)
    返回: [{'ts_code','code','market','name','area','industry','list_date','exchange'}, ...]
    """
    pro = _get_pro_api()
    if not pro:
        return None

    df = _call_with_retry(
        pro.stock_basic,
        list_status=list_status,
        fields='ts_code,symbol,name,area,industry,list_date,exchange',
    )
    if df is None or df.empty:
        logger.warning('[Tushare] get_stock_basic: 返回空数据 list_status=%s', list_status)
        return None

    result = []
    for _, row in df.iterrows():
        ts_code = str(row.get('ts_code', '')).strip()
        if not ts_code:
            continue
        parsed = parse_tushare_code(ts_code)
        if not parsed:
            continue
        result.append({
            'ts_code':   ts_code,
            'code':      parsed['code'],
            'market':    parsed['market'],
            'name':      str(row.get('name', '')).strip(),
            'area':      str(row.get('area', '')).strip(),
            'industry':  str(row.get('industry', '')).strip(),
            'list_date': str(row.get('list_date', '')).strip(),
            'exchange':  str(row.get('exchange', '')).strip(),
        })

    logger.info('[Tushare] get_stock_basic: 获取 %d 只 A 股', len(result))
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 日线行情 K 线
# ═══════════════════════════════════════════════════════════════════════════

def get_daily_klines(
    ts_code: str,
    start_date: str,   # 'YYYYMMDD'
    end_date: str,     # 'YYYYMMDD'
) -> Optional[List[Dict]]:
    """
    获取股票日线行情历史 K 线
    ts_code    : Tushare 代码，如 '000001.SZ'
    start_date : 'YYYYMMDD' 格式
    end_date   : 'YYYYMMDD' 格式
    返回 (升序排列):
      [{'k_time', 'open', 'high', 'low', 'close', 'volume',
        'amount', 'pct_chg', 'pre_close', 'change'}, ...]
    注：
      - volume 单位：手（100股）→ 已转为手（保持原始值，前端按需转换）
      - amount 单位：千元
      - k_time 为 UTC 时间（当日 00:00:00 UTC），存储时与 Finnhub 规范对齐
    """
    pro = _get_pro_api()
    if not pro:
        return None

    df = _call_with_retry(
        pro.daily,
        ts_code=ts_code,
        start_date=start_date,
        end_date=end_date,
    )
    if df is None or df.empty:
        logger.debug('[Tushare] get_daily_klines: %s [%s~%s] 无数据',
                     ts_code, start_date, end_date)
        return None

    items = []
    for _, row in df.iterrows():
        trade_date = str(row.get('trade_date', '')).strip()
        if len(trade_date) != 8:
            continue
        try:
            # 存储为 UTC 当日 0 点（与 Finnhub 日 K 对齐，便于统一查询）
            k_time = datetime(
                int(trade_date[:4]),
                int(trade_date[4:6]),
                int(trade_date[6:8]),
                0, 0, 0,
                tzinfo=_tz.utc,
            )
        except (ValueError, TypeError):
            continue

        items.append({
            'k_time':    k_time,
            'open':      _safe_float(row.get('open')),
            'high':      _safe_float(row.get('high')),
            'low':       _safe_float(row.get('low')),
            'close':     _safe_float(row.get('close')),
            'volume':    _safe_int(row.get('vol')),     # 单位：手
            'amount':    _safe_float(row.get('amount')), # 单位：千元
            'pct_chg':   _safe_float(row.get('pct_chg')),
            'pre_close': _safe_float(row.get('pre_close')),
            'change':    _safe_float(row.get('change')),
        })

    # Tushare 返回降序，转为升序（时间从旧到新）
    items.reverse()
    logger.debug('[Tushare] get_daily_klines: %s 获取 %d 条', ts_code, len(items))
    return items


def get_daily_klines_by_date(trade_date: str) -> Optional[List[Dict]]:
    """
    获取指定交易日全市场 A 股日线数据（一次 API 调用返回所有股票）。

    对比 get_daily_klines：
      get_daily_klines   → 单股 × N 次调用（5484 只 = 5484 次 API）
      get_daily_klines_by_date → 全市场 × 1 次调用（1 次 API 拿当日所有股票）

    trade_date: 'YYYYMMDD' 格式（如 '20260226'）
    若为非交易日，Tushare 返回空 DataFrame，本函数返回 None。

    返回列表（每条多了 ts_code / code / market 字段供调用方路由到 Asset）：
      [{'ts_code', 'code', 'market', 'k_time',
        'open', 'high', 'low', 'close', 'volume', 'amount',
        'pct_chg', 'pre_close', 'change'}, ...]
    """
    pro = _get_pro_api()
    if not pro:
        return None

    df = _call_with_retry(pro.daily, trade_date=trade_date)
    if df is None or df.empty:
        logger.debug('[Tushare] get_daily_klines_by_date: %s 非交易日或无数据', trade_date)
        return None

    items = []
    for _, row in df.iterrows():
        ts_code   = str(row.get('ts_code', '')).strip()
        trade_d   = str(row.get('trade_date', '')).strip()
        if not ts_code or len(trade_d) != 8:
            continue

        parsed = parse_tushare_code(ts_code)
        if not parsed:
            continue

        try:
            k_time = datetime(
                int(trade_d[:4]), int(trade_d[4:6]), int(trade_d[6:8]),
                0, 0, 0, tzinfo=_tz.utc,
            )
        except (ValueError, TypeError):
            continue

        items.append({
            'ts_code':   ts_code,
            'code':      parsed['code'],
            'market':    parsed['market'],
            'k_time':    k_time,
            'open':      _safe_float(row.get('open')),
            'high':      _safe_float(row.get('high')),
            'low':       _safe_float(row.get('low')),
            'close':     _safe_float(row.get('close')),
            'volume':    _safe_int(row.get('vol')),
            'amount':    _safe_float(row.get('amount')),
            'pct_chg':   _safe_float(row.get('pct_chg')),
            'pre_close': _safe_float(row.get('pre_close')),
            'change':    _safe_float(row.get('change')),
        })

    logger.info('[Tushare] get_daily_klines_by_date: %s 获取 %d 条（全市场）',
                trade_date, len(items))
    return items or None


def get_latest_daily_quotes_all(lookback_days: int = 7) -> Optional[List[Dict]]:
    """
    获取全市场最近交易日的行情数据（一次 API 调用，自动回退）。

    对比 get_latest_daily_quote（逐股调用）：
      旧：5485 只 × 1 次调用 × 0.9s ≈ 82 分钟
      新：1 次调用（自动回退直到找到有数据的交易日）≈ 0.4 秒

    lookback_days: 最多向前回退天数（应对周末/节假日，建议 >=5）
    返回格式同 get_daily_klines_by_date，每条多了 ts_code / code / market。
    None 表示最近 lookback_days 天内均无数据。
    """
    for delta in range(lookback_days):
        dt = datetime.now(_tz.utc) - timedelta(days=delta)
        date_str = dt.strftime('%Y%m%d')
        items = get_daily_klines_by_date(date_str)
        if items:
            logger.info('[Tushare] get_latest_daily_quotes_all: 取到 %s 共 %d 条', date_str, len(items))
            return items

    logger.warning('[Tushare] get_latest_daily_quotes_all: 最近 %d 天均无数据', lookback_days)
    return None


def get_latest_daily_quote(ts_code: str, lookback_days: int = 7) -> Optional[Dict]:
    """
    获取最新交易日的行情快照（收盘数据）
    lookback_days: 向前查找的最大天数（应对节假日/周末，建议 >= 5）

    返回与 finnhub_service.get_quote() 格式完全对齐的字典，便于统一写入快照表：
    {
        'price', 'change_amount', 'change_pct',
        'open', 'high', 'low', 'prev_close',
        'volume', 'amount', 'quote_time', 'source'
    }
    """
    end_date = datetime.now(_tz.utc).strftime('%Y%m%d')
    start_date = (datetime.now(_tz.utc) - timedelta(days=lookback_days)).strftime('%Y%m%d')

    items = get_daily_klines(ts_code, start_date, end_date)
    if not items:
        logger.debug('[Tushare] get_latest_daily_quote: %s 无数据', ts_code)
        return None

    # 升序最后一条 = 最新交易日
    latest = items[-1]

    return {
        'price':         latest.get('close'),
        'change_amount': latest.get('change'),
        'change_pct':    latest.get('pct_chg'),   # 单位已是 % 值（如 2.35）
        'open':          latest.get('open'),
        'high':          latest.get('high'),
        'low':           latest.get('low'),
        'prev_close':    latest.get('pre_close'),
        'volume':        latest.get('volume'),     # 手
        'amount':        latest.get('amount'),     # 千元
        'quote_time':    latest.get('k_time'),
        'source':        'tushare',
    }


# ═══════════════════════════════════════════════════════════════════════════
# 港股：hk_basic / hk_daily（需 Tushare 积分与 hk_daily 权限）
# ═══════════════════════════════════════════════════════════════════════════

def get_hk_basic(list_status: str = 'L') -> Optional[List[Dict]]:
    """
    港股列表 pro.hk_basic(list_status=...)
    返回 [{'ts_code','code','name','fullname','list_status','list_date','curr_type'}, ...]
    """
    pro = _get_pro_api()
    if not pro:
        return None

    df = _call_with_retry(pro.hk_basic, list_status=list_status)
    if df is None or df.empty:
        logger.warning('[Tushare] get_hk_basic: 空数据 list_status=%s', list_status)
        return None

    out = []
    for _, row in df.iterrows():
        ts_code = str(row.get('ts_code', '')).strip()
        if not ts_code:
            continue
        parsed = parse_hk_ts_code(ts_code)
        if not parsed:
            continue
        out.append({
            'ts_code':     ts_code,
            'code':        parsed['code'],
            'name':        str(row.get('name', '')).strip(),
            'fullname':    str(row.get('fullname', '') or '').strip(),
            'list_status': str(row.get('list_status', '') or '').strip(),
            'list_date':   str(row.get('list_date', '') or '').strip(),
            'curr_type':   str(row.get('curr_type', '') or '').strip(),
        })

    logger.info('[Tushare] get_hk_basic: %d 条 list_status=%s', len(out), list_status)
    return out


def _row_to_hk_kline_item(row) -> Optional[Dict]:
    """单条 hk_daily 行 → 与 get_daily_klines 单条兼容的结构"""
    trade_date = str(row.get('trade_date', '')).strip()
    if len(trade_date) != 8:
        return None
    try:
        k_time = datetime(
            int(trade_date[:4]),
            int(trade_date[4:6]),
            int(trade_date[6:8]),
            0, 0, 0,
            tzinfo=_tz.utc,
        )
    except (ValueError, TypeError):
        return None

    return {
        'k_time':    k_time,
        'open':      _safe_float(row.get('open')),
        'high':      _safe_float(row.get('high')),
        'low':       _safe_float(row.get('low')),
        'close':     _safe_float(row.get('close')),
        'volume':    _safe_int(row.get('vol')),
        'amount':    _safe_float(row.get('amount')),
        'pct_chg':   _safe_float(row.get('pct_chg')),
        'pre_close': _safe_float(row.get('pre_close')),
        'change':    _safe_float(row.get('change')),
    }


def get_hk_daily_klines(
    ts_code: str,
    start_date: str,
    end_date: str,
) -> Optional[List[Dict]]:
    """
    单只港股历史日线 pro.hk_daily(ts_code=..., start_date=..., end_date=...)
    返回与 get_daily_klines 相同（升序）
    """
    pro = _get_pro_api()
    if not pro:
        return None

    df = _call_with_retry(
        pro.hk_daily,
        ts_code=ts_code,
        start_date=start_date,
        end_date=end_date,
    )
    if df is None or df.empty:
        logger.debug('[Tushare] get_hk_daily_klines: %s [%s~%s] 无数据',
                     ts_code, start_date, end_date)
        return None

    items = []
    for _, row in df.iterrows():
        item = _row_to_hk_kline_item(row)
        if item:
            items.append(item)

    items.reverse()
    logger.debug('[Tushare] get_hk_daily_klines: %s 获取 %d 条', ts_code, len(items))
    return items


def get_hk_daily_by_date(trade_date: str) -> Optional[List[Dict]]:
    """
    指定交易日全市场港股日线（一次 API pro.hk_daily(trade_date=...)）。
    全市场单日若超过 5000 行需 Tushare 侧分页，当前单次调用（文档上限 5000）。

    返回字段与 get_daily_klines_by_date 对齐，含 ts_code / code / market：
      code 为 normalize_hk_listing_code 后的路由键
    """
    pro = _get_pro_api()
    if not pro:
        return None

    df = _call_with_retry(pro.hk_daily, trade_date=trade_date)
    if df is None or df.empty:
        logger.debug('[Tushare] get_hk_daily_by_date: %s 非交易日或无数据', trade_date)
        return None

    items = []
    for _, row in df.iterrows():
        ts_code = str(row.get('ts_code', '')).strip()
        trade_d = str(row.get('trade_date', '')).strip()
        if not ts_code or len(trade_d) != 8:
            continue
        parsed = parse_hk_ts_code(ts_code)
        if not parsed:
            continue

        base = _row_to_hk_kline_item(row)
        if not base:
            continue

        items.append({
            'ts_code':   ts_code,
            'code':      parsed['code'],
            'market':    HK_MARKET,
            **base,
        })

    logger.info('[Tushare] get_hk_daily_by_date: %s 获取 %d 条（全市场港股）',
                trade_date, len(items))
    return items or None


# ═══════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════

def _safe_float(val) -> Optional[float]:
    """安全转换为 float，NaN/None 返回 None"""
    if val is None:
        return None
    try:
        f = float(val)
        return None if (f != f) else f   # NaN check: NaN != NaN
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    """安全转换为 int，NaN/None 返回 None"""
    if val is None:
        return None
    try:
        f = float(val)
        if f != f:   # NaN
            return None
        return int(f)
    except (ValueError, TypeError):
        return None


def date_to_tushare_str(dt: datetime) -> str:
    """datetime → Tushare 日期格式 'YYYYMMDD'"""
    return dt.strftime('%Y%m%d')
