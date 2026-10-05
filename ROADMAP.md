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

## 🚧 Этап 5: Рыночные данные (следующий)

**Backend:**
- Модель `PriceSnapshot` для кэша цен
- Интеграция с CoinGecko (крипта) — без API-ключа
- Интеграция с MT5 (форекс) — через локальный мост
- Эндпоинты:
  - `GET /api/market/{symbol}/` — текущая цена
  - `GET /api/market/{symbol}/candles/?tf=1h&limit=100` — свечи OHLC
  - `WS /ws/market/{symbol}/` — WebSocket-стрим
- Периодическое обновление через `threading` или Celery (без Redis)
- **8 тестов** (моки API, кэш, fallback)

## 🔮 Этап 6: AI-агент (анализ скриншотов)

- Модель `Analysis` (screenshot, prompt_version, result, cost_usd)
- Интеграция с OpenAI GPT-4o Vision
- Эндпоинт `POST /api/ai/analyze/` (upload скриншота)
- Celery-задача для асинхронного анализа
- Промпт: тренд, уровни, рекомендация, confidence
- Дисклеймер «не финансовая рекомендация»
- **7 тестов** (мок OpenAI, лимиты, стоимость)

## 🔮 Этап 7: Уведомления

- **Telegram-бот**: `/start`, `/link`, `/stats`, `/last`
- **Email**: через SendGrid/Mailgun
- **Push (FCM)**: Firebase Cloud Messaging
- Модель `DeviceToken`
- Сценарии: новая сделка, цель достигнута, AI-анализ готов
- **6 тестов** (Telegram, email, FCM, retry)

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
| 5. Market data | 8 | ⏳ |
| 6. AI agent | 7 | ⏳ |
| 7. Notifications | 6 | ⏳ |
| 8. Flutter | 10 | ⏳ |
| **Итого** | **59** | **28/59** |

## 💼 Что даёт проект

- **Backend**: Django + DRF + PostgreSQL + JWT + MT5-интеграция
- **Frontend**: Flutter + Firebase
- **DevOps**: CI/CD + деплой + Firebase Hosting
- **AI**: OpenAI Vision + промпт-инжиниринг
- **Практическая польза**: реальный трейдинг-журнал, работает вживую
