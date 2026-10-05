"""
CoinGecko API вЂ” РєСЂРёРїС‚Рѕ-РєРѕС‚РёСЂРѕРІРєРё. Р‘РµСЃРїР»Р°С‚РЅРѕ, Р±РµР· РєР»СЋС‡Р° (30 req/min).
"""
import logging
from decimal import Decimal
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# CoinGecko РёСЃРїРѕР»СЊР·СѓРµС‚ СЃРІРѕРё ID РґР»СЏ РјРѕРЅРµС‚
SYMBOL_MAP = {
    'BTCUSDT': 'bitcoin',
    'BTC': 'bitcoin',
    'ETHUSDT': 'ethereum',
    'ETH': 'ethereum',
    'SOLUSDT': 'solana',
    'SOL': 'solana',
    'BNBUSDT': 'binancecoin',
    'BNB': 'binancecoin',
    'XRPUSDT': 'ripple',
    'XRP': 'ripple',
    'ADAUSDT': 'cardano',
    'ADA': 'cardano',
    'DOGEUSDT': 'dogecoin',
    'DOGE': 'dogecoin',
    'TONUSDT': 'the-open-network',
    'TON': 'the-open-network',
    'NOTUSDT': 'notcoin',
    'NOT': 'notcoin',
}

BASE_URL = 'https://api.coingecko.com/api/v3'


def _to_coingecko_id(symbol: str) -> str:
    """BTCUSDT в†’ bitcoin. Р•СЃР»Рё РЅРµ РЅР°Р№РґРµРЅРѕ вЂ” РїС‹С‚Р°РµС‚СЃСЏ СѓРіР°РґР°С‚СЊ РїРѕ lowercase."""
    return SYMBOL_MAP.get(symbol.upper(), symbol.lower())


def fetch_prices(symbols: list) -> dict:
    """
    Р’РѕР·РІСЂР°С‰Р°РµС‚ {symbol: {'price': Decimal, 'change_24h': Decimal}}.
    РћРґРёРЅ Р·Р°РїСЂРѕСЃ вЂ” РІСЃРµ СЃРёРјРІРѕР»С‹.
    """
    if not symbols:
        return {}

    ids_map = {s: _to_coingecko_id(s) for s in symbols}
    ids = ','.join(set(ids_map.values()))

    try:
        r = requests.get(
            f'{BASE_URL}/simple/price',
            params={
                'ids': ids,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        logger.error(f'CoinGecko error: {e}')
        return {}

    result = {}
    for symbol, cg_id in ids_map.items():
        item = data.get(cg_id, {})
        if 'usd' in item:
            result[symbol] = {
                'price': Decimal(str(item['usd'])),
                'change_24h': Decimal(str(item.get('usd_24h_change', 0))).quantize(Decimal('0.0001')),
            }
    return result


def fetch_candles(symbol: str, days: int = 1) -> list:
    """
    РЎРІРµС‡Рё РґР»СЏ РіСЂР°С„РёРєР°. Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРїРёСЃРѕРє dict СЃ OHLCV.
    days: 1 (5-РјРёРЅСѓС‚РЅС‹Рµ), 7 (С‡Р°СЃРѕРІС‹Рµ), 30 (РґРЅРµРІРЅС‹Рµ), 365 (РЅРµРґРµР»СЊРЅС‹Рµ).
    """
    cg_id = _to_coingecko_id(symbol)
    try:
        r = requests.get(
            f'{BASE_URL}/coins/{cg_id}/ohlc',
            params={'vs_currency': 'usd', 'days': days},
            timeout=10,
        )
        r.raise_for_status()
        raw = r.json()  # [[timestamp_ms, open, high, low, close], ...]
    except requests.RequestException as e:
        logger.error(f'CoinGecko candles error: {e}')
        return []

    candles = []
    for ts, o, h, l, c in raw:
        candles.append({
            'timestamp': datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
            'open': Decimal(str(o)),
            'high': Decimal(str(h)),
            'low': Decimal(str(l)),
            'close': Decimal(str(c)),
            'volume': Decimal('0'),
        })
    return candles