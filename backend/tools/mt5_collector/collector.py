import sys, time, json, argparse
from datetime import datetime, timezone, timedelta
import requests
try:
    import MetaTrader5 as mt5
except ImportError:
    print("❌ Установите MetaTrader5: pip install MetaTrader5")
    sys.exit(1)
from config import API_URL, API_TOKEN, DAYS_BACK, MT5_LOGIN, MT5_PASSWORD, MT5_SERVER


def connect_mt5():
    kwargs = {}
    if MT5_LOGIN:
        kwargs['login'] = int(MT5_LOGIN)
        kwargs['password'] = MT5_PASSWORD
        kwargs['server'] = MT5_SERVER
    if not mt5.initialize(**kwargs):
        print(f"❌ mt5.initialize() failed: {mt5.last_error()}")
        sys.exit(1)
    info = mt5.account_info()
    print(f"✅ Подключено к MT5. Аккаунт: {info.login} @ {info.server}, баланс: {info.balance} {info.currency}")


def fetch_closed_trades(days_back=7):
    date_from = datetime.now(timezone.utc) - timedelta(days=days_back)
    date_to = datetime.now(timezone.utc) + timedelta(days=1)
    deals = mt5.history_deals_get(date_from, date_to)
    if deals is None:
        print(f"❌ history_deals_get failed: {mt5.last_error()}")
        return []
    positions = {}
    for d in deals:
        if d.position_id == 0:
            continue
        positions.setdefault(d.position_id, []).append(d)
    trades = []
    for pid, deals_list in positions.items():
        deals_list.sort(key=lambda x: x.time)
        entry_deal = deals_list[0]
        exit_deals = [d for d in deals_list if d.entry == 1]
        if not exit_deals:
            continue
        exit_deal = exit_deals[-1]
        trades.append({
            'external_id': f"mt5-{pid}",
            'symbol': entry_deal.symbol,
            'side': 'buy' if entry_deal.type == 0 else 'sell',
            'status': 'closed',
            'entry_price': str(entry_deal.price),
            'exit_price': str(exit_deal.price),
            'quantity': str(entry_deal.volume),
            'pnl': str(sum(d.profit for d in deals_list)),
            'commission': str(sum(d.commission for d in deals_list)),
            'opened_at': datetime.fromtimestamp(entry_deal.time, tz=timezone.utc).isoformat(),
            'closed_at': datetime.fromtimestamp(exit_deal.time, tz=timezone.utc).isoformat(),
            'strategy': '',
            'notes': f"MT5 deal #{pid}",
        })
    return trades


def send_to_api(trades):
    if not trades:
        print("ℹ️  Нет новых сделок")
        return
    url = f"{API_URL.rstrip('/')}/api/trades/import/mt5/"
    headers = {'Content-Type': 'application/json', 'X-API-Key': API_TOKEN}
    try:
        r = requests.post(url, headers=headers, json={'trades': trades}, timeout=30)
        r.raise_for_status()
        result = r.json()
        print(f"✅ Отправлено {len(trades)} сделок")
        print(f"   created: {result.get('created')}, updated: {result.get('updated')}, errors: {len(result.get('errors', []))}")
        if result.get('errors'):
            print(f"   Ошибки: {json.dumps(result['errors'], indent=2, ensure_ascii=False)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка отправки: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Ответ: {e.response.text}")


def run_once():
    connect_mt5()
    trades = fetch_closed_trades(days_back=DAYS_BACK)
    print(f"📊 Найдено сделок: {len(trades)}")
    send_to_api(trades)
    mt5.shutdown()


def run_loop(interval_minutes=5):
    print(f"🔄 Запуск в цикле (каждые {interval_minutes} мин). Ctrl+C для остановки.")
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        print(f"⏳ Жду {interval_minutes} мин...")
        time.sleep(interval_minutes * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MT5 → Django collector')
    parser.add_argument('--loop', action='store_true')
    parser.add_argument('--interval', type=int, default=5)
    args = parser.parse_args()
    if args.loop:
        run_loop(args.interval)
    else:
        run_once()