"""
Получение цен форекс/металлов через локальный MT5 (Windows-only).
На сервере/CI импорт не падает — просто возвращает {}.
"""
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.info('MetaTrader5 not installed — MT5 prices disabled')


def fetch_prices(symbols: list) -> dict:
    """
    Возвращает {symbol: {'price': Decimal, 'change_24h': Decimal}}.
    """
    if not MT5_AVAILABLE or not symbols:
        return {}

    if not mt5.initialize():
        logger.warning(f'MT5 initialize failed: {mt5.last_error()}')
        return {}

    result = {}
    try:
        for symbol in symbols:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                continue
            result[symbol] = {
                'price': Decimal(str(tick.bid)),
                'change_24h': Decimal('0'),  # MT5 не даёт 24h% напрямую
            }
    finally:
        mt5.shutdown()

    return result