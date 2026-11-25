@echo off
chcp 65001 > nul
cd /d "%~dp0"

REM 1. Создаем .venv и ставим зависимости, если первого запуска еще не было
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Первый запуск: создаем виртуальное окружение .venv...
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
)

REM 2. Создаем .env из шаблона, если его нет
if not exist ".env" (
    copy .env.example .env > nul
)

REM 3. Запускаем приложение через pythonw (без открытия и зависания консоли)
start "" ".\.venv\Scripts\pythonw.exe" run_desktop.py
exit