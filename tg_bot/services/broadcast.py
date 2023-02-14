import asyncio
import logging

from aiogram import Bot
from aiogram.utils import exceptions

from tg_bot.models.seasons import Season2User
from tg_bot.models.users import User


async def send_message(bot: Bot, user_id, text: str, disable_notification: bool = False) -> bool:
    session = bot['db']
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        logging.error(f'Target [ID:{user_id}]: Bot blocked by user')
    except exceptions.ChatNotFound:
        logging.exception(f'Target [ID:{user_id}]: ChatNotFound')
    except exceptions.UserDeactivated:
        logging.exception(f'Target [ID:{user_id}]: User Deactivated')
        await User.delete_user(telegram_id=user_id, session_maker=session)
        await Season2User.delete_user(user_id=user_id, session_maker=session)
    except exceptions.TelegramAPIError:
        logging.exception(f'Target [ID:{user_id}]: Failed')
    else:
        logging.info(f'Target [ID:{user_id}]: success')
        return True
    return False


async def send_photo(bot: Bot, user_id, text: str, photo_id: str, disable_notification: bool = False) -> bool:
    session = bot['db']
    try:
        await bot.send_photo(user_id, photo_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        logging.error(f'Target [ID:{user_id}]: Bot blocked by user')
    except exceptions.ChatNotFound:
        logging.exception(f'Target [ID:{user_id}]: ChatNotFound')
    except exceptions.UserDeactivated:
        logging.exception(f'Target [ID:{user_id}]: User Deactivated')
        await User.delete_user(telegram_id=user_id, session_maker=session)
        await Season2User.delete_user(user_id=user_id, session_maker=session)
    except exceptions.TelegramAPIError:
        logging.exception(f'Target [ID:{user_id}]: failed')
    else:
        logging.info(f'Target [ID:{user_id}]: success')
        return True
    return False


async def broadcast(bot: Bot, users: list, text: str, message_type: str, disable_notifications: bool = False,
                    photo_id: str = None) -> int:
    count = 0
    try:
        for user_id in users:
            if message_type == 'text':
                if await send_message(bot, user_id, text, disable_notifications):
                    count += 1
            elif message_type == 'photo':
                if await send_photo(bot, user_id, text, photo_id, disable_notifications):
                    count += 1
            await asyncio.sleep(0.033)
    finally:
        logging.info(f"{count} messages successful sent.")

    return count
