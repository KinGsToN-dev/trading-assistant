@echo off
cd /d C:\projects\trading_assistant\backend\tools\mt5_collector
call C:\projects\trading_assistant\.venv\Scripts\activate.bat
python collector.py --loop --interval 5