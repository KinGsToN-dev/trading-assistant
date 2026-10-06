"""
Binance API — крипто-котировки.
Не блокирует облачные IP. Бесплатно, без API-ключа.
"""
import logging
from decimal import Decimal
import requests

logger = logging.getLogger(__name__)

# Символы Binance
SYMBOL_MAP = {
    'BTCUSDT': 'BTCUSDT', 'BTC': 'BTCUSDT',
    'ETHUSDT': 'ETHUSDT', 'ETH': 'ETHUSDT',
    'SOLUSDT': 'SOLUSDT', 'SOL': 'SOLUSDT',
    'BNBUSDT': 'BNBUSDT', 'BNB': 'BNBUSDT',
    'XRPUSDT': 'XRPUSDT', 'XRP': 'XRPUSDT',
    'DOGEUSDT': 'DOGEUSDT', 'DOGE': 'DOGEUSDT',
    'ADAUSDT': 'ADAUSDT', 'ADA': 'ADAUSDT',
}

BASE_URL = 'https://api.binance.com/api/v3'


def fetch_prices(symbols: list) -> dict:
    """
    Возвращает {symbol: {'price': Decimal, 'change_24h': Decimal}}.
    Один запрос ко всем символам сразу.
    """
    if not symbols:
        return {}

    result = {}
    for symbol in symbols:
        binance_sym = SYMBOL_MAP.get(symbol.upper(), symbol.upper())
        try:
            r = requests.get(
                f'{BASE_URL}/ticker/24hr',
                params={'symbol': binance_sym},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            result[symbol] = {
                'price': Decimal(str(data['lastPrice'])),
                'change_24h': Decimal(str(data['priceChangePercent'])).quantize(Decimal('0.0001')),
            }
            logger.info(f'Binance {symbol}: {data["lastPrice"]}')
        except requests.RequestException as e:
            logger.error(f'Binance error for {symbol}: {e}')
            continue

    return result


def fetch_candles(symbol: str, days: int = 7) -> list:
    """
    Свечи через Binance Klines API.
    days: 1 = 5m, 7 = 1h, 30 = 4h, 365 = 1d
    """
    from datetime import datetime, timezone

    binance_sym = SYMBOL_MAP.get(symbol.upper(), symbol.upper())

    # Интервал по дням
    if days <= 1:
        interval = '5m'
        limit = 288
    elif days <= 7:
        interval = '1h'
        limit = 168
    elif days <= 30:
        interval = '4h'
        limit = 180
    else:
        interval = '1d'
        limit = 365

    try:
        r = requests.get(
            f'{BASE_URL}/klines',
            params={
                'symbol': binance_sym,
                'interval': interval,
                'limit': limit,
            },
            timeout=10,
        )
        r.raise_for_status()
        raw = r.json()
    except requests.RequestException as e:
        logger.error(f'Binance klines error for {symbol}: {e}')
        return []

    candles = []
    for item in raw:
        # Binance: [openTime, open, high, low, close, volume, closeTime, ...]
        ts = int(item[0])
        candles.append({
            'timestamp': datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
            'open': Decimal(str(item[1])),
            'high': Decimal(str(item[2])),
            'low': Decimal(str(item[3])),
            'close': Decimal(str(item[4])),
            'volume': Decimal(str(item[5])),
        })

    return candles