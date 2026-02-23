"""
Finnhub 服务层
遵循 finnhub-api.mdc 规范：
1. Key 从环境变量 FINNHUB_API_KEY 读取，禁止明文出现在代码/日志中
2. 所有请求在后端拼接 token 参数，禁止前端直接调用
3. 429 → 指数退避重试；5xx → 重试（上限）；4xx → 不重试
4. 日志脱敏：不打印 Key，只记录"是否已配置"
"""
import os
import time
import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

# ---------- 运行时 403 记忆（进程内，避免重复请求已知无权限的端点） ----------
# 格式：{ endpoint: True }   —— 例如 '/stock/candle'
# 重启后自动清除，不影响其他端点
_forbidden_endpoints: set = set()


def mark_endpoint_forbidden(endpoint: str):
    """将某个 Finnhub endpoint 标记为已知 403（进程内有效）"""
    _forbidden_endpoints.add(endpoint)
    logger.warning('[Finnhub] 端点已被标记为无权限（403），后续请求将跳过: %s', endpoint)


def is_endpoint_forbidden(endpoint: str) -> bool:
    return endpoint in _forbidden_endpoints


# ---------- 配置读取 ----------

def _get_api_key() -> str:
    """从环境变量读取 Finnhub API Key（绝对不写入日志）"""
    key = os.environ.get('FINNHUB_API_KEY', '')
    return key


def is_api_key_configured() -> bool:
    """仅用于启动检查：返回 Key 是否已配置（不返回 Key 本身）"""
    return bool(_get_api_key())


# ---------- 常量 ----------

BASE_URL = 'https://finnhub.io/api/v1'
DEFAULT_TIMEOUT = 10  # 秒
MAX_RETRIES = 3
BACKOFF_BASE = 2  # 指数退避基数（秒）

# ---------- 核心请求函数 ----------

def _request(endpoint: str, params: Optional[Dict] = None, retries: int = MAX_RETRIES) -> Optional[Dict]:
    """
    向 Finnhub 发送 GET 请求（带重试与限流处理）
    - 429: 指数退避重试
    - 5xx: 重试（不超过 retries 次）
    - 4xx: 不重试，记录参数摘要（脱敏）
    返回解析后的 JSON 字典，或 None（所有重试失败）
    """
    api_key = _get_api_key()
    if not api_key:
        logger.error('[Finnhub] FINNHUB_API_KEY 未配置，跳过请求')
        return None

    url = f"{BASE_URL}{endpoint}"
    request_params = dict(params or {})
    request_params['token'] = api_key  # key 在后端拼接，绝不在日志中打印

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=request_params, timeout=DEFAULT_TIMEOUT)

            if resp.status_code == 200:
                return resp.json()

            elif resp.status_code == 429:
                wait_time = BACKOFF_BASE ** attempt
                logger.warning(
                    '[Finnhub] 触发限流(429), endpoint=%s, attempt=%d/%d, 退避 %ds',
                    endpoint, attempt, retries, wait_time
                )
                time.sleep(wait_time)
                continue

            elif 500 <= resp.status_code < 600:
                wait_time = BACKOFF_BASE ** attempt
                logger.warning(
                    '[Finnhub] 服务端错误(%d), endpoint=%s, attempt=%d/%d, 退避 %ds',
                    resp.status_code, endpoint, attempt, retries, wait_time
                )
                time.sleep(wait_time)
                continue

            else:
                # 4xx：不重试，记录摘要（脱敏：不打印 token）
                safe_params = {k: v for k, v in request_params.items() if k != 'token'}
                if resp.status_code == 403:
                    # 403 = 无访问权限
                    # 仅对已知套餐限制的端点做进程内标记（避免重复请求）
                    # /quote 的 403 可能是 symbol 级别（如 A股不支持），不标记整个端点
                    _PLAN_RESTRICTED = {'/stock/candle', '/stock/candle_compressed', '/stock/financials', '/stock/financials-reported'}
                    if endpoint in _PLAN_RESTRICTED:
                        logger.warning(
                            '[Finnhub] 无访问权限(403), endpoint=%s —— 免费版套餐限制，已标记端点后续跳过',
                            endpoint
                        )
                        mark_endpoint_forbidden(endpoint)
                    else:
                        logger.warning(
                            '[Finnhub] 无访问权限(403), endpoint=%s, symbol=%s —— 该标的无数据或需要付费套餐',
                            endpoint, safe_params.get('symbol', '?')
                        )
                else:
                    logger.error(
                        '[Finnhub] 客户端错误(%d), endpoint=%s, params=%s, response=%s',
                        resp.status_code, endpoint, safe_params, resp.text[:200]
                    )
                return None

        except requests.exceptions.Timeout:
            logger.warning('[Finnhub] 请求超时, endpoint=%s, attempt=%d/%d', endpoint, attempt, retries)
            time.sleep(BACKOFF_BASE ** attempt)

        except requests.exceptions.RequestException as exc:
            logger.error('[Finnhub] 请求异常, endpoint=%s, error=%s', endpoint, str(exc))
            return None

    logger.error('[Finnhub] 重试耗尽，放弃请求: endpoint=%s', endpoint)
    return None


