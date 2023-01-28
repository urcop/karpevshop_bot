import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tg_bot.config import load_config
from tg_bot.filters.admin import AdminFilter
from tg_bot.filters.support import SupportFilter
from tg_bot.filters.worker import WorkerFilter
from tg_bot.handlers.admin import register_admin_handlers
from tg_bot.handlers.cases import register_cases
from tg_bot.handlers.games import register_games
from tg_bot.handlers.gold import register_gold
from tg_bot.handlers.other_items import register_other_items
from tg_bot.handlers.payments import register_payments
from tg_bot.handlers.profile import register_profile
from tg_bot.handlers.reviews import register_reviews
from tg_bot.handlers.start import register_start
from tg_bot.handlers.support import register_support
from tg_bot.middlewares.db import DbMiddleware
from tg_bot.middlewares.support_middleware import SupportMiddleware
from tg_bot.services.cron import top_month, top_week, start_new_season
from tg_bot.services.database import create_db_session

logger = logging.getLogger(__name__)


def register_all_middlewares(dp):
    dp.setup_middleware(DbMiddleware())
    dp.setup_middleware(SupportMiddleware())


def register_all_filters(dp):
    dp.bind_filter(AdminFilter)
    dp.bind_filter(SupportFilter)
    dp.bind_filter(WorkerFilter)


def register_all_handlers(dp):
    register_start(dp)
    register_profile(dp)
    register_reviews(dp)
    register_support(dp)
    register_cases(dp)
    register_payments(dp)
    register_gold(dp)
    register_games(dp)
    register_admin_handlers(dp)
    register_other_items(dp)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s'
    )
    config = load_config('.env')

    bot = Bot(token=config.bot.token, parse_mode='HTML')
    storage = RedisStorage2(host=config.redis.host,
                            password=config.redis.password,
                            port=config.redis.port) if config.bot.use_redis else MemoryStorage()
    logger.info('storage creating')
    dp = Dispatcher(bot, storage=storage)

    bot['config'] = config
    bot['dp'] = dp
    try:
        bot['db'] = await create_db_session(config)
        logger.info('db started')
    except Exception as e:
        logger.error(f'db can`t start cause: {e}')

    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(top_month, trigger='cron', hour=0,
                      minute=0, day=1, month='1-12',
                      kwargs={'bot': bot})

    scheduler.add_job(top_week, trigger='cron', hour=0,
                      minute=0, day_of_week=0, kwargs={'bot': bot})

    scheduler.add_job(start_new_season, trigger='cron', day='*',
                      hour=0, minute=0, kwargs={'bot': bot})

    scheduler.start()

    register_all_middlewares(dp)
    register_all_filters(dp)
    register_all_handlers(dp)

    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
        logger.info('Bot started!')
    except (KeyboardInterrupt, SystemExit):
        logger.error('Bot stopped!')
