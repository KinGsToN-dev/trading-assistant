"""
Единая точка входа для рыночных данных с fallback между источниками.

Приоритет:
1. Biquote (форекс + золото + крипта) — основной, без ключа
2. Binance (только крипта) — резерв №1
3. MT5 (локально) — последний рубеж
"""
import logging
from decimal import Decimal
from . import biquote, binance

logger = logging.getLogger(__name__)


# Символы, которые Biquote отдаёт как крипту
CRYPTO_SYMBOLS = {
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT',
    'XRPUSDT', 'DOGEUSDT', 'ADAUSDT',
}


def fetch_prices(symbols: list) -> dict:
    """
    Пытается получить цены из источников по порядку.
    Возвращает {symbol: {'price': Decimal, 'change_24h': Decimal, 'source': str}}.
    """
    if not symbols:
        return {}

    result = {}

    # 1. Biquote
    try:
        biquote_result = biquote.fetch_prices(symbols)
        for sym, data in biquote_result.items():
            data['source'] = 'biquote'
            result[sym] = data
        logger.info(f'[prices] Biquote: {len(biquote_result)}/{len(symbols)}')
    except Exception as e:
        logger.error(f'[prices] Biquote error: {e}')

    # 2. Binance — ТОЛЬКО для недостающих
    missing = [s for s in symbols if s not in result]
    if missing:
        try:
            binance_result = binance.fetch_prices(missing)
            for sym, data in binance_result.items():
                data['source'] = 'binance'
                result[sym] = data
            logger.info(f'[prices] Binance fallback: {len(binance_result)}/{len(missing)}')
        except Exception as e:
            logger.error(f'[prices] Binance error: {e}')

    # 3. MT5 — последний рубеж
    missing = [s for s in symbols if s not in result]
    if missing:
        try:
            from . import mt5_prices
            mt5_result = mt5_prices.fetch_prices(missing)
            for sym, data in mt5_result.items():
                data['source'] = 'mt5'
                result[sym] = data
        except Exception as e:
            logger.error(f'[prices] MT5 error: {e}')

    return result


def fetch_candles(symbol: str, interval: str = '1h', limit: int = 500) -> list:
    """
    Возвращает свечи OHLC. Таймфреймы: 1m, 5m, 15m, 30m, 1h, 4h, 1d.
    """
    # 1. Biquote
    try:
        candles = biquote.fetch_candles(symbol, interval=interval, limit=limit)
        if candles:
            logger.info(f'[candles] Biquote {symbol} {interval}: {len(candles)}')
            return candles
    except Exception as e:
        logger.error(f'[candles] Biquote error for {symbol}: {e}')

    # 2. Binance
    try:
        candles = binance.fetch_candles(symbol, interval=interval, limit=limit)
        if candles:
            logger.info(f'[candles] Binance {symbol} {interval}: {len(candles)}')
            return candles
    except Exception as e:
        logger.error(f'[candles] Binance error for {symbol}: {e}')

    return []