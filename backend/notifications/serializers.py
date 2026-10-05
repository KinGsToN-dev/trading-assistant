from rest_framework import serializers
from .models import NotificationSettings, NotificationLog


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = [
            'telegram_chat_id', 'telegram_linked_at',
            'notify_new_trade', 'notify_tp_sl', 'notify_daily_digest',
            'digest_hour', 'updated_at',
        ]
        read_only_fields = ['telegram_linked_at', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = ['id', 'kind', 'status', 'message', 'error', 'created_at']