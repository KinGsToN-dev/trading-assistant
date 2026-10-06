"""
Единая точка входа для рыночных данных с fallback между источниками.

Приоритет:
1. Biquote (форекс + золото + крипта) — основной, без ключа
2. Binance (только крипта) — резерв №1
3. Twelve Data (форекс + крипта) — резерв №2, нужен ключ
4. XAUS.com (только золото) — резерв №3, без ключа
5. MT5 (локально) — последний рубеж

Пока реализованы только 1, 2, 5. Добавим 3-4 позже, если понадобится.
"""
import logging
from . import biquote, binance

logger = logging.getLogger(__name__)


def fetch_prices(symbols: list) -> dict:
    """
    Пытается получить цены из источников по порядку.
    Возвращает {symbol: {'price': Decimal, 'change_24h': Decimal}}.
    """
    if not symbols:
        return {}

    # 1. Biquote — форекс, золото, крипта
    try:
        result = biquote.fetch_prices(symbols)
        if result:
            logger.info(f'[prices] Biquote: {len(result)}/{len(symbols)}')
            missing = [s for s in symbols if s not in result]
            if not missing:
                return result
            # Дозаполняем из Binance
            try:
                binance_result = binance.fetch_prices(missing)
                result.update(binance_result)
            except Exception as e:
                logger.error(f'[prices] Binance fallback error: {e}')
            return result
    except Exception as e:
        logger.error(f'[prices] Biquote error: {e}')

    # 2. Binance — только крипта
    try:
        result = binance.fetch_prices(symbols)
        if result:
            logger.info(f'[prices] Binance: {len(result)}/{len(symbols)}')
            return result
    except Exception as e:
        logger.error(f'[prices] Binance error: {e}')

    # 3. MT5 — локально (для облака недоступно)
    try:
        from . import mt5_prices
        result = mt5_prices.fetch_prices(symbols)
        if result:
            logger.info(f'[prices] MT5: {len(result)}/{len(symbols)}')
            return result
    except Exception as e:
        logger.error(f'[prices] MT5 error: {e}')

    return {}


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

    # 2. Binance — маппинг интервалов
    try:
        binance_interval = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '4h', '1d': '1d',
        }.get(interval, '1h')

        candles = binance.fetch_candles(symbol, interval=binance_interval, limit=limit)
        if candles:
            logger.info(f'[candles] Binance {symbol} {interval}: {len(candles)}')
            return candles
    except Exception as e:
        logger.error(f'[candles] Binance error for {symbol}: {e}')

    return []