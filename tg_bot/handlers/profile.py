from aiogram import types, Dispatcher

from tg_bot.keyboards import inline_profile
from tg_bot.models.users import User


async def profile(message: types.Message):
    session_maker = message.bot['db']
    text = [
        f'🔑 ID: {message.from_user.id}',
        f'👤 Никнейм: {message.from_user.username if message.from_user.username else message.from_user.first_name}',
        f'💸 Баланс: 24140 руб.',
        f'💰 Золото: 12522',
        f'⏰ Запросов на вывод золота: 0',
        f'💵 Куплено золота: 32 за все время'
    ]
    await message.answer('\n'.join(text), reply_markup=inline_profile.keyboard)


async def referral_system(call: types.CallbackQuery):

    session_maker = call.bot['db']
    user = User(telegram_id=call.from_user.id)
    count_refs = await user.count_referrals(session_maker, user)
    text = [
        '❤️ За каждую покупку реферала вы получаете 5 золота',
        f'🔥 Ваша ссылка: https://t.me/karpevshop_bot?start={call.from_user.id}',
        f'👥 Количество приглашенных пользователей: {count_refs}'
    ]

    await call.message.answer('\n'.join(text))


async def promocode(call: types.CallbackQuery):
    ...


async def top_week(call: types.CallbackQuery):
    ...


async def top_month(call: types.CallbackQuery):
    ...


async def rules(call: types.CallbackQuery):
    await call.message.delete()
    text = [
        '1. Запрещено менять аватарку во время вывода.',
        '\t\t- Мы не несем ответственности за получение голды, если вы изменили аватарку.',
        '2. Запрещено снимать скин во время вывода.',
        '\t\t- Мы не несем ответственности за получение голды, если вы сняли скин и выставили опять.',
        '3. Запрещено менять цену скина.',
        '\t\t- Мы не несем ответственности за получение голды, если вы изменили цену скина во время вывода.',
        '4. Попытка обмана.',
        '\t\t- Блокировка аккаунта / обнуление',
        '5. Оскорбление.',
        '\t\t- Блокировка аккаунта / обнуление'
    ]
    await call.message.answer('\n'.join(text))


def register_profile(dp: Dispatcher):
    dp.register_message_handler(profile, text="Профиль 📝")
    dp.register_callback_query_handler(referral_system, text="profile_referral_system")
    dp.register_callback_query_handler(promocode, text="profile_promocode")
    dp.register_callback_query_handler(top_week, text="profile_top_week")
    dp.register_callback_query_handler(top_month, text="profile_top_month")
    dp.register_callback_query_handler(rules, text="profile_rules")

