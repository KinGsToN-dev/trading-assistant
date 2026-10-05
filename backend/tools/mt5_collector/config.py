import os

# URL Django API
API_URL = os.getenv('TRADING_API_URL', 'http://127.0.0.1:8000')

# Токен из backend\.env (строка MT5_API_TOKEN=...)
API_TOKEN = os.getenv('MT5_API_TOKEN', '8eb638ba524b806de86de7a27b4f7fb10fd23b23ca0ff6cc')

DAYS_BACK = 7
MT5_LOGIN = os.getenv('MT5_LOGIN', '')
MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
MT5_SERVER = os.getenv('MT5_SERVER', '')