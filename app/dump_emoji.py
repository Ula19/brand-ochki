"""Выгрузка ID всех премиум-эмодзи из набора.

Запуск: .venv/bin/python -m app.dump_emoji [имя_набора]

По умолчанию набор — tgmacicons (из ссылки https://t.me/addemoji/tgmacicons).
Печатает таблицу «эмодзи → custom_emoji_id» и готовый Python-словарь,
который можно вставить в app/emojis.py.
"""
import asyncio
import sys

from aiogram import Bot

from app.config import settings

DEFAULT_PACK = "tgmacicons"


async def main() -> None:
    pack = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PACK
    bot = Bot(token=settings.bot_token)
    try:
        sticker_set = await bot.get_sticker_set(pack)
    finally:
        await bot.session.close()

    print(f"Набор: {sticker_set.name} — «{sticker_set.title}», стикеров: {len(sticker_set.stickers)}\n")
    print(f"{'эмодзи':<8} custom_emoji_id")
    print("-" * 35)
    for s in sticker_set.stickers:
        print(f"{(s.emoji or '?'):<8} {s.custom_emoji_id}")

    print("\n# Готовый словарь для app/emojis.py:")
    print("E_ID = {")
    for s in sticker_set.stickers:
        print(f'    {s.emoji!r}: "{s.custom_emoji_id}",')
    print("}")


if __name__ == "__main__":
    asyncio.run(main())
