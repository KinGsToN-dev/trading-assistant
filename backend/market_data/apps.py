from django.apps import AppConfig
import os


class MarketDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'market_data'

    def ready(self):
        # Не запускаем scheduler во время миграций или тестов
        if os.environ.get('RUN_MAIN') != 'true' and os.environ.get('PYTEST_CURRENT_TEST') is None:
            # Только в runserver (RUN_MAIN=true) — не в migrate, не в shell
            if 'runserver' in os.environ.get('_', '') or os.environ.get('RUN_MAIN') == 'true':
                from .scheduler import start_scheduler
                start_scheduler()