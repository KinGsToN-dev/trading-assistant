from django.contrib import admin
from .models import Trade


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'side', 'status', 'entry_price', 'exit_price', 'pnl', 'user', 'opened_at')
    list_filter = ('status', 'side', 'source', 'strategy', 'emotion')
    search_fields = ('symbol', 'notes', 'strategy', 'external_id')
    readonly_fields = ('pnl', 'created_at', 'updated_at')
    date_hierarchy = 'opened_at'
    ordering = ('-opened_at',)

    fieldsets = (
        ('Основное', {
            'fields': ('user', 'symbol', 'side', 'status', 'source', 'external_id')
        }),
        ('Цены и объём', {
            'fields': ('entry_price', 'exit_price', 'quantity', 'stop_loss', 'take_profit')
        }),
        ('Результат', {
            'fields': ('pnl', 'commission')
        }),
        ('Время', {
            'fields': ('opened_at', 'closed_at', 'created_at', 'updated_at')
        }),
        ('Метаданные', {
            'fields': ('strategy', 'tags', 'notes', 'screenshot')
        }),
        ('Психология', {
            'fields': ('emotion', 'followed_plan')
        }),
    )