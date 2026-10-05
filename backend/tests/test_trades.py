import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from django.urls import reverse
from django.contrib.auth import get_user_model
from trades.models import Trade

User = get_user_model()
pytestmark = pytest.mark.django_db


def make_trade(user, **kwargs):
    defaults = {
        'user': user,
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'status': 'open',
        'entry_price': Decimal('50000'),
        'quantity': Decimal('0.1'),
        'opened_at': datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return Trade.objects.create(**defaults)


def test_create_trade(auth_client, user):
    url = reverse('trade-list')
    data = {
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'status': 'open',
        'entry_price': '50000',
        'quantity': '0.1',
        'opened_at': datetime.now(timezone.utc).isoformat(),
    }
    r = auth_client.post(url, data, format='json')
    assert r.status_code == 201, r.data
    assert r.data['symbol'] == 'BTCUSDT'
    assert Trade.objects.filter(user=user).count() == 1


def test_create_trade_invalid_price(auth_client):
    url = reverse('trade-list')
    data = {
        'symbol': 'BTCUSDT', 'side': 'buy', 'status': 'open',
        'entry_price': '-100', 'quantity': '0.1',
        'opened_at': datetime.now(timezone.utc).isoformat(),
    }
    r = auth_client.post(url, data, format='json')
    assert r.status_code == 400


def test_create_trade_closed_without_exit(auth_client):
    url = reverse('trade-list')
    data = {
        'symbol': 'BTCUSDT', 'side': 'buy', 'status': 'closed',
        'entry_price': '50000', 'quantity': '0.1',
        'opened_at': datetime.now(timezone.utc).isoformat(),
    }
    r = auth_client.post(url, data, format='json')
    assert r.status_code == 400


def test_list_own_trades_only(auth_client, user):
    make_trade(user, symbol='BTCUSDT')
    other = User.objects.create_user(email='other@example.com', username='other', password='x')
    make_trade(other, symbol='ETHUSDT')

    r = auth_client.get(reverse('trade-list'))
    assert r.status_code == 200
    symbols = [t['symbol'] for t in r.data['results']]
    assert 'BTCUSDT' in symbols
    assert 'ETHUSDT' not in symbols


def test_cannot_read_other_users_trade(auth_client, user):
    other = User.objects.create_user(email='other@example.com', username='other', password='x')
    trade = make_trade(other, symbol='ETHUSDT')

    r = auth_client.get(reverse('trade-detail', args=[trade.id]))
    assert r.status_code == 404


def test_cannot_update_other_users_trade(auth_client):
    other = User.objects.create_user(email='other@example.com', username='other', password='x')
    trade = make_trade(other)

    r = auth_client.patch(reverse('trade-detail', args=[trade.id]), {'symbol': 'X'}, format='json')
    assert r.status_code == 404


def test_pnl_calculated_on_close(auth_client, user):
    trade = make_trade(user, side='buy', entry_price=Decimal('100'), quantity=Decimal('10'))
    trade.exit_price = Decimal('110')
    trade.status = 'closed'
    trade.closed_at = datetime.now(timezone.utc)
    trade.save()
    trade.refresh_from_db()
    # (110 - 100) * 10 = 100
    assert trade.pnl == Decimal('100.00000000')


def test_pnl_short_position(auth_client, user):
    trade = make_trade(user, side='sell', entry_price=Decimal('100'), quantity=Decimal('10'))
    trade.exit_price = Decimal('90')
    trade.status = 'closed'
    trade.save()
    trade.refresh_from_db()
    # (100 - 90) * 10 = 100
    assert trade.pnl == Decimal('100.00000000')


def test_filter_by_symbol(auth_client, user):
    make_trade(user, symbol='BTCUSDT')
    make_trade(user, symbol='ETHUSDT')
    make_trade(user, symbol='BTCUSDT')

    r = auth_client.get(reverse('trade-list') + '?symbol=BTCUSDT')
    assert r.status_code == 200
    assert r.data['count'] == 2


def test_filter_by_status(auth_client, user):
    make_trade(user, status='open')
    make_trade(user, status='open')
    make_trade(user, status='closed', exit_price=Decimal('100'), closed_at=datetime.now(timezone.utc))

    r = auth_client.get(reverse('trade-list') + '?status=open')
    assert r.data['count'] == 2


def test_search_by_notes(auth_client, user):
    make_trade(user, notes='Пробой уровня сопротивления')
    make_trade(user, notes='Отскок от поддержки')

    r = auth_client.get(reverse('trade-list') + '?search=сопротивления')
    assert r.data['count'] == 1


def test_stats_endpoint(auth_client, user):
    now = datetime.now(timezone.utc)
    # Прибыльная: buy 100 → 110 × 10 = +100
    make_trade(
        user, status='closed', side='buy',
        entry_price=Decimal('100'), exit_price=Decimal('110'),
        quantity=Decimal('10'), closed_at=now,
    )
    # Убыточная: buy 100 → 90 × 10 = -100
    make_trade(
        user, status='closed', side='buy',
        entry_price=Decimal('100'), exit_price=Decimal('90'),
        quantity=Decimal('10'), closed_at=now,
    )
    # Открытая
    make_trade(user, status='open')

    r = auth_client.get(reverse('trade-stats'))
    assert r.status_code == 200
    assert r.data['total_trades'] == 3
    assert r.data['open_trades'] == 1
    assert r.data['closed_trades'] == 2
    assert r.data['wins'] == 1
    assert r.data['losses'] == 1
    assert r.data['win_rate'] == 50.0
    assert float(r.data['total_pnl']) == 0.0  # +100 - 100


def test_trades_require_auth(api_client):
    r = api_client.get(reverse('trade-list'))
    assert r.status_code == 401