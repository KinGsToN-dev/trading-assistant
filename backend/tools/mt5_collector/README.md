# MT5 Collector

Читает закрытые сделки из MT5 и отправляет в Django API.

## Установка
pip install MetaTrader5 requests

## Настройка
1. Откройте config.py
2. Замените API_TOKEN на значение MT5_API_TOKEN из backend\.env

## Запуск
python collector.py
python collector.py --loop
python collector.py --loop --interval 30