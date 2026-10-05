from django.db import models
from django.conf import settings


class NotificationSettings(models.Model):
    """Настройки уведомлений для пользователя."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name='Пользователь',
    )

    # Telegram
    telegram_chat_id = models.CharField(
        max_length=50, blank=True, db_index=True,
        verbose_name='Telegram chat_id',
    )
    telegram_linked_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Привязан к Telegram',
    )

    # Типы уведомлений
    notify_new_trade = models.BooleanField(
        default=True, verbose_name='Новая сделка',
    )
    notify_tp_sl = models.BooleanField(
        default=True, verbose_name='Достижение TP/SL',
    )
    notify_daily_digest = models.BooleanField(
        default=True, verbose_name='Утренний дайджест',
    )

    # Дневной дайджест
    digest_hour = models.IntegerField(
        default=9, verbose_name='Час дайджеста (UTC)',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications_settings'
        verbose_name = 'Настройки уведомлений'
        verbose_name_plural = 'Настройки уведомлений'

    def __str__(self):
        return f"Настройки {self.user.email}"


class NotificationLog(models.Model):
    """История отправленных уведомлений."""

    KIND_CHOICES = [
        ('new_trade', 'Новая сделка'),
        ('tp_sl', 'TP/SL'),
        ('daily_digest', 'Дайджест'),
        ('test', 'Тестовое'),
    ]
    STATUS_CHOICES = [
        ('sent', 'Отправлено'),
        ('failed', 'Ошибка'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_logs',
        verbose_name='Пользователь',
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, verbose_name='Тип')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Статус')
    message = models.TextField(blank=True, verbose_name='Сообщение')
    error = models.TextField(blank=True, verbose_name='Ошибка')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'notifications_log'
        ordering = ['-created_at']
        verbose_name = 'Лог уведомления'
        verbose_name_plural = 'Логи уведомлений'

    def __str__(self):
        return f"[{self.status}] {self.kind} → {self.user.email}"