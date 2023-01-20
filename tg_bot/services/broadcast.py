import asyncio
import logging

from aiogram import Bot
from aiogram import exceptions


async def send_message(bot: Bot, user_id, text: str, disable_notification: bool = False) -> bool:
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        logging.error(f'Target [ID:{user_id}]: Bot blocked by user')
    except exceptions.TelegramAPIError:
        logging.exception(f"Target [ID:{user_id}]: failed")
    else:
        logging.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def broadcast(bot: Bot, users: list, text: str, disable_notifications: bool = False) -> int:
    count = 0
    try:
        for user_id in users:
            if await send_message(bot, user_id, text, disable_notifications):
                count += 1
            await asyncio.sleep(0.05)  # 20 messages per second (Limit: 30 messages per second)
    finally:
        logging.info(f"{count} messages successful sent.")

    return count