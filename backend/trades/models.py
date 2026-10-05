from django.db import models
from django.conf import settings
from decimal import Decimal


class Trade(models.Model):
    SIDE_CHOICES = [
        ('buy', 'Buy (Long)'),
        ('sell', 'Sell (Short)'),
    ]
    SOURCE_CHOICES = [
        ('manual', 'Р’СЂСѓС‡РЅСѓСЋ'),
        ('mt5', 'MetaTrader 5'),
        ('api', 'API'),
        ('import', 'РРјРїРѕСЂС‚'),
    ]
    EMOTION_CHOICES = [
        ('calm', 'РЎРїРѕРєРѕР№СЃС‚РІРёРµ'),
        ('fomo', 'FOMO'),
        ('fear', 'РЎС‚СЂР°С…'),
        ('greed', 'Р–Р°РґРЅРѕСЃС‚СЊ'),
        ('revenge', 'РўРёР»СЊС‚ / Р РµРІР°РЅС€'),
        ('confidence', 'РЈРІРµСЂРµРЅРЅРѕСЃС‚СЊ'),
    ]
    STATUS_CHOICES = [
        ('open', 'РћС‚РєСЂС‹С‚Р°'),
        ('closed', 'Р—Р°РєСЂС‹С‚Р°'),
        ('cancelled', 'РћС‚РјРµРЅРµРЅР°'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trades',
        verbose_name='РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ',
    )

    # РћСЃРЅРѕРІРЅС‹Рµ РґР°РЅРЅС‹Рµ
    symbol = models.CharField(max_length=20, db_index=True, verbose_name='РЎРёРјРІРѕР»')
    side = models.CharField(max_length=10, choices=SIDE_CHOICES, verbose_name='РЎС‚РѕСЂРѕРЅР°')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open', verbose_name='РЎС‚Р°С‚СѓСЃ')

    # Р¦РµРЅС‹ Рё РѕР±СЉС‘Рј
    entry_price = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='Р¦РµРЅР° РІС…РѕРґР°')
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, verbose_name='Р¦РµРЅР° РІС‹С…РѕРґР°')
    quantity = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='РћР±СЉС‘Рј')
    stop_loss = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, verbose_name='Stop Loss')
    take_profit = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, verbose_name='Take Profit')

    # Р РµР·СѓР»СЊС‚Р°С‚
    pnl = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, verbose_name='PnL')
    commission = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'), verbose_name='РљРѕРјРёСЃСЃРёСЏ')

    # Р’СЂРµРјСЏ
    opened_at = models.DateTimeField(verbose_name='РћС‚РєСЂС‹С‚Р°')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Р—Р°РєСЂС‹С‚Р°')

    # РњРµС‚Р°РґР°РЅРЅС‹Рµ
    strategy = models.CharField(max_length=100, blank=True, db_index=True, verbose_name='РЎС‚СЂР°С‚РµРіРёСЏ')
    tags = models.JSONField(default=list, blank=True, verbose_name='РўРµРіРё')
    notes = models.TextField(blank=True, verbose_name='Р—Р°РјРµС‚РєРё')

    # РџСЃРёС…РѕР»РѕРіРёСЏ
    emotion = models.CharField(max_length=20, choices=EMOTION_CHOICES, blank=True, verbose_name='Р­РјРѕС†РёСЏ')
    followed_plan = models.BooleanField(default=True, verbose_name='РЎР»РµРґРѕРІР°Р» РїР»Р°РЅСѓ')

    # РЎРєСЂРёРЅС€РѕС‚
    screenshot = models.ImageField(upload_to='trades/%Y/%m/', null=True, blank=True, verbose_name='РЎРєСЂРёРЅС€РѕС‚')

    # РСЃС‚РѕС‡РЅРёРє
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual', verbose_name='РСЃС‚РѕС‡РЅРёРє')
    external_id = models.CharField(max_length=100, blank=True, db_index=True, verbose_name='Р’РЅРµС€РЅРёР№ ID')

    # РЎР»СѓР¶РµР±РЅРѕРµ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trades_trade'
        ordering = ['-opened_at']
        verbose_name = 'РЎРґРµР»РєР°'
        verbose_name_plural = 'РЎРґРµР»РєРё'
        indexes = [
            models.Index(fields=['user', '-opened_at']),
            models.Index(fields=['user', 'symbol']),
            models.Index(fields=['user', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'source', 'external_id'],
                name='unique_external_trade_per_user',
                condition=models.Q(external_id__gt=''),
            )
        ]

    def __str__(self):
        return f"{self.symbol} {self.side} @ {self.entry_price}"

    def calculate_pnl(self):
        if self.exit_price is None or self.status != 'closed':
            return None
        diff = self.exit_price - self.entry_price
        if self.side == 'sell':
            diff = -diff
        gross = diff * self.quantity
        return gross - self.commission

    def save(self, *args, **kwargs):
        # Автоматический расчёт PnL при закрытии — только если PnL не задан явно
        if (
            self.status == 'closed'
            and self.exit_price is not None
            and self.pnl is None
        ):
            self.pnl = self.calculate_pnl()
        super().save(*args, **kwargs)