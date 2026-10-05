import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_register_success(api_client):
    url = reverse('register')
    data = {'email': 'new@example.com', 'username': 'newuser', 'password': 'secret123', 'password2': 'secret123'}
    r = api_client.post(url, data)
    assert r.status_code == 201
    assert 'access' in r.data
    assert 'refresh' in r.data
    assert User.objects.filter(email='new@example.com').exists()


def test_register_password_mismatch(api_client):
    url = reverse('register')
    data = {'email': 'x@example.com', 'username': 'xuser', 'password': 'secret123', 'password2': 'different'}
    r = api_client.post(url, data)
    assert r.status_code == 400


def test_register_short_password(api_client):
    url = reverse('register')
    data = {'email': 'x@example.com', 'username': 'xuser', 'password': '123', 'password2': '123'}
    r = api_client.post(url, data)
    assert r.status_code == 400


def test_register_duplicate_email(api_client, user):
    url = reverse('register')
    data = {'email': user.email, 'username': 'another', 'password': 'secret123', 'password2': 'secret123'}
    r = api_client.post(url, data)
    assert r.status_code == 400


def test_login_success(api_client, user):
    url = reverse('login')
    r = api_client.post(url, {'email': user.email, 'password': 'secret123'})
    assert r.status_code == 200
    assert 'access' in r.data


def test_login_wrong_password(api_client, user):
    url = reverse('login')
    r = api_client.post(url, {'email': user.email, 'password': 'wrong'})
    assert r.status_code == 401


def test_me_requires_auth(api_client):
    url = reverse('me')
    r = api_client.get(url)
    assert r.status_code == 401


def test_me_with_auth(auth_client, user):
    url = reverse('me')
    r = auth_client.get(url)
    assert r.status_code == 200
    assert r.data['email'] == user.email


def test_logout_blacklists_refresh(api_client, user):
    r = api_client.post(reverse('login'), {'email': user.email, 'password': 'secret123'})
    refresh = r.data['refresh']
    access = r.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    r2 = api_client.post(reverse('logout'), {'refresh': refresh})
    assert r2.status_code == 200