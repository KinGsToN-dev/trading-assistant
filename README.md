# 📈 Trading Assistant — Full-Stack

![Backend Tests](https://github.com/KinGsToN-dev/trading-assistant/actions/workflows/tests.yml/badge.svg)

AI-ассистент трейдера: журнал сделок, импорт из MetaTrader 5, котировки в реальном времени, AI-анализ графиков и уведомления.

## ✨ Что уже реализовано

- 🔐 **JWT-аутентификация** — регистрация, логин, refresh, logout с blacklist
- 👤 **Кастомная модель User** — email вместо username, поля для Telegram и timezone
- 📝 **Журнал сделок (Trade)** — 20+ полей: symbol, side, entry/exit, quantity, pnl, strategy, tags, notes, emotion, screenshot, source, external_id
- 💰 **Автоматический расчёт PnL** — long/short позиции, учёт комиссии
- 🔍 **Фильтры и поиск** — по символу, статусу, стратегии, датам, заметкам
- 📊 **Статистика** — Win Rate, total PnL, avg win/loss, best/worst trade
- 🤖 **Импорт из MetaTrader 5** — через API-токен (`X-API-Key`), идемпотентность по `external_id`
- 🖥️ **MT5-коллектор** — локальный скрипт читает историю сделок и пушит в Django
- 🎨 **Django Admin** — с фильтрами, date-hierarchy, поиском

## 🏗️ Стек

| Слой | Технологии |
|---|---|
| Backend | Python 3.12, Django 5.2, DRF, SimpleJWT |
| БД | PostgreSQL 18 |
| Auth | JWT (access + refresh), bcrypt |
| MT5 | MetaTrader5 (Python), `history_deals_get` |
| Тесты | pytest, pytest-django, 28 тестов |
| API docs | drf-spectacular (Swagger UI) |

## 🚀 Быстрый старт

### 1. Клонирование и установка

```powershell
git clone <repo-url>
cd trading_assistant

# Виртуальное окружение
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Зависимости
cd backend
pip install -r requirements.txt
2. Настройка PostgreSQL
powershell
# Создайте БД и пользователя (см. ROADMAP.md → Этап 1)
psql -U postgres -c "CREATE DATABASE trading_assistant_db OWNER trading_user;"
3. .env
Создайте backend/.env:

ini
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=trading_assistant_db
DB_USER=trading_user
DB_PASSWORD=change-me
DB_HOST=localhost
DB_PORT=5432
JWT_ACCESS_MINUTES=30
JWT_REFRESH_DAYS=7
MT5_API_TOKEN=change-me
4. Миграции и запуск
powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
Swagger UI: http://127.0.0.1:8000/api/docs/

Admin: http://127.0.0.1:8000/admin/

🧪 Тесты
powershell
cd backend
python -m pytest -v
28 тестов: 9 auth + 13 trades + 6 mt5-import.

📊 API
Метод	Путь	Описание
POST	/api/auth/register/	Регистрация
POST	/api/auth/login/	Логин (JWT)
POST	/api/auth/refresh/	Обновить access-токен
GET	/api/auth/me/	Текущий пользователь
POST	/api/auth/logout/	Logout (blacklist refresh)
GET	/api/trades/	Список сделок (фильтры, поиск, сортировка)
POST	/api/trades/	Создать сделку
GET	/api/trades/{id}/	Детали
PUT/PATCH	/api/trades/{id}/	Обновить
DELETE	/api/trades/{id}/	Удалить
GET	/api/trades/stats/	Статистика (Win Rate, PnL)
POST	/api/trades/import/mt5/	Импорт из MT5 (X-API-Key)
📁 Структура
text
trading_assistant/
├── backend/
│   ├── config/              # settings, urls, wsgi
│   ├── users/               # User, JWT auth
│   ├── trades/              # Trade, CRUD, MT5-import
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   └── admin.py
│   ├── market_data/         # (этап 5) котировки
│   ├── ai_agent/            # (этап 6) анализ скриншотов
│   ├── notifications/       # (этап 7) Telegram, FCM
│   ├── analytics/           # (этап 8) метрики
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_trades.py
│   │   └── test_mt5_import.py
│   ├── tools/mt5_collector/ # локальный коллектор MT5
│   ├── requirements.txt
│   └── manage.py
└── README.md, ROADMAP.md
📄 Лицензия
MIT
