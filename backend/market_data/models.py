from django.db import models


class PriceSnapshot(models.Model):
    """Кэш последней известной цены символа."""

    SOURCE_CHOICES = [
        ('coingecko', 'CoinGecko'),
        ('binance', 'Binance'),
        ('mt5', 'MetaTrader 5'),
        ('manual', 'Вручную'),
    ]

    symbol = models.CharField(max_length=20, unique=True, db_index=True, verbose_name='Символ')
    price = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='Цена')
    change_24h = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name='Изм. 24ч (%)')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='coingecko', verbose_name='Источник')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    is_active = models.BooleanField(default=True, verbose_name='В избранном')

    class Meta:
        db_table = 'market_price_snapshot'
        ordering = ['symbol']
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'

    def __str__(self):
        return f"{self.symbol}: {self.price} ({self.source})"


class Candle(models.Model):
    """Свеча OHLC для графиков."""

    symbol = models.CharField(max_length=20, db_index=True, verbose_name='Символ')
    timeframe = models.CharField(max_length=5, default='1h', verbose_name='Таймфрейм')
    timestamp = models.DateTimeField(verbose_name='Время')
    open = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='Open')
    high = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='High')
    low = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='Low')
    close = models.DecimalField(max_digits=20, decimal_places=8, verbose_name='Close')
    volume = models.DecimalField(max_digits=30, decimal_places=8, default=0, verbose_name='Объём')

    class Meta:
        db_table = 'market_candle'
        ordering = ['-timestamp']
        unique_together = [('symbol', 'timeframe', 'timestamp')]
        indexes = [models.Index(fields=['symbol', 'timeframe', '-timestamp'])]
        verbose_name = 'Свеча'
        verbose_name_plural = 'Свечи'

    def __str__(self):
        return f"{self.symbol} {self.timeframe} @ {self.timestamp}"