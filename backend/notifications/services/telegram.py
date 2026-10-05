"""
Сервис отправки сообщений через Telegram Bot API.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = 'https://api.telegram.org/bot{token}/sendMessage'


def send_message(chat_id: str, text: str, parse_mode: str = 'HTML') -> dict:
    """
    Отправляет сообщение в Telegram.
    Возвращает {'ok': bool, 'error': str|None}.
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    if not token:
        logger.error('TELEGRAM_BOT_TOKEN не задан')
        return {'ok': False, 'error': 'no_token'}

    if not chat_id:
        return {'ok': False, 'error': 'no_chat_id'}

    url = TELEGRAM_API.format(token=token)
    try:
        r = requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True,
        }, timeout=10)
        data = r.json()
        if not data.get('ok'):
            logger.warning(f'Telegram error: {data}')
            return {'ok': False, 'error': data.get('description', 'unknown')}
        return {'ok': True, 'error': None}
    except requests.RequestException as e:
        logger.error(f'Telegram request failed: {e}')
        return {'ok': False, 'error': str(e)}


def send_to_user(user, text: str, kind: str = 'test') -> bool:
    """
    Отправляет сообщение пользователю, если у него привязан Telegram.
    Логирует результат в NotificationLog.
    """
    from ..models import NotificationLog

    try:
        chat_id = user.notification_settings.telegram_chat_id
    except Exception:
        chat_id = getattr(user, 'telegram_chat_id', '')

    if not chat_id:
        logger.info(f'User {user.email} has no Telegram chat_id')
        return False

    result = send_message(chat_id, text)
    NotificationLog.objects.create(
        user=user,
        kind=kind,
        status='sent' if result['ok'] else 'failed',
        message=text[:1000],
        error=result.get('error') or '',
    )
    return result['ok']


# ---------- Готовые шаблоны сообщений ----------

def notify_new_trade(user, trade) -> bool:
    """Уведомление о новой сделке (после импорта из MT5)."""
    side_emoji = '🟢' if trade.side == 'buy' else '🔴'
    
    if trade.status == 'open':
        # Открытая позиция
        text = (
            f"📈 <b>Открыта новая позиция</b>\n\n"
            f"📊 {trade.symbol} • {trade.side.upper()}\n"
            f"💵 Вход: <b>{trade.entry_price}</b>\n"
            f"📦 Объём: {trade.quantity}"
        )
    else:
        # Закрытая сделка
        pnl_line = ''
        if trade.pnl is not None:
            pnl_emoji = '💰' if trade.pnl >= 0 else '📉'
            pnl_line = f"\n{pnl_emoji} PnL: <b>{trade.pnl:+.2f}</b>"

        text = (
            f"{side_emoji} <b>Сделка закрыта</b>\n\n"
            f"📊 {trade.symbol} • {trade.side.upper()}\n"
            f"💵 Вход: {trade.entry_price}"
        )
        if trade.exit_price:
            text += f"\n💵 Выход: {trade.exit_price}"
        text += pnl_line

    return send_to_user(user, text, kind='new_trade')


def notify_tp_sl(user, symbol: str, price: str, level_type: str, level: str) -> bool:
    """Уведомление о достижении Take Profit / Stop Loss."""
    if level_type == 'tp':
        emoji = '🎯'
        label = 'Take Profit'
    else:
        emoji = '🛑'
        label = 'Stop Loss'

    text = (
        f"{emoji} <b>{label} достигнут</b>\n\n"
        f"📊 {symbol}\n"
        f"💰 Текущая цена: <b>{price}</b>\n"
        f"🎯 Уровень: {level}"
    )
    return send_to_user(user, text, kind='tp_sl')


def notify_daily_digest(user, stats: dict) -> bool:
    """Утренний дайджест со статистикой."""
    win_rate = stats.get('win_rate', 0)
    total_pnl = stats.get('total_pnl', 0)

    pnl_emoji = '💰' if total_pnl >= 0 else '📉'

    text = (
        f"☀️ <b>Доброе утро!</b>\n\n"
        f"📊 Статистика за последние 24 часа:\n\n"
        f"📈 Всего сделок: <b>{stats.get('total_trades', 0)}</b>\n"
        f"✅ Прибыльных: <b>{stats.get('wins', 0)}</b>\n"
        f"❌ Убыточных: <b>{stats.get('losses', 0)}</b>\n"
        f"🎯 Win Rate: <b>{win_rate}%</b>\n"
        f"{pnl_emoji} PnL: <b>{total_pnl:+.2f}</b>\n\n"
        f"Хорошего дня и профитных сделок! 🚀"
    )
    return send_to_user(user, text, kind='daily_digest')