from rest_framework import serializers
from .models import PriceSnapshot, Candle


class PriceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceSnapshot
        fields = ['symbol', 'price', 'change_24h', 'source', 'updated_at', 'is_active']


class CandleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candle
        fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']