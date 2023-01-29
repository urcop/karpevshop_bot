from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InputFile
from sqlalchemy.orm import sessionmaker

from tg_bot.keyboards.inline.output_items import returns_output_button, returns_output_callback
from tg_bot.keyboards.reply import main_menu, back_to_main
from tg_bot.keyboards.reply.admin import admin_keyboard
from tg_bot.models.case import Case, CaseItems
from tg_bot.models.history import GoldHistory, BalanceHistory, CaseHistory
from tg_bot.models.items import OutputQueue, Item
from tg_bot.models.lottery import TicketGames
from tg_bot.models.product import Product
from tg_bot.models.promocode import Promocode
from tg_bot.models.support import Tickets
from tg_bot.models.users import User, Referral
from tg_bot.models.workers import Worker, Support, WorkerHistory
from tg_bot.services.broadcast import broadcast
from tg_bot.states.product import AddProduct


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
    count_purchases = await GoldHistory.get_sum_user_purchase(session_maker=session_maker,
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
        await message.bot.send_message(user_id, text=f'<b>Администратор отправил вам сообщение:</b> {message_to_user}')
    elif message.content_type == 'photo':
        await message.copy_to(user_id, caption=f'<b>Администратор отправил вам сообщение:</b> {message_to_user}')


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
    dp: Dispatcher = message.bot['dp']
    text = message.text.split(' ')
    await User.set_role(user_id=int(text[1]), role='support', session_maker=session_maker)
    await Support.add_support(user_id=int(text[1]), password=text[2], session_maker=session_maker)
    await message.answer('Работник добавлен!')
    user_state = dp.current_state(chat=int(text[1]), user=int(text[1]))
    await user_state.finish()
    await message.bot.send_message(chat_id=int(text[1]), text='Вас назначили работником тех поддержки',
                                   reply_markup=main_menu.keyboard)


async def delete_support(message: types.Message):
    session_maker = message.bot['db']
    dp: Dispatcher = message.bot['dp']
    text = message.text.split(' ')
    await User.set_role(user_id=int(text[1]), role='user', session_maker=session_maker)
    await Support.delete_support(user_id=int(text[1]), session_maker=session_maker)
    await message.answer('Работник тех. поддержки удален!')
    user_state = dp.current_state(chat=int(text[1]), user=int(text[1]))
    await user_state.finish()
    await message.bot.send_message(chat_id=int(text[1]), text='Вас сняли с должности работника тех. поддержки',
                                   reply_markup=main_menu.keyboard)


async def admin_menu(message: types.Message, state: FSMContext):
    await message.answer('Меню администратора', reply_markup=admin_keyboard)
    await state.set_state('admin_in_job')


async def output(message: types.Message):
    session_maker = message.bot['db']
    config = message.bot['config']
    if await OutputQueue.is_active(worker_id=message.from_user.id, session_maker=session_maker):
        await message.answer('Вы не завершили предыдущий вывод!')
        return
    first_free_ticket = await OutputQueue.get_first_free_queue(session_maker)
    if first_free_ticket is None:
        await message.answer('Нет активных запросов')
        return
    first_free_ticket_split = str(first_free_ticket[0]).split(':')
    id = int(first_free_ticket_split[0])
    user = int(first_free_ticket_split[1])
    gold = float(first_free_ticket_split[2])
    photo = first_free_ticket_split[3]
    item_id = int(first_free_ticket_split[4])
    user_nickname = first_free_ticket_split[5]

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
                               reply_markup=await returns_output_button(user_id=user,
                                                                        gold=int(int(gold) * config.misc.gold_rate),
                                                                        ticket_id=id))


async def finish(message: types.Message):
    session_maker = message.bot['db']
    admins = await User.get_admins(session_maker)
    taken_ticket = await OutputQueue.taken_ticket(worker_id=message.from_user.id, session_maker=session_maker)
    if taken_ticket is None:
        await message.answer('У вас нет активных запросов')
        return
    taken_ticket_split = str((taken_ticket)[0]).split(':')
    id = int(taken_ticket_split[0])
    user = int(taken_ticket_split[1])
    gold = float(taken_ticket_split[2])
    free_tickets = len(await OutputQueue.get_all_free_queue(session_maker=session_maker))

    for admin in admins:
        await message.bot.send_message(chat_id=admin[0],
                                       text=f'{message.from_user.id} завершил запрос пользователя {user}')
    await OutputQueue.delete_from_queue(id=id, session_maker=session_maker)
    await message.bot.send_message(chat_id=user, text='🎉 Запрос на вывод золота, успешно завершён!')
    referrer = await Referral.get_referrer(telegram_id=user, session_maker=session_maker)
    if referrer:
        await message.bot.send_message(chat_id=referrer, text='Вы получили 5G за реферала')
        await User.add_currency(telegram_id=referrer, currency_type='gold', value=5, session_maker=session_maker)
        await GoldHistory.add_gold_purchase(telegram_id=referrer, gold=5, session_maker=session_maker)
    await message.answer('Проверка закончена!\n'
                         f'Впереди еще {free_tickets}\n'
                         'Нажмите /output')
    await WorkerHistory.add_worker_history(worker_id=message.from_user.id, gold=gold, session_maker=session_maker)


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


