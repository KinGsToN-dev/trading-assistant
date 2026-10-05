import pytest
from decimal import Decimal
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from trades.models import Trade

User = get_user_model()
pytestmark = pytest.mark.django_db

MT5_URL = reverse('trade-import-mt5')


def mt5_payload(external_id='12345', **kwargs):
    data = {
        'external_id': external_id,
        'symbol': 'EURUSD',
        'side': 'buy',
        'status': 'closed',
        'entry_price': '1.0850',
        'exit_price': '1.0900',
        'quantity': '0.1',
        'pnl': '50.00',
        'commission': '2.50',
        'opened_at': '2026-10-04T10:00:00Z',
        'closed_at': '2026-10-04T14:30:00Z',
        'strategy': 'trend',
        'notes': 'Demo trade',
    }
    data.update(kwargs)
    return data


def test_import_requires_api_key(api_client, user):
    r = api_client.post(MT5_URL, {'trades': [mt5_payload()]}, format='json')
    assert r.status_code == 403


def test_import_with_wrong_api_key(api_client, user):
    r = api_client.post(MT5_URL, {'trades': [mt5_payload()]}, format='json', HTTP_X_API_KEY='wrong-key')
    assert r.status_code == 403


def test_import_success(api_client, user):
    user.is_superuser = True
    user.save()
    r = api_client.post(
        MT5_URL,
        {'trades': [mt5_payload('ext-1'), mt5_payload('ext-2', symbol='GBPUSD')]},
        format='json', HTTP_X_API_KEY=settings.MT5_API_TOKEN,
    )
    assert r.status_code == 200
    assert r.data['created'] == 2
    assert r.data['updated'] == 0
    assert Trade.objects.filter(source='mt5').count() == 2


def test_import_idempotency(api_client, user):
    user.is_superuser = True
    user.save()

    r1 = api_client.post(MT5_URL, {'trades': [mt5_payload('idem-1')]}, format='json', HTTP_X_API_KEY=settings.MT5_API_TOKEN)
    assert r1.status_code == 200
    assert r1.data['created'] == 1

    r2 = api_client.post(
        MT5_URL,
        {'trades': [mt5_payload('idem-1', exit_price='1.1000', pnl='150.00')]},
        format='json', HTTP_X_API_KEY=settings.MT5_API_TOKEN,
    )
    assert r2.status_code == 200
    assert r2.data['created'] == 0
    assert r2.data['updated'] == 1
    assert Trade.objects.filter(source='mt5', external_id='idem-1').count() == 1
    t = Trade.objects.get(source='mt5', external_id='idem-1')
    assert t.exit_price == Decimal('1.1000')
    assert t.pnl == Decimal('150.00')


def test_import_does_not_recalc_pnl_from_mt5(api_client, user):
    user.is_superuser = True
    user.save()
    r = api_client.post(
        MT5_URL,
        {'trades': [mt5_payload('pnl-test', entry_price='1.0850', exit_price='1.0900',
                                quantity='0.1', pnl='999.99')]},
        format='json', HTTP_X_API_KEY=settings.MT5_API_TOKEN,
    )
    assert r.status_code == 200
    t = Trade.objects.get(source='mt5', external_id='pnl-test')
    assert t.pnl == Decimal('999.99')


def test_import_invalid_data_returns_errors(api_client, user):
    user.is_superuser = True
    user.save()
    bad = mt5_payload('bad-1')
    bad['entry_price'] = '-100'
    r = api_client.post(MT5_URL, {'trades': [bad]}, format='json', HTTP_X_API_KEY=settings.MT5_API_TOKEN)
    assert r.status_code == 200
    assert r.data['created'] == 0
    assert len(r.data['errors']) == 1
    assert r.data['errors'][0]['external_id'] == 'bad-1'