# ---------- 行情 API ----------

def get_quote(symbol: str) -> Optional[Dict]:
    """
    获取单只股票最新行情（对应接口文档 6.4）
    Finnhub /quote 返回: c(最新价), d(涨跌额), dp(涨跌幅%), h, l, o, pc, t
    """
    data = _request('/quote', {'symbol': symbol})
    if data is None:
        return None

    # Finnhub 行情正常时 c > 0；c = 0 通常意味着无数据
    if data.get('c', 0) == 0:
        logger.debug('[Finnhub] get_quote: %s 无行情数据（c=0）', symbol)
        return None

    return {
        'price': data.get('c'),
        'change_amount': data.get('d'),
        'change_pct': data.get('dp'),
        'open': data.get('o'),
        'high': data.get('h'),
        'low': data.get('l'),
        'prev_close': data.get('pc'),
        'quote_time': _ts_to_datetime(data.get('t')),
        'source': 'finnhub',
    }


def get_candles(symbol: str, resolution: str, from_ts: int, to_ts: int) -> Optional[Dict]:
    """
    获取 K 线数据（对应接口文档 6.5）
    Finnhub /stock/candle 返回: c, h, l, o, v, t（均为数组），s（状态）
    resolution: 1/5/15/30/60/D/W/M
    注意：Finnhub 免费版不支持此接口（返回 403），首次 403 后进程内不再重复请求。
    """
    if is_endpoint_forbidden('/stock/candle'):
        logger.debug('[Finnhub] get_candles: /stock/candle 已知无权限，跳过请求（%s）', symbol)
        return None

    data = _request('/stock/candle', {
        'symbol': symbol,
        'resolution': resolution,
        'from': from_ts,
        'to': to_ts,
    })
    if data is None or data.get('s') != 'ok':
        logger.debug('[Finnhub] get_candles: %s [%s] 无数据或状态非ok, s=%s', symbol, resolution, data.get('s') if data else 'None')
        return None

    times = data.get('t', [])
    opens = data.get('o', [])
    highs = data.get('h', [])
    lows = data.get('l', [])
    closes = data.get('c', [])
    volumes = data.get('v', [])

    items = []
    for i in range(len(times)):
        items.append({
            'k_time': _ts_to_datetime(times[i]),
            'open': opens[i] if i < len(opens) else None,
            'high': highs[i] if i < len(highs) else None,
            'low': lows[i] if i < len(lows) else None,
            'close': closes[i] if i < len(closes) else None,
            'volume': int(volumes[i]) if i < len(volumes) else None,
        })

    return {'resolution': resolution, 'items': items}


def get_stock_symbols(exchange: str) -> Optional[List[Dict]]:
    """
    获取交易所股票列表（用于 Symbols Sync 任务）
    exchange: US / HK 等（Finnhub 格式）
    A 股通常 exchange='SS'(上交所)/'SZ'(深交所)
    返回列表：[{symbol, description, displaySymbol, type, currency, ...}]
    """
    data = _request('/stock/symbol', {'exchange': exchange})
    if not isinstance(data, list):
        logger.error('[Finnhub] get_stock_symbols: exchange=%s 返回格式异常', exchange)
        return None
    return data


def get_company_profile(symbol: str) -> Optional[Dict]:
    """
    获取公司基本信息（名称、行业、Logo、货币、市值等）
    用于补全 Asset 的 description/industry/logo_url/currency 字段
    """
    data = _request('/stock/profile2', {'symbol': symbol})
    if not data:
        return None
    return {
        'name': data.get('name', ''),
        'industry': data.get('finnhubIndustry', ''),
        'logo_url': data.get('logo', ''),
        'currency': data.get('currency', ''),
        'description': data.get('weburl', ''),
        'exchange': data.get('exchange', ''),
    }


# ---------- 工具函数 ----------

def _ts_to_datetime(ts: Optional[int]) -> Optional[datetime]:
    """Unix 时间戳 → UTC datetime"""
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def datetime_to_ts(dt: datetime) -> int:
    """datetime → Unix 时间戳"""
    return int(dt.timestamp())


def now_ts() -> int:
    """当前 UTC Unix 时间戳"""
    return int(datetime.now(tz=timezone.utc).timestamp())