async def worker_stats(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    worker_id = int(params[1])
    date = params[2]
    gold_issued = await WorkerHistory.get_worker_stats(worker_id=worker_id, date=date, session_maker=session_maker)
    text = [
        f'Статистика работника за {"все время" if date == "all" else date}',
        f'Выведено {gold_issued} золота'
    ]
    await message.answer('\n'.join(text))


async def ticket_stats(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    date = params[1]

    games = TicketGames.get_count_games_period(date=date, session_maker=session_maker)
    sum_bets = TicketGames.get_sum_bets_period(date=date, session_maker=session_maker)
    win = TicketGames.get_sum_win_period(date=date, session_maker=session_maker)

    text = [
        f'Статистика лотереи за {"все время" if date == "all" else date}',
        f'Количество игр: {games}',
        f'Сумма: {sum_bets}',
        f'Выигрыш: {win}',
    ]
    await message.answer('\n'.join(text))

async def add_case(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    params.pop(0)
    price = int(params[0])
    params.pop(0)
    name = ' '.join(params)
    await Case.add_case(name=name, price=price, session_maker=session_maker)
    await message.answer(f'Кейс {name} успешно добавлен.')
    await message.answer(f'CASE ID: <code>{await Case.get_case_id(name=name, session_maker=session_maker)}</code>')


async def delete_case(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    name = params[1]
    await Case.delete_case(name=name, session_maker=session_maker)
    await message.answer(f'Кейс {name} удален')


async def change_case_visible(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    case_id = int(params[1])
    visible = bool(int(params[2]))
    case_name = await Case.get_case_name(id=case_id, session_maker=session_maker)

    await Case.change_visible(case_id=case_id, visible=visible, session_maker=session_maker)
    text = {
        False: f'Кейс {case_name} скрыт из списка',
        True: f'Кейс {case_name} добавлен в список'
    }
    await message.answer(text[visible])


async def add_case_item(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    case_id = int(params[1])
    price = int(params[2])
    chance = int(params[3])
    params.pop(3)
    params.pop(2)
    params.pop(1)
    params.pop(0)
    item_name = ' '.join(params)

    await CaseItems.add_case_item(case_id=case_id, game_price=price, chance=chance, item_name=item_name,
                                  session_maker=session_maker)
    await message.answer(f'Предмет {item_name} успешно добавлен.')


async def delete_case_item(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    params.pop(0)
    item_name = ' '.join(params)

    await CaseItems.delete_case_item(item_name=item_name, session_maker=session_maker)
    await message.answer(f'Предмет {item_name} удален')


async def delete_item(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    params.pop(0)
    category = int(params[0])
    params.pop(0)
    name = ' '.join(params)

    await Item.delete_item(category=category, name=name, session_maker=session_maker)
    await message.answer('Предмет успешно удален')


async def add_item(message: types.Message, state: FSMContext):
    params = message.text.split(' ')
    type_item = int(params[1])
    category_item = int(params[2])
    quality_item = int(params[3])

    type_item_text = {
        1: 'Оружие',
        2: 'Наклейка',
        3: 'Брелок'
    }
    category_item_text = {
        0: 'Без категории',
        1: 'Regular',
        2: 'StatTrack'
    }
    quality_item_text = {
        1: 'Arcane',
        2: 'Legendary',
        3: 'Epic',
        4: 'Rare',
    }
    text = f"""
Характеристики предмета:
Тип: {type_item_text[type_item]}
Категория: {category_item_text[category_item]}
Качество: {quality_item_text[quality_item]}
"""
    data = {
        'type': type_item,
        'category': category_item,
        'quality': quality_item,
    }
    await message.answer(text)
    await message.answer('Укажите название предмета')
    await state.set_state('add_item_name')
    await state.update_data(data=data)


async def add_item_name(message: types.Message, state: FSMContext):
    session_maker = message.bot['db']
    data = await state.get_data('add_item_name')
    name = message.text
    await Item.add_item(name=name, type=data['type'], category=data['category'], quality=data['quality'],
                        session_maker=session_maker)
    await message.answer('Предмет успешно добавлен')
    await state.finish()


async def delete_product(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    name = params[1]
    await Product.delete_product(name=name, session_maker=session_maker)
    await message.answer('Товар удален!')


async def add_product(message: types.Message):
    await message.answer('Укажите название товара', reply_markup=back_to_main.keyboard)
    await AddProduct.name.set()


async def add_product_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        await message.answer('Укажите описание товара')
        await AddProduct.description.set()


async def add_product_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
        await message.answer('Укажите цену товара')
        await AddProduct.price.set()


async def add_product_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = int(message.text)
        await message.answer('Отправьте фото товара')
        await AddProduct.photo.set()


async def add_product_photo(message: types.Message, state: FSMContext):
    session_maker = message.bot['db']
    config = message.bot['config']
    async with state.proxy() as data:
        await Product.add_product(data['name'], data['description'], price=int(data['price']),
                                  session_maker=session_maker)
        product_id = await Product.get_id(name=data['name'], session_maker=session_maker)
        photo_name = f'{product_id}.jpg'
        await message.photo[-1].download(
            destination_file=config.misc.base_dir / 'uploads' / 'aprods' / photo_name)
        await Product.add_photo(id=product_id, photo=photo_name, session_maker=session_maker)
        await message.answer('Товар успешно добавлен', reply_markup=main_menu.keyboard)
        await state.finish()


async def support_stats(message: types.Message):
    session_maker = message.bot['db']
    params = message.text.split(' ')
    support_id = int(params[1])
    date = params[2]

    done = await Tickets.get_done_support_tickets(support_id=support_id, date=date, session_maker=session_maker)
    canceled = await Tickets.get_cancel_support_tickets(support_id=support_id, date=date, session_maker=session_maker)

    await message.answer(f"За {date} работник {support_id}\n"
                         f"Ответил на {done} тикетов\n"
                         f"Отклонил {canceled} тикетов")


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
    dp.register_message_handler(worker_stats, Command(['ijob']), is_admin=True)
    dp.register_message_handler(ticket_stats, Command(['ticket']), is_admin=True)
    dp.register_message_handler(add_case, Command(['addcase']), is_admin=True)
    dp.register_message_handler(delete_case, Command(['dcase']), is_admin=True)
    dp.register_message_handler(add_case_item, Command(['addcaseitem']), is_admin=True)
    dp.register_message_handler(delete_case_item, Command(['dcaseitem']), is_admin=True)
    dp.register_message_handler(change_case_visible, Command(['casevisible']), is_admin=True)
    dp.register_message_handler(delete_item, Command(['ditem']), is_admin=True)
    dp.register_message_handler(add_item, Command(['aitem']), is_admin=True)
    dp.register_message_handler(add_item_name, state='add_item_name', is_admin=True)
    dp.register_message_handler(delete_product, Command(['dprod']), is_admin=True)
    dp.register_message_handler(add_product, Command(['addproduct']), is_admin=True)
    dp.register_message_handler(support_stats, Command(['rep']), is_admin=True)
    # dp.register_message_handler(add_product, Command(['ref']), is_admin=True)
    dp.register_message_handler(add_product_name, state=AddProduct.name, is_admin=True)
    dp.register_message_handler(add_product_description, state=AddProduct.description, is_admin=True)
    dp.register_message_handler(add_product_price, state=AddProduct.price, is_admin=True)
    dp.register_message_handler(add_product_photo, state=AddProduct.photo, content_types=['photo'], is_admin=True)

    dp.register_message_handler(admin_menu, Command(['admin']), is_admin=True)
    dp.register_message_handler(output, Command(['output']), state='admin_in_job', is_admin=True)
    dp.register_message_handler(finish, Command(['finish']), state='admin_in_job', is_admin=True)

    dp.register_message_handler(tell, text_startswith='/tell', content_types=['text', 'photo'], is_admin=True)

    dp.register_callback_query_handler(returns_output, returns_output_callback.filter(), state='admin_in_job',
                                       is_admin=True)
