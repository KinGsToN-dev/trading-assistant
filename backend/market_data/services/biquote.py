"""
Biquote вЂ” Р±РµСЃРїР»Р°С‚РЅС‹Рµ СЂС‹РЅРѕС‡РЅС‹Рµ РґР°РЅРЅС‹Рµ (С„РѕСЂРµРєСЃ, РєСЂРёРїС‚Р°, Р·РѕР»РѕС‚Рѕ) РёР· С„РёРґР° MetaTrader 5.
РќРµ С‚СЂРµР±СѓРµС‚ API-РєР»СЋС‡Р°. CORS РѕС‚РєСЂС‹С‚. Р›РёРјРёС‚ 15 000 Р·Р°РїСЂРѕСЃРѕРІ/РјРёРЅ.
"""
import logging
from decimal import Decimal
from biquote import Biquote

logger = logging.getLogger(__name__)

# РњР°РїРїРёРЅРі СЃРёРјРІРѕР»РѕРІ (Biquote РёСЃРїРѕР»СЊР·СѓРµС‚ С‚Рµ Р¶Рµ С‚РёРєРµСЂС‹, РЅРѕ РїСЂРѕРІРµСЂРёРј)
SYMBOL_MAP = {
    # Форекс и золото — Biquote использует те же тикеры
    'XAUUSD': 'XAUUSD',
    'EURUSD': 'EURUSD',
    'GBPUSD': 'GBPUSD',
    'USDJPY': 'USDJPY',
    # Крипта — Biquote использует USDT (crypto-биржи), 
    # это точнее и меньше спред, чем USD (MetaTrader 5)
    'BTCUSDT': 'BTCUSDT',
    'ETHUSDT': 'ETHUSDT',
    'SOLUSDT': 'SOLUSDT',
    'BNBUSDT': 'BNBUSDT',
    'XRPUSDT': 'XRPUSDT',
    'DOGEUSDT': 'DOGEUSDT',
    'ADAUSDT': 'ADAUSDT',
}

def _to_biquote_symbol(symbol: str) -> str:
    return SYMBOL_MAP.get(symbol.upper(), symbol.upper())


def fetch_prices(symbols: list) -> dict:
    """
    Р’РѕР·РІСЂР°С‰Р°РµС‚ {symbol: {'price': Decimal, 'change_24h': Decimal}}.
    Biquote РѕС‚РґР°С‘С‚ 'mid' РєР°Рє С†РµРЅСѓ РґР»СЏ FX/CFD, 'last' Рё 'volume' РІСЃРµРіРґР° 0.
    """
    if not symbols:
        return {}

    bq = Biquote()
    result = {}

    # Р Р°Р·Р±РёРІР°РµРј РЅР° РіСЂСѓРїРїС‹ РїРѕ 100 (Р»РёРјРёС‚ Biquote)
    for i in range(0, len(symbols), 100):
        chunk = symbols[i:i+100]
        bq_symbols = [_to_biquote_symbol(s) for s in chunk]

        try:
            ticks = bq.latest(bq_symbols)
            for original, bq_sym in zip(chunk, bq_symbols):
                tick = ticks.get(bq_sym)
                if tick is None:
                    continue
                result[original] = {
                    'price': Decimal(str(tick.get('mid', 0))),
                    'change_24h': Decimal(str(tick.get('dayDiffPercent', 0))).quantize(Decimal('0.0001')),
                }
        except Exception as e:
            logger.error(f'Biquote error for {chunk}: {e}')
            continue

    return result


def fetch_candles(symbol: str, interval: str = '1h', limit: int = 500) -> list:
    """
    Возвращает список свечей OHLC.
    interval: '1m', '5m', '15m', '30m', '1h', '4h', '1d'
    """
    from datetime import datetime, timezone

    bq_sym = _to_biquote_symbol(symbol)
    try:
        bq = Biquote()
        bars = bq.ohlc(bq_sym, interval=interval, limit=limit)
    except Exception as e:
        logger.error(f'Biquote ohlc error for {symbol}: {e}')
        return []

    candles = []
    for bar in bars:
        open_time = bar.get('openTime')
        if not open_time:
            continue
        try:
            ts = datetime.fromisoformat(open_time.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            continue

        candles.append({
            'timestamp': ts,
            'open': Decimal(str(bar.get('open', 0))),
            'high': Decimal(str(bar.get('high', 0))),
            'low': Decimal(str(bar.get('low', 0))),
            'close': Decimal(str(bar.get('close', 0))),
            'volume': Decimal(str(bar.get('tickVolume', 0) or 0)),
        })

    return candles