#!/bin/sh
set -e

echo "Применяю миграции БД..."
alembic upgrade head

echo "Запускаю бота..."
exec python bot.py
