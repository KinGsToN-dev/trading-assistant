"""
Простой фоновый обновлятор цен через threading.Timer.
Не требует Redis/Celery. Запускается при старте Django.
"""
import logging
import threading

logger = logging.getLogger(__name__)

_started = False
_timer = None
INTERVAL_SECONDS = 60  # обновление раз в минуту


def _tick():
    """Обновляет цены и перезапускает таймер."""
    global _timer
    try:
        from .views import refresh_prices
        count = refresh_prices()
        logger.info(f'[scheduler] Обновлено цен: {count}')
    except Exception as e:
        logger.error(f'[scheduler] Ошибка: {e}')

    _timer = threading.Timer(INTERVAL_SECONDS, _tick)
    _timer.daemon = True
    _timer.start()


def start_scheduler():
    """Запускается один раз при инициализации приложения."""
    global _started, _timer
    if _started:
        return
    _started = True

    # Первый тик через 10 секунд, чтобы не мешать migrate
    _timer = threading.Timer(10, _tick)
    _timer.daemon = True
    _timer.start()
    logger.info('[scheduler] Фоновое обновление цен запущено (каждые %d сек)', INTERVAL_SECONDS)