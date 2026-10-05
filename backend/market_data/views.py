import logging
from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import PriceSnapshot, Candle
from .serializers import PriceSnapshotSerializer, CandleSerializer
from .services import coingecko, mt5_prices

logger = logging.getLogger(__name__)


# Символы, которые обновляются автоматически
CRYPTO_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT']
FOREX_SYMBOLS = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY']


def refresh_prices(symbols=None):
    """Обновляет цены в БД. Используется scheduler'ом и API."""
    crypto = symbols or CRYPTO_SYMBOLS
    forex = FOREX_SYMBOLS

    updated = 0

    # Крипта
    crypto_data = coingecko.fetch_prices(crypto)
    for symbol, data in crypto_data.items():
        PriceSnapshot.objects.update_or_create(
            symbol=symbol,
            defaults={
                'price': data['price'],
                'change_24h': data['change_24h'],
                'source': 'coingecko',
            },
        )
        updated += 1

    # Форекс (если MT5 доступен локально)
    forex_data = mt5_prices.fetch_prices(forex)
    for symbol, data in forex_data.items():
        PriceSnapshot.objects.update_or_create(
            symbol=symbol,
            defaults={
                'price': data['price'],
                'change_24h': data['change_24h'],
                'source': 'mt5',
            },
        )
        updated += 1

    return updated


@api_view(['GET'])
@permission_classes([AllowAny])
def watchlist(request):
    """Список избранных символов с ценами."""
    symbols = CRYPTO_SYMBOLS + FOREX_SYMBOLS
    # Дозаполняем недостающие
    existing = set(PriceSnapshot.objects.filter(symbol__in=symbols).values_list('symbol', flat=True))
    missing = [s for s in symbols if s not in existing]
    if missing:
        refresh_prices(missing)

    qs = PriceSnapshot.objects.filter(symbol__in=symbols).order_by('symbol')
    return Response(PriceSnapshotSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def price_detail(request, symbol):
    """Текущая цена символа."""
    snapshot = PriceSnapshot.objects.filter(symbol=symbol.upper()).first()
    if not snapshot:
        # Пробуем обновить один раз
        refresh_prices([symbol.upper()])
        snapshot = PriceSnapshot.objects.filter(symbol=symbol.upper()).first()

    if not snapshot:
        return Response(
            {'detail': f'Символ {symbol} не найден'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(PriceSnapshotSerializer(snapshot).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def candles(request, symbol):
    """
    Свечи для графика.
    ?days=1|7|30|365 — период (1=5мин, 7=часовые, 30=дневные)
    """
    symbol = symbol.upper()
    days = int(request.query_params.get('days', 7))

    # Пробуем взять из БД
    timeframe = '5m' if days == 1 else '1h' if days == 7 else '1d'
    qs = Candle.objects.filter(symbol=symbol, timeframe=timeframe).order_by('timestamp')[:500]

    if qs.count() < 10:
        # Забираем с CoinGecko
        data = coingecko.fetch_candles(symbol, days=days)
        if data:
            # Сохраняем в БД
            for c in data:
                Candle.objects.update_or_create(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=c['timestamp'],
                    defaults={
                        'open': c['open'],
                        'high': c['high'],
                        'low': c['low'],
                        'close': c['close'],
                        'volume': c['volume'],
                    },
                )
            qs = Candle.objects.filter(symbol=symbol, timeframe=timeframe).order_by('timestamp')[:500]

    if not qs:
        return Response(
            {'detail': f'Нет свечей для {symbol}'},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(CandleSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_refresh(request):
    """Ручное обновление цен (только для авторизованных)."""
    count = refresh_prices()
    return Response({'updated': count})