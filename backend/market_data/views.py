import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import PriceSnapshot, Candle
from .serializers import PriceSnapshotSerializer, CandleSerializer
from .services import price_service

logger = logging.getLogger(__name__)


# РЎРёРјРІРѕР»С‹, РєРѕС‚РѕСЂС‹Рµ РѕР±РЅРѕРІР»СЏСЋС‚СЃСЏ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё
CRYPTO_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT']
FOREX_SYMBOLS = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY']


def refresh_prices(symbols=None):
    """РћР±РЅРѕРІР»СЏРµС‚ С†РµРЅС‹ РІ Р‘Р” С‡РµСЂРµР· price_service (Biquote в†’ Binance в†’ MT5)."""
    crypto = symbols or CRYPTO_SYMBOLS
    forex = FOREX_SYMBOLS

    updated = 0

    all_prices = price_service.fetch_prices(crypto + forex)
    for symbol, data in all_prices.items():
        source = 'biquote' if symbol in forex or symbol in crypto else 'unknown'
        PriceSnapshot.objects.update_or_create(
            symbol=symbol,
            defaults={
                'price': data['price'],
                'change_24h': data['change_24h'],
                'source': source,
            },
        )
        updated += 1

    return updated


@api_view(['GET'])
@permission_classes([AllowAny])
def watchlist(request):
    """РЎРїРёСЃРѕРє РёР·Р±СЂР°РЅРЅС‹С… СЃРёРјРІРѕР»РѕРІ СЃ С†РµРЅР°РјРё."""
    symbols = CRYPTO_SYMBOLS + FOREX_SYMBOLS
    existing = set(PriceSnapshot.objects.filter(symbol__in=symbols).values_list('symbol', flat=True))
    missing = [s for s in symbols if s not in existing]
    if missing:
        refresh_prices()

    qs = PriceSnapshot.objects.filter(symbol__in=symbols).order_by('symbol')
    return Response(PriceSnapshotSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def price_detail(request, symbol):
    """РўРµРєСѓС‰Р°СЏ С†РµРЅР° СЃРёРјРІРѕР»Р°."""
    snapshot = PriceSnapshot.objects.filter(symbol=symbol.upper()).first()
    if not snapshot:
        refresh_prices()
        snapshot = PriceSnapshot.objects.filter(symbol=symbol.upper()).first()

    if not snapshot:
        return Response(
            {'detail': f'РЎРёРјРІРѕР» {symbol} РЅРµ РЅР°Р№РґРµРЅ'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(PriceSnapshotSerializer(snapshot).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def candles(request, symbol):
    """
    РЎРІРµС‡Рё РґР»СЏ РіСЂР°С„РёРєР°.
    ?interval=1h|4h|1d|5m|15m|30m
    ?limit=500
    """
    symbol = symbol.upper()
    interval = request.query_params.get('interval', '1h')
    limit = int(request.query_params.get('limit', 500))

    # РџСЂРѕРІРµСЂСЏРµРј РґРѕРїСѓСЃС‚РёРјС‹Рµ РёРЅС‚РµСЂРІР°Р»С‹
    if interval not in ('1m', '5m', '15m', '30m', '1h', '4h', '1d'):
        interval = '1h'

    # РџСЂРѕР±СѓРµРј РёР· Р‘Р”
    qs = Candle.objects.filter(
        symbol=symbol, timeframe=interval
    ).order_by('timestamp')[:limit]

    if qs.count() < 10:
        # Р—Р°Р±РёСЂР°РµРј РёР· price_service
        data = price_service.fetch_candles(symbol, interval=interval, limit=limit)
        if data:
            for c in data:
                Candle.objects.update_or_create(
                    symbol=symbol,
                    timeframe=interval,
                    timestamp=c['timestamp'],
                    defaults={
                        'open': c['open'],
                        'high': c['high'],
                        'low': c['low'],
                        'close': c['close'],
                        'volume': c['volume'],
                    },
                )
            qs = Candle.objects.filter(
                symbol=symbol, timeframe=interval
            ).order_by('timestamp')[:limit]

    if not qs:
        return Response(
            {'detail': f'РќРµС‚ СЃРІРµС‡РµР№ РґР»СЏ {symbol}'},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(CandleSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_refresh(request):
    """Р СѓС‡РЅРѕРµ РѕР±РЅРѕРІР»РµРЅРёРµ С†РµРЅ."""
    count = refresh_prices()
    return Response({'updated': count})