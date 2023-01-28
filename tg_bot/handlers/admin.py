from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InputFile
from sqlalchemy.orm import sessionmaker

from tg_bot.keyboards.inline.output_items import returns_output_button, returns_output_callback
from tg_bot.keyboards.reply import main_menu
from tg_bot.keyboards.reply.support import support_keyboard
from tg_bot.keyboards.reply.worker import worker_keyboard
from tg_bot.models.history import GoldHistory, BalanceHistory, CaseHistory
from tg_bot.models.items import OutputQueue, Item
from tg_bot.models.promocode import Promocode
from tg_bot.models.users import User
from tg_bot.models.workers import Worker, Support
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
    await message.answer(f'Промокод <b>{name}</b> на <b>{count_use}</b> использований успешно добавлен!')


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


async def stat(message: types.Message):
    session_maker = message.bot['db']
    date = message.text.split(' ')
    gold = await GoldHistory.get_stats_params(session_maker, date[1])
    money = await BalanceHistory.get_stats_params(session_maker, date[1])
    text = [
        f'Статистика за {"все время" if date[1] == "all" else date[1]}',
        f'Пополнено денег: {money}',
        f'Продано золота: {gold}'
    ]
    await message.answer('\n'.join(text))


async def cinfo(message: types.Message):
    session_maker = message.bot['db']
    date = message.text.split(' ')
    money_spent = await CaseHistory.get_case_stats_money(session_maker=session_maker, date=date[1])
    gold_won = await CaseHistory.get_case_stats_gold(session_maker=session_maker, date=date[1])
    opened = await CaseHistory.get_case_stats_opened(session_maker=session_maker, date=date[1])
    text = [
        f'Статистика за {"все время" if date[1] == "all" else date[1]}',
        f'Открыто кейсов: {opened}',
        f'Потрачено денег: {money_spent}',
        f'Выиграно золота: {gold_won}'
    ]
    await message.answer('\n'.join(text))


async def add_worker(message: types.Message):
    session_maker = message.bot['db']
    text = message.text.split(' ')
    await User.set_role(user_id=int(text[1]), role='worker', session_maker=session_maker)
    await Worker.add_worker(user_id=int(text[1]), password=text[2], session_maker=session_maker)
    await message.answer('Работник добавлен!')
    await message.bot.send_message(chat_id=int(text[1]), text='Вас назначили работником')


async def delete_worker(message: types.Message):
    session_maker = message.bot['db']
    text = message.text.split(' ')
    await User.set_role(user_id=int(text[1]), role='user', session_maker=session_maker)
    await Worker.delete_worker(user_id=int(text[1]), session_maker=session_maker)
    await message.answer('Работник удален!')
    await message.bot.send_message(chat_id=int(text[1]), text='Вас сняли с должности работника')


async def add_support(message: types.Message):
    session_maker = message.bot['db']
    text = message.text.split(' ')
    await User.set_role(user_id=int(text[1]), role='support', session_maker=session_maker)
    await Support.add_support(user_id=int(text[1]), password=text[2], session_maker=session_maker)
    await message.answer('Работник добавлен!')
    await message.bot.send_message(chat_id=int(text[1]), text='Вас назначили работником тех поддержки')


async def delete_support(message: types.Message):
    session_maker = message.bot['db']
    text = message.text.split(' ')
    await User.set_role(user_id=int(text[1]), role='user', session_maker=session_maker)
    await Support.delete_support(user_id=int(text[1]), session_maker=session_maker)
    await message.answer('Работник тех. поддержки удален!')
    await message.bot.send_message(chat_id=int(text[1]), text='Вас сняли с должности работника тех. поддержки')


async def job(message: types.Message, state: FSMContext):
    session_maker = message.bot['db']
    text = message.text.split(' ')
    if text[1] == 'off':
        await Worker.set_active(user_id=message.from_user.id, active=False, session_maker=session_maker)
        await Support.set_active(user_id=message.from_user.id, active=False, session_maker=session_maker)
        await message.answer('Вы закончили работу', reply_markup=main_menu.keyboard)
        await state.finish()
    else:
        keyboard = None
        if await Worker.auth_worker(user_id=message.from_user.id, password=text[1], session_maker=session_maker):
            await Worker.set_active(user_id=message.from_user.id, active=True, session_maker=session_maker)
            await state.set_state('worker_in_job')
            keyboard = worker_keyboard
        elif await Support.auth_support(user_id=message.from_user.id, password=text[1], session_maker=session_maker):
            await Support.set_active(user_id=message.from_user.id, active=True, session_maker=session_maker)
            await state.set_state('support_in_job')
            keyboard = support_keyboard

        await message.answer('Успешная авторизация', reply_markup=keyboard)


async def output(message: types.Message):
    session_maker = message.bot['db']
    config = message.bot['config']
    if await OutputQueue.is_active(worker_id=message.from_user.id, session_maker=session_maker):
        await message.answer('Вы не завершили предыдущий вывод!')
        return

    first_free_ticket = str((await OutputQueue.get_first_free_queue(session_maker))[0]).split(':')
    id = int(first_free_ticket[0])
    user = int(first_free_ticket[1])
    gold = float(first_free_ticket[2])
    photo = first_free_ticket[3]
    item_id = int(first_free_ticket[4])
    user_nickname = first_free_ticket[5]

    item_name = await Item.get_item_name(id=item_id, session_maker=session_maker)
    photo_file = InputFile(config.misc.base_dir / 'uploads' / 'outputs' / photo)

    await OutputQueue.set_worker(worker_id=message.from_user.id, id=id, session_maker=session_maker)

    admins = await User.get_admins(session_maker)
    for admin in admins:
        await message.bot.send_message(chat_id=admin[0],
                                       text=f'{message.from_user.id} взял запрос пользователя {user}')

    text = [
        f'🔑ID: <code>{user}</code>',
        f'🔫Предмет: {item_name}',
        f'💵Цена предмета: {gold}',
        f'🔗Ссылка для связи https://t.me/{user_nickname}'
    ]
    await message.answer_photo(photo=photo_file, caption='\n'.join(text),
                               reply_markup=await returns_output_button(user_id=user, gold=int(int(gold) * 0.8),
                                                                        ticket_id=id))


async def finish(message: types.Message):
    session_maker = message.bot['db']
    admins = await User.get_admins(session_maker)
    taken_ticket = str((await OutputQueue.taken_ticket(worker_id=message.from_user.id, session_maker=session_maker))[0]).split(':')
    id = int(taken_ticket[0])
    user = int(taken_ticket[1])
    free_tickets = len(await OutputQueue.get_all_free_queue(session_maker=session_maker))

    for admin in admins:
        await message.bot.send_message(chat_id=admin[0],
                                       text=f'{message.from_user.id} завершил запрос пользователя {user}')
    await OutputQueue.delete_from_queue(id=id, session_maker=session_maker)
    await message.bot.send_message(chat_id=user, text='🎉 Запрос на вывод золота, успешно завершён!')
    await message.answer('Проверка закончена!\n'
                         f'Впереди еще {free_tickets}\n'
                         'Нажмите /output')


async def returns_output(call: types.CallbackQuery, callback_data: dict):
    session_maker = call.bot['db']
    user = int(callback_data.get('user_id'))
    gold = int(callback_data.get('gold'))
    id = int(callback_data.get('ticket_id'))
    await OutputQueue.delete_from_queue(id=id, session_maker=session_maker)
    admins = await User.get_admins(session_maker)
    for admin in admins:
        await call.bot.send_message(chat_id=admin[0],
                                    text=f'{call.from_user.id} выполнил возврат запроса пользователя {user}')
    await call.message.delete()
    await User.add_currency(session_maker, user, currency_type='gold', value=gold)
    await call.message.answer('Средства возвращены на баланс пользователя')
    await call.bot.send_message(chat_id=user, text='Средства вернулись обратно на ваш баланс')


def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(broadcaster, text_startswith='/ads', content_types=['text', 'photo'], is_admin=True)
    dp.register_message_handler(user_information, Command(['info']), is_admin=True)
    dp.register_message_handler(give_currency, Command(['giveg', 'givem']), is_admin=True)
    dp.register_message_handler(add_promo, Command(['promo']), is_admin=True)
    dp.register_message_handler(add_worker, Command(['ajob']), is_admin=True)
    dp.register_message_handler(add_support, Command(['arep']), is_admin=True)
    dp.register_message_handler(delete_support, Command(['drep']), is_admin=True)
    dp.register_message_handler(delete_worker, Command(['djob']), is_admin=True)
    dp.register_message_handler(stat, Command(['stat']), is_admin=True)
    dp.register_message_handler(cinfo, Command(['cinfo']), is_admin=True)
    dp.register_message_handler(tell, text_startswith='/tell', content_types=['text', 'photo'], is_admin=True)

    dp.register_message_handler(tell, text_startswith='/tell', content_types=['text', 'photo'], is_support=True)

    dp.register_message_handler(output, Command(['output']), state='worker_in_job', is_worker=True)
    dp.register_message_handler(finish, Command(['finish']), state='worker_in_job', is_worker=True)
    dp.register_callback_query_handler(returns_output, returns_output_callback.filter(), state='worker_in_job',
                                       is_worker=True)

    dp.register_message_handler(job, Command(['job']), state=['support_in_job', None], is_support=True)
    dp.register_message_handler(job, Command(['job']), state=['worker_in_job', None], is_worker=True)
