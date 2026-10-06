import pytest
from decimal import Decimal
from unittest.mock import patch
from django.urls import reverse
from market_data.models import PriceSnapshot, Candle


pytestmark = pytest.mark.django_db


def test_watchlist_creates_prices(api_client):
    """РџСѓСЃС‚РѕР№ watchlist в†’ РґРµСЂРіР°РµС‚ CoinGecko Рё СЃРѕР·РґР°С‘С‚ С†РµРЅС‹."""
    fake_prices = {
        'BTCUSDT': {'price': Decimal('50000'), 'change_24h': Decimal('2.5')},
        'ETHUSDT': {'price': Decimal('3000'), 'change_24h': Decimal('-1.2')},
    }
    with patch('market_data.services.coingecko.fetch_prices', return_value=fake_prices):
        with patch('market_data.services.mt5_prices.fetch_prices', return_value={}):
            r = api_client.get(reverse('market-watchlist'))
    assert r.status_code == 200
    symbols = {item['symbol'] for item in r.data}
    assert 'BTCUSDT' in symbols
    assert 'ETHUSDT' in symbols


def test_price_detail_found(api_client):
    PriceSnapshot.objects.create(
        symbol='BTCUSDT', price=Decimal('50000'),
        change_24h=Decimal('1.0'), source='coingecko',
    )
    r = api_client.get(reverse('market-price-detail', args=['BTCUSDT']))
    assert r.status_code == 200
    assert r.data['symbol'] == 'BTCUSDT'
    assert Decimal(r.data['price']) == Decimal('50000')


def test_price_detail_not_found(api_client):
    with patch('market_data.services.coingecko.fetch_prices', return_value={}):
        with patch('market_data.services.mt5_prices.fetch_prices', return_value={}):
            r = api_client.get(reverse('market-price-detail', args=['UNKNOWN']))
    assert r.status_code == 404


def test_price_detail_lowercase_symbol(api_client):
    PriceSnapshot.objects.create(
        symbol='ETHUSDT', price=Decimal('3000'),
        change_24h=Decimal('0'), source='coingecko',
    )
    r = api_client.get(reverse('market-price-detail', args=['ethusdt']))
    assert r.status_code == 200
    assert r.data['symbol'] == 'ETHUSDT'


def test_candles_from_db(api_client):
    """Если свечи есть в БД - CoinGecko не дергается."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    for i in range(15):
        Candle.objects.create(
            symbol='BTCUSDT', timeframe='1h',
            timestamp=now - timedelta(hours=i),
            open=Decimal('50000'), high=Decimal('50100'),
            low=Decimal('49900'), close=Decimal('50050'),
            volume=Decimal('10'),
        )
    r = api_client.get(reverse('market-candles', args=['BTCUSDT']) + '?days=7')
    assert r.status_code == 200
    assert len(r.data) == 15


def test_candles_fetch_from_api(api_client):
    """Если свечей нет — идёт запрос к Biquote."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    fake_candles = [
        {
            'timestamp': now - timedelta(hours=i),
            'open': Decimal('50000'), 'high': Decimal('50100'),
            'low': Decimal('49900'), 'close': Decimal('50050'),
            'volume': Decimal('0'),
        }
        for i in range(12)
    ]
    # Патчим Biquote — основной источник в price_service
    with patch('market_data.services.biquote.fetch_candles', return_value=fake_candles):
        with patch('market_data.services.binance.fetch_candles', return_value=[]):
            r = api_client.get(reverse('market-candles', args=['BTCUSDT']) + '?interval=1h&limit=12')
    assert r.status_code == 200
    assert len(r.data) == 12


def test_candles_not_found(api_client):
    with patch('market_data.services.coingecko.fetch_candles', return_value=[]):
        r = api_client.get(reverse('market-candles', args=['UNKNOWN']) + '?days=7')
    assert r.status_code == 404


def test_manual_refresh_requires_auth(api_client):
    r = api_client.post(reverse('market-refresh'))
    assert r.status_code == 401


def test_manual_refresh_with_auth(auth_client):
    with patch('market_data.views.refresh_prices', return_value=6):
        r = auth_client.post(reverse('market-refresh'))
    assert r.status_code == 200
    assert r.data['updated'] == 6