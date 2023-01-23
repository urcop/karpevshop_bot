from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Command
from sqlalchemy.orm import sessionmaker

from tg_bot.models.history import GoldHistory, BalanceHistory
from tg_bot.models.promocode import Promocode
from tg_bot.models.users import User
from tg_bot.services.broadcast import broadcast


async def broadcaster(message: types.Message):
    session_maker = message.bot['db']
    if message.content_type == 'photo':
        text = message.caption[4:]
        photo_id = message.photo[-1].file_id
    else:
        text = message.text[4:]
        photo_id = None
    users = [i[0] for i in await User.get_all_users(session_maker=session_maker)]
    await broadcast(bot=message.bot, users=users, text=text, disable_notifications=True,
                    message_type=message.content_type, photo_id=photo_id)


async def user_information(message: types.Message):
    session_maker = message.bot['db']
    text = message.text.split(' ')
    user_id = int(text[1])
    user_balance = await User.get_balance(session_maker=session_maker, telegram_id=user_id)
    user_gold = await User.get_gold(session_maker=session_maker, telegram_id=user_id)
    count_purchases = await GoldHistory.get_count_user_purchase(session_maker=session_maker,
                                                                telegram_id=message.from_user.id)
    user = User(telegram_id=user_id)
    count_refs = await User.count_referrals(session_maker=session_maker, user=user)

    text = [
        f'🔑 ID: {user_id}',
        f'💸 Баланс: {user_balance} руб.',
        f'💰 Золото: {user_gold}',
        '⏰ Запросов на вывод золота: 0',
        f'💵 Куплено золота: {count_purchases} за все время',
        f'👥 Количество приглашенных пользователей: {count_refs if count_refs else 0}'
    ]
    await message.answer('\n'.join(text))


async def generate_currency_text(type: str, notify_text: dict, session_maker: sessionmaker, count_currency: int,
                                 user_id: int):
    text = 'золота' if type == 'gold' else 'рублей'
    if count_currency > 0:
        await User.add_currency(session_maker=session_maker, telegram_id=user_id, currency_type=type,
                                value=count_currency)
        if type == 'gold':
            await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=user_id, gold=count_currency)
        else:
            await BalanceHistory.add_balance_purchase(session_maker=session_maker, telegram_id=user_id,
                                                      money=count_currency)

        notify_text['user_notify'] = f'На ваш счет зачислено {count_currency} {text}'
        notify_text['admin_confirm'] = f'На аккаунт пользователя {user_id} переведено {count_currency} {text}'
    elif count_currency < 0:
        count_currency = count_currency * -1
        await User.take_currency(session_maker=session_maker, telegram_id=user_id, currency_type=type,
                                 value=count_currency)
        notify_text['user_notify'] = f'С вашего счета снято {count_currency} {text}'
        notify_text['admin_confirm'] = f'Счет пользователя {user_id} снято {count_currency} {text}'
    return notify_text


async def give_currency(message: types.Message):
    session_maker = message.bot['db']
    text = message.text.split(' ')
    notify_text = {
        'admin_confirm': '',
        'user_notify': ''
    }

    user_id = int(text[1])
    count_currency = int(text[2])

    result = {}
    if text[0][1:] == 'givem':
        result = await generate_currency_text('balance', notify_text=notify_text, session_maker=session_maker,
                                              count_currency=count_currency, user_id=user_id)
    elif text[0][1:] == 'giveg':
        result = await generate_currency_text('gold', notify_text=notify_text, session_maker=session_maker,
                                              count_currency=count_currency, user_id=user_id)
    await message.answer(result['admin_confirm'])
    await message.bot.send_message(user_id, result['user_notify'])


async def add_promo(message: types.Message):
    session_maker = message.bot['db']
    text = message.text.split(' ')
    name = text[1]
    promo_type = text[2]
    value = int(text[3])
    count_use = int(text[4])

    if promo_type == 'g':
        promo_type = 'gold'
    elif promo_type == 'm':
        promo_type = 'balance'

    await Promocode.create_promo(session_maker=session_maker, code_name=name, currency=promo_type, count_use=count_use,
                                 value=value)
    await message.answer(f'Промокод <b>{name}</b> на <b>{count_use}</b> использований успешно добавлен!"')


async def tell(message: types.Message):
    text = message.text.split(' ') if message.content_type == 'text' else message.caption.split(' ')
    text.pop(0)
    user_id = int(text[0])
    text.pop(0)
    message_to_user = ' '.join(text)
    if message.content_type == 'text':
        await message.bot.send_message(user_id, message_to_user)
    elif message.content_type == 'photo':
        await message.copy_to(user_id, caption=message_to_user)


def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(broadcaster, text_startswith='/ads', content_types=['text', 'photo'], is_admin=True)
    dp.register_message_handler(user_information, Command(['info']), is_admin=True)
    dp.register_message_handler(give_currency, Command(['giveg', 'givem']), is_admin=True)
    dp.register_message_handler(add_promo, Command(['promo']), is_admin=True)

    dp.register_message_handler(tell, text_startswith='/tell', content_types=['text', 'photo'], is_admin=True)
    # dp.register_message_handler(tell, Command(['tell']), content_types=['photo', 'text'], is_support=True)
