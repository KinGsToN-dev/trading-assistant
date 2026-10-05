from rest_framework import serializers
from decimal import Decimal
from .models import Trade


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = [
            'id', 'symbol', 'side', 'status',
            'entry_price', 'exit_price', 'quantity',
            'stop_loss', 'take_profit',
            'pnl', 'commission',
            'opened_at', 'closed_at',
            'strategy', 'tags', 'notes',
            'emotion', 'followed_plan',
            'screenshot', 'source', 'external_id',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'pnl', 'created_at', 'updated_at']


class TradeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = [
            'symbol', 'side', 'status',
            'entry_price', 'exit_price', 'quantity',
            'stop_loss', 'take_profit', 'commission',
            'opened_at', 'closed_at',
            'strategy', 'tags', 'notes',
            'emotion', 'followed_plan',
            'screenshot', 'source', 'external_id',
        ]

    def validate(self, data):
        # entry_price > 0
        if data.get('entry_price') is not None and data['entry_price'] <= 0:
            raise serializers.ValidationError({'entry_price': 'Цена входа должна быть больше 0'})
        # quantity > 0
        if data.get('quantity') is not None and data['quantity'] <= 0:
            raise serializers.ValidationError({'quantity': 'Объём должен быть больше 0'})
        # если статус closed — нужен exit_price
        if data.get('status') == 'closed' and data.get('exit_price') is None:
            raise serializers.ValidationError({'exit_price': 'Для закрытой сделки нужна цена выхода'})
        return data


class TradeStatsSerializer(serializers.Serializer):
    total_trades = serializers.IntegerField()
    open_trades = serializers.IntegerField()
    closed_trades = serializers.IntegerField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    win_rate = serializers.FloatField()
    total_pnl = serializers.DecimalField(max_digits=20, decimal_places=8)
    avg_pnl = serializers.DecimalField(max_digits=20, decimal_places=8)
    avg_win = serializers.DecimalField(max_digits=20, decimal_places=8)
    avg_loss = serializers.DecimalField(max_digits=20, decimal_places=8)
    best_trade = serializers.DecimalField(max_digits=20, decimal_places=8, allow_null=True)
    worst_trade = serializers.DecimalField(max_digits=20, decimal_places=8, allow_null=True)

class MT5TradeImportSerializer(serializers.Serializer):
    external_id = serializers.CharField(max_length=100)
    symbol = serializers.CharField(max_length=20)
    side = serializers.ChoiceField(choices=['buy', 'sell'])
    status = serializers.ChoiceField(choices=['open', 'closed'], default='closed')
    entry_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    exit_price = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=20, decimal_places=8)
    pnl = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    commission = serializers.DecimalField(max_digits=20, decimal_places=8, default=0)
    opened_at = serializers.DateTimeField()
    closed_at = serializers.DateTimeField(required=False, allow_null=True)
    strategy = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    stop_loss = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)
    take_profit = serializers.DecimalField(max_digits=20, decimal_places=8, required=False, allow_null=True)

    def validate_entry_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Цена входа должна быть больше 0')
        return value

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Объём должен быть больше 0')
        return value

    def validate(self, data):
        if data.get('status') == 'closed' and data.get('exit_price') is None:
            raise serializers.ValidationError({'exit_price': 'Для закрытой сделки нужна цена выхода'})
        return data
