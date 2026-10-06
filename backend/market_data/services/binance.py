"""
Binance API — крипто-котировки.
Не блокирует облачные IP. Бесплатно, без API-ключа.
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
import requests

logger = logging.getLogger(__name__)

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
        except requests.RequestException as e:
            logger.error(f'Binance error for {symbol}: {e}')
            continue

    return result


def fetch_candles(symbol: str, interval: str = '1h', limit: int = 500) -> list:
    """
    Свечи через Binance Klines API.
    interval: '1m', '5m', '15m', '30m', '1h', '4h', '1d'
    """
    binance_sym = SYMBOL_MAP.get(symbol.upper(), symbol.upper())

    try:
        r = requests.get(
            f'{BASE_URL}/klines',
            params={
                'symbol': binance_sym,
                'interval': interval,
                'limit': min(limit, 1000),
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