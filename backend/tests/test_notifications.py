import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from notifications.models import NotificationSettings, NotificationLog


pytestmark = pytest.mark.django_db


def test_settings_created_on_first_get(auth_client, user):
    r = auth_client.get(reverse('notification-settings'))
    assert r.status_code == 200
    assert NotificationSettings.objects.filter(user=user).exists()
    assert r.data['notify_new_trade'] is True


def test_settings_patch(auth_client, user):
    NotificationSettings.objects.create(user=user)
    r = auth_client.patch(
        reverse('notification-settings'),
        {'notify_new_trade': False, 'digest_hour': 12},
        format='json',
    )
    assert r.status_code == 200
    obj = NotificationSettings.objects.get(user=user)
    assert obj.notify_new_trade is False
    assert obj.digest_hour == 12


@patch('notifications.views.send_message')
def test_link_telegram_success(mock_send, auth_client, user):
    mock_send.return_value = {'ok': True, 'error': None}

    r = auth_client.post(
        reverse('notification-telegram-link'),
        {'chat_id': '123456789'},
        format='json',
    )
    assert r.status_code == 200
    obj = NotificationSettings.objects.get(user=user)
    assert obj.telegram_chat_id == '123456789'
    assert obj.telegram_linked_at is not None


@patch('notifications.views.send_message')
def test_link_telegram_failed(mock_send, auth_client, user):
    mock_send.return_value = {'ok': False, 'error': 'chat not found'}

    r = auth_client.post(
        reverse('notification-telegram-link'),
        {'chat_id': 'bad-id'},
        format='json',
    )
    assert r.status_code == 400
    obj = NotificationSettings.objects.filter(user=user).first()
    assert not obj or not obj.telegram_chat_id


@patch('notifications.views.send_to_user')
def test_test_notification_with_telegram(mock_send, auth_client, user):
    NotificationSettings.objects.create(user=user, telegram_chat_id='123')
    mock_send.return_value = True

    r = auth_client.post(reverse('notification-test'))
    assert r.status_code == 200
    assert 'отправлено' in r.data['detail'].lower()


def test_test_notification_without_telegram(auth_client, user):
    NotificationSettings.objects.create(user=user)
    r = auth_client.post(reverse('notification-test'))
    assert r.status_code == 400


def test_notification_history(auth_client, user):
    NotificationLog.objects.create(user=user, kind='test', status='sent', message='hi')
    NotificationLog.objects.create(user=user, kind='new_trade', status='sent', message='trade')
    r = auth_client.get(reverse('notification-history'))
    assert r.status_code == 200
    assert len(r.data) == 2


def test_requires_auth(api_client):
    r = api_client.get(reverse('notification-settings'))
    assert r.status_code == 401