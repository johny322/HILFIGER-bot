from asyncio import sleep

from aiogram.exceptions import AiogramError 
from loguru import logger

from data import texts

async def notify_users(bot, users):
    for user_id in users:
        try:
            await bot.send_message(user_id, texts.notify_answer)
        except AiogramError as ex:
            print(ex, user_id)
            logger.error(ex)

        await sleep(0.2)
