from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum, Count, Avg, Max, Min
from django_filters.rest_framework import DjangoFilterBackend
from .models import Trade
from .serializers import TradeSerializer, TradeCreateSerializer, TradeStatsSerializer, MT5TradeImportSerializer
from .permissions import HasMT5ApiKey
from notifications.services.telegram import notify_new_trade


class TradeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['symbol', 'side', 'status', 'strategy', 'source']
    search_fields = ['symbol', 'notes', 'strategy']
    ordering_fields = ['opened_at', 'closed_at', 'pnl', 'symbol', 'created_at']
    ordering = ['-opened_at']

    def get_queryset(self):
        qs = Trade.objects.filter(user=self.request.user)

        # Р В¤Р С‘Р В»РЎРЉРЎвЂљРЎР‚ Р С—Р С• Р Т‘Р С‘Р В°Р С—Р В°Р В·Р С•Р Р…РЎС“ Р Т‘Р В°РЎвЂљ
        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')
        if date_from:
            qs = qs.filter(opened_at__gte=date_from)
        if date_to:
            qs = qs.filter(opened_at__lte=date_to)

        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return TradeCreateSerializer
        return TradeSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Р РЋРЎвЂљР В°РЎвЂљР С‘РЎРѓРЎвЂљР С‘Р С”Р В° Р С—Р С• РЎРѓР Т‘Р ВµР В»Р С”Р В°Р С Р С—Р С•Р В»РЎРЉР В·Р С•Р Р†Р В°РЎвЂљР ВµР В»РЎРЏ."""
        qs = self.get_queryset()
        closed = qs.filter(status='closed', pnl__isnull=False)

        total = qs.count()
        open_count = qs.filter(status='open').count()
        closed_count = closed.count()

        wins = closed.filter(pnl__gt=0).count()
        losses = closed.filter(pnl__lt=0).count()

        pnl_agg = closed.aggregate(
            total=Sum('pnl'),
            avg=Avg('pnl'),
            best=Max('pnl'),
            worst=Min('pnl'),
        )
        avg_win = closed.filter(pnl__gt=0).aggregate(a=Avg('pnl'))['a'] or 0
        avg_loss = closed.filter(pnl__lt=0).aggregate(a=Avg('pnl'))['a'] or 0

        win_rate = (wins / closed_count * 100) if closed_count > 0 else 0

        data = {
            'total_trades': total,
            'open_trades': open_count,
            'closed_trades': closed_count,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate, 2),
            'total_pnl': pnl_agg['total'] or 0,
            'avg_pnl': pnl_agg['avg'] or 0,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_trade': pnl_agg['best'],
            'worst_trade': pnl_agg['worst'],
        }
        return Response(TradeStatsSerializer(data).data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[HasMT5ApiKey],
        authentication_classes=[],
        url_path='import/mt5',
    )
    def import_mt5(self, request):
        trades_data = request.data.get('trades', [])
        if not isinstance(trades_data, list):
            return Response({'detail': 'РџРѕР»Рµ "trades" РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ РјР°СЃСЃРёРІРѕРј'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        owner = User.objects.filter(is_superuser=True).order_by('id').first()
        if not owner:
            return Response({'detail': 'РќРµС‚ СЃСѓРїРµСЂСЋР·РµСЂР°'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        created = 0
        updated = 0
        errors = []

        for idx, raw in enumerate(trades_data):
            s = MT5TradeImportSerializer(data=raw)
            if not s.is_valid():
                errors.append({'index': idx, 'external_id': raw.get('external_id'), 'errors': s.errors})
                continue

            d = s.validated_data
            external_id = d['external_id']

            existing = Trade.objects.filter(user=owner, source='mt5', external_id=external_id).first()

            defaults = {
                'symbol': d['symbol'], 'side': d['side'], 'status': d.get('status', 'closed'),
                'entry_price': d['entry_price'], 'exit_price': d.get('exit_price'),
                'quantity': d['quantity'], 'pnl': d.get('pnl'),
                'commission': d.get('commission', 0),
                'opened_at': d['opened_at'], 'closed_at': d.get('closed_at'),
                'strategy': d.get('strategy', ''), 'notes': d.get('notes', ''),
                'stop_loss': d.get('stop_loss'), 'take_profit': d.get('take_profit'),
            }

            if existing:
                for k, v in defaults.items():
                    setattr(existing, k, v)
                existing.save()
                updated += 1
            else:
                trade = Trade.objects.create(
                user=owner, source='mt5', external_id=external_id, **defaults
                )
                created += 1
            # Уведомление в Telegram
                # Уведомление в Telegram
                try:
                    if owner.notification_settings.notify_new_trade:
                        notify_new_trade(owner, trade)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).exception(
                        f'Failed to send notification for trade {trade.id}: {e}'
                    )

        return Response({
            'created': created, 'updated': updated, 'skipped': 0,
            'errors': errors, 'total': len(trades_data),
        }, status=status.HTTP_200_OK)