from rest_framework.permissions import BasePermission
from django.conf import settings


class HasMT5ApiKey(BasePermission):
    def has_permission(self, request, view):
        key = request.headers.get('X-API-Key', '')
        expected = getattr(settings, 'MT5_API_TOKEN', None)
        return bool(key) and bool(expected) and key == expected