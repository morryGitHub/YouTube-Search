import asyncio
import os

from aiogram import Bot, Dispatcher
import logging
from dotenv import load_dotenv

from handlers.user import user

load_dotenv()


async def main():
    bot = Bot(token=os.getenv('API_TOKEN'))

    dp = Dispatcher()
    dp.include_router(user)

    await process_last_pending_update(bot)  # <- обработка только последнего
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def process_last_pending_update(bot):
    # Получаем все необработанные апдейты
    updates = await bot.get_updates(limit=10, timeout=0)

    if not updates:
        return

    # Берем последнее сообщение
    last_update = updates[-1]

    # Проверка: это сообщение?
    if last_update.message:
        chat_id = last_update.message.chat.id
        text = last_update.message.text

        # Отвечаем только на последнее сообщение
        await bot.send_message(chat_id, f"🔁 Бот снова в сети!\nВы писали: {text}")


if '__main__' == __name__:
    logging.basicConfig(level=logging.INFO)
    print("Bot is running")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
