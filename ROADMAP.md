# 🗺️ ROADMAP — Trading Assistant

## ✅ Этап 1-2: Фундамент + JWT (завершён)

- Django 5.2 + DRF + SimpleJWT
- PostgreSQL 18
- Кастомная модель `User` (email, telegram_chat_id, timezone)
- Эндпоинты: register, login, refresh, me, logout
- Swagger UI + Django Admin
- **9 тестов** (регистрация, логин, JWT, blacklist)

## ✅ Этап 3: Журнал сделок (завершён)

- Модель `Trade` (20+ полей)
- CRUD через ViewSet: list, create, retrieve, update, destroy
- Фильтры: symbol, side, status, strategy, source, date-range
- Поиск: по symbol, notes, strategy
- Сортировка: по opened_at, pnl, symbol
- Автоматический расчёт PnL (long + short)
- Эндпоинт `/api/trades/stats/` (Win Rate, total PnL, avg win/loss)
- Django Admin с фильтрами и date-hierarchy
- **13 тестов** (валидация, изоляция, PnL, фильтры, поиск)

## ✅ Этап 4: Импорт из MetaTrader 5 (завершён)

- API-токен `MT5_API_TOKEN` (X-API-Key, отдельно от JWT)
- Эндпоинт `POST /api/trades/import/mt5/`
- Идемпотентность через `external_id + source='mt5'`
- Модель `Trade.save()` не пересчитывает PnL из MT5
- Локальный коллектор `tools/mt5_collector/collector.py`
  - Подключается к MT5
  - Читает `history_deals_get`
  - Группирует по `position_id`
  - Отправляет в Django с retry-логикой
- Валидация: отрицательные цены, quantity > 0
- **6 тестов** (авторизация, идемпотентность, валидация)
- **Работает вживую** на FundedNext-аккаунте

## ✅ Этап 5: Рыночные данные (завершён)

- Модель `PriceSnapshot` — кэш цен
- Модель `Candle` — свечи OHLC
- Сервис **CoinGecko** — крипта (BTC, ETH, SOL, BNB, XRP, DOGE), без API-ключа
- Сервис **MT5** — форекс (XAUUSD, EURUSD, GBPUSD, USDJPY), если доступен локально
- Эндпоинты:
  - `GET /api/market/watchlist/` — избранные символы с ценами
  - `GET /api/market/{symbol}/` — текущая цена
  - `GET /api/market/{symbol}/candles/?days=7` — свечи OHLC
  - `POST /api/market/refresh/` — ручное обновление
- **Фоновый scheduler** через `threading.Timer` (обновление каждые 60 сек, без Redis/Celery)
- **9 тестов** (моки CoinGecko, кэш, свечи, fallback)

## 🔮 Этап 6: AI-агент (анализ скриншотов)

- Модель `Analysis` (screenshot, prompt_version, result, cost_usd)
- Интеграция с OpenAI GPT-4o Vision
- Эндпоинт `POST /api/ai/analyze/` (upload скриншота)
- Celery-задача для асинхронного анализа
- Промпт: тренд, уровни, рекомендация, confidence
- Дисклеймер «не финансовая рекомендация»
- **7 тестов** (мок OpenAI, лимиты, стоимость)

## ✅ Этап 7: Уведомления (завершён)

- Модель `NotificationSettings` (per-user настройки)
- Модель `NotificationLog` (история отправок)
- Telegram-сервис: `send_message`, `send_to_user`
- Готовые шаблоны: `notify_new_trade`, `notify_tp_sl`, `notify_daily_digest`
- Эндпоинты: link, unlink, test, settings, history
- **Интеграция с MT5-импортом** — уведомления о новых сделках
- **8 тестов** (моки Telegram API)
- **Работает вживую** — проверено на реальной сделке XAUUSD

## 🔮 Этап 8: Flutter + Firebase + деплой

**Frontend (Flutter):**
- Экраны: Login, Register, Dashboard, Trades List, Trade Detail, Add Trade, Analyze, Settings
- Библиотеки: `http`, `fl_chart`, `shared_preferences`, `firebase_messaging`, `firebase_auth`, `go_router`, `sqflite`
- Offline-режим: локальный кэш + sync
- Deep links: `myapp://trade/123`

**Firebase:**
- Auth, FCM, Hosting

**Деплой:**
- Backend → Render (Django + PostgreSQL)
- Frontend → Firebase Hosting
- Mobile → Google Play

**Тесты Flutter:** 10 штук

## 🎯 Итоговые метрики

| Этап | Тестов | Статус |
|---|---|---|
| 1-2. Auth | 9 | ✅ |
| 3. Trades | 13 | ✅ |
| 4. MT5 import | 6 | ✅ |
| 5. Market data | 9 | ✅ |
| 6. AI agent | 7 | ⏳ |
| 7. Notifications | 8 | ✅ |
| 8. Flutter | 10 | ⏳ |
| **Итого** | **53** | **45/53** |

## 💼 Что даёт проект

- **Backend**: Django + DRF + PostgreSQL + JWT + MT5-интеграция
- **Frontend**: Flutter + Firebase
- **DevOps**: CI/CD + деплой + Firebase Hosting
- **AI**: OpenAI Vision + промпт-инжиниринг
- **Практическая польза**: реальный трейдинг-журнал, работает вживую


