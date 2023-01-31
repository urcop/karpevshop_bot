import datetime
import logging
from random import randint

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile

from tg_bot.keyboards.inline.access_buy_gold import access_keyboard
from tg_bot.keyboards.inline.output_items import types_keyboard, category_keyboard, quality_keyboard, \
    item_type_callback, item_category_callback, item_quality_callback, generate_output_keyboard, item_callback
from tg_bot.keyboards.reply import main_menu
from tg_bot.keyboards.reply.back_to_gold_menu import back_to_gold_keyboard
from tg_bot.keyboards.reply.gold_menu import gold_menu_keyboard
from tg_bot.misc.place_in_queue import place_in_queue
from tg_bot.misc.prefixes import get_prefix_type, prefixes, get_prefix_type_reverse
from tg_bot.models.history import GoldHistory
from tg_bot.models.items import Item, OutputQueue
from tg_bot.models.seasons import Season, Season2User
from tg_bot.models.users import User
from tg_bot.states.gold_output import GoldOutput


async def gold_menu(message: types.Message):
    await message.answer('Выберите действие в меню', reply_markup=gold_menu_keyboard)


async def back_to_gold_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Выберите действие в меню', reply_markup=gold_menu_keyboard)


async def back_button(message: types.Message):
    await message.answer('Главное меню ⬅️', reply_markup=main_menu.keyboard)


async def gold_calculate(message: types.Message, state: FSMContext):
    await message.answer('🥇 Введите количество золота', reply_markup=back_to_gold_keyboard)
    await state.set_state('calculate_gold')


async def get_gold_count(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        config = message.bot['config']
        try:
            data['count_gold'] = int(message.text)
        except ValueError:
            await message.answer('Введите целое число')
            return

        if data['count_gold'] >= config.misc.min_payment_value:
            price = round(data['count_gold'] * config.misc.gold_rate)
            await message.answer(f'Цена за {data["count_gold"]} золота, {price} руб.',
                                 reply_markup=back_to_gold_keyboard)
        else:
            await message.answer(f'Можно купить минимум {config.misc.min_payment_value + 1} золота')
            return


async def gold_exchange(message: types.Message, state: FSMContext):
    await message.answer('🥇 Введите количество золота для пополнения', reply_markup=back_to_gold_keyboard)
    await state.set_state('get_count_gold_exchange')


async def get_count_gold_exchange(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        config = message.bot['config']
        session_maker = message.bot['db']
        try:
            data['count_gold'] = int(message.text)
        except ValueError:
            await message.answer('Введите целое число')
            return

        if data['count_gold'] >= config.misc.min_payment_value:
            price = round(data['count_gold'] * config.misc.gold_rate)
            if await User.is_enough(session_maker=session_maker, telegram_id=message.from_user.id,
                                    currency_type='balance', count=price):
                await message.answer(f'С вашего счета будет списано {price} руб. за {message.text} золота.',
                                     reply_markup=access_keyboard)

            else:
                await message.answer(f'Стоимость покупки {data["count_gold"]} золота составляет {price} руб.\n'
                                     'На вашем счете недостаточно средств. Пополните баланс.')
                return
            return
        else:
            await message.answer(f'Можно купить минимум {config.misc.min_payment_value + 1} золота')
            return


async def access_buy(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        session_maker = call.bot['db']
        config = call.bot['config']
        price = round(data['count_gold'] * config.misc.gold_rate)
        await User.take_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                 currency_type='balance', value=price)
        await User.add_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                currency_type='gold', value=data['count_gold'])
        await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=call.from_user.id,
                                            gold=data['count_gold'])
        logging.info(f'Пользователь - {call.from_user.id} пополнил баланс на {data["count_gold"]}G')

        now = datetime.datetime.now().timestamp()
        current_season_id = await Season.get_current_season(session_maker, now)
        times = await Season.get_season_time(session_maker, current_season_id)

        gold_in_season = await GoldHistory.get_gold_user_period(session_maker, start_time=int(times[0]),
                                                                end_time=int(times[1]), user_id=call.from_user.id)
        prefix_type = await get_prefix_type(gold_in_season)
        current_prefix = await prefixes(prefix_type)
        prefix_in_db = await Season2User.get_user_prefix(session_maker=session_maker, telegram_id=call.from_user.id,
                                                         season_id=current_season_id)

        if current_prefix[1] != prefix_in_db:
            await Season2User.update_prefix(session_maker=session_maker, telegram_id=call.from_user.id,
                                            season_id=current_season_id, prefix=current_prefix[1])
            await User.add_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                    currency_type='gold', value=current_prefix[0])
            await call.message.answer(
                f'🎉 Поздравляем, вы получили награду в виде {current_prefix[0]} золота за достижение нового префикса. '
                f'Продолжайте открывать новые префиксы.')

            current_prefix_reverse = await get_prefix_type_reverse(prefix_in_db)
            if prefix_type - current_prefix_reverse > 1:
                for row in range(current_prefix_reverse, prefix_type):
                    reward = await prefixes(row)

                    await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=call.from_user.id,
                                                        gold=reward[0])
                    await User.add_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                            currency_type='gold', value=reward[0])
        await call.message.delete()
        await call.message.answer('Успешная покупка!', reply_markup=gold_menu_keyboard)
        await state.finish()


async def output(message: types.Message):
    await message.answer('🥇 Введите количество золота для вывода', reply_markup=back_to_gold_keyboard)
    await GoldOutput.first()


async def count_gold_output(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['count'] = int(message.text)
        except ValueError:
            await message.answer('Введите целое число')

    session_maker = message.bot['db']
    if data['count'] >= 50:
        user_gold = await User.get_gold(session_maker=session_maker, telegram_id=message.from_user.id)
        if user_gold >= data['count']:
            await message.answer('Выберите предмет для вывода:', reply_markup=types_keyboard)
            await GoldOutput.next()
        else:
            await message.answer('У вас недостаточно средств')
    else:
        await message.answer('Минимальная сумма 50 золота')


async def choosing_an_item_type(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    async with state.proxy() as data:
        try:
            if data['category'] == 'back':
                data.pop('category')
            if data['quality'] == 'back':
                data.pop('quality')
        except KeyError:
            pass

        data['type'] = int(callback_data.get('type'))
        if data['type'] == 1:
            await GoldOutput.category.set()
            await call.message.edit_text('Выберите категорию оружия', reply_markup=category_keyboard)
        else:
            if data['type'] in (2, 3):
                text = {
                    2: 'наклейки',
                    3: 'брелока'
                }
                await call.message.edit_text(f'Выберите качество {text[data["type"]]}',
                                             reply_markup=quality_keyboard)
                await GoldOutput.quality.set()


async def choosing_an_item_category(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    async with state.proxy() as data:
        data['category'] = callback_data.get('category')
        if data['category'] == 'back':
            await GoldOutput.type.set()
            await call.message.edit_text('Выберите предмет для вывода', reply_markup=types_keyboard)
        else:
            if data['type'] == 1:
                await call.message.edit_text(f'Выберите качество оружия',
                                             reply_markup=quality_keyboard)
                await GoldOutput.quality.set()


async def choosing_an_item_quality(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    async with state.proxy() as data:
        try:
            if data['category'] == 'back':
                data['category'] = 0
        except KeyError:
            data['category'] = 0

        data['quality'] = callback_data.get('quality')
        if data['quality'] == 'back' and data['category'] == 0:
            await GoldOutput.type.set()
            await call.message.edit_text('Выберите предмет для вывода', reply_markup=types_keyboard)
        elif data['quality'] == 'back' and data['type'] == 1:
            await GoldOutput.category.set()
            await call.message.edit_text('Выберите категорию оружия', reply_markup=category_keyboard)
        elif data['quality'] != 'back':
            session_maker = call.bot['db']
            await GoldOutput.item_name.set()
            items = [item[0] for item in
                     await Item.find_all_items(type=int(data['type']), category=int(data['category']),
                                               quality=int(data['quality']),
                                               session_maker=session_maker)]
            if len(items) > 0:
                await call.message.edit_text('Выберите предмет из списка',
                                             reply_markup=await generate_output_keyboard(items))
            else:
                await call.message.delete()
                await call.message.answer('Не найдены предметы в этой категории', reply_markup=gold_menu_keyboard)
                await state.finish()


async def choosing_an_item_name(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    async with state.proxy() as data:
        data['item_name'] = callback_data.get('name')
        if data['item_name'] == 'back':
            await GoldOutput.quality.set()
            if data['type'] == 1:
                await call.message.edit_text('Выберите качество оружия',
                                             reply_markup=quality_keyboard)
            elif data['type'] in (2, 3):
                text = {
                    2: 'наклейки',
                    3: 'брелока'
                }
                await call.message.edit_text(f'Выберите качество {text[data["type"]]}',
                                             reply_markup=quality_keyboard)
        else:
            data['price'] = int(int(data['count']) / 0.8) + randint(10, 99) / 100
            text = f"""🌟Отлично!

Теперь вам необходимо зайти в Standoff 2 и сделать скриншот, где выставлен {data['item_name']} на рынке за {data['price']} G.

❗️Не забудьте поставить галочку на рынке: <b>'Только мои запросы'</b>!

Когда все будет сделано, отправьте скриншот в этот диалог. Пример сверху ⬆️
            """
            example_photo_path = call.bot['config'].misc.base_dir / 'uploads'
            example_photo = InputFile(example_photo_path / 'example.jpg')
            await call.message.delete()
            await call.message.answer_photo(caption=text, photo=example_photo)
            await GoldOutput.photo.set()


async def get_photo_output(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        session_maker = message.bot['db']
        item_id = await Item.get_item_id_by_name(item_name=data['item_name'], session_maker=session_maker)
        config = message.bot['config']
        file_name = f'{message.from_user.id}_{randint(1000, 9999)}.jpg'
        await message.photo[-1].download(destination_file=config.misc.base_dir / 'uploads' / 'outputs' / file_name)
        user_nickname = message.from_user.username if message.from_user.username else message.from_user.full_name
        await User.take_currency(session_maker=session_maker, telegram_id=message.from_user.id,
                                 currency_type='gold', value=data['count'])
        await OutputQueue.add_to_queue(user_id=message.from_user.id, item_id=item_id, photo=file_name,
                                       user_nickname=user_nickname,
                                       gold=data['count'], session_maker=session_maker)
        admins_and_workers = await User.get_admins(session_maker) + await User.get_workers(session_maker)
        admins_and_workers = [user[0] for user in admins_and_workers]
        list(set(admins_and_workers))

        for user in admins_and_workers:
            await message.bot.send_message(chat_id=user,
                                           text=f'❗️Получен новый запрос на вывод от пользователя '
                                                f'{message.from_user.get_mention(f"@{user_nickname}")}')
        users = await OutputQueue.get_all_queue(session_maker)
        place = await place_in_queue(users, message.from_user.id)
        await message.answer('💫Ваш запрос на вывод добавлен, ожидайте.\n\n'
                             f'Вы {place[-1][0] + 1} в очереди', reply_markup=gold_menu_keyboard)
        await state.finish()


async def output_queue(message: types.Message):
    session_maker = message.bot['db']
    users = await OutputQueue.get_all_queue(session_maker)
    place = await place_in_queue(users, message.from_user.id)
    text = ['Ваша очередь']

    for p in place:
        text.append(f'{p[1]}G - №{p[0] + 1}')
    if len(text) > 1:
        await message.answer('\n'.join(text))
    else:
        await message.answer('У вас нет предметов на вывод!')


async def rewards(message: types.Message):
    session_maker = message.bot['db']
    now = datetime.datetime.now().timestamp()
    text = []
    current_season_id = await Season.get_current_season(session_maker, now)
    times = await Season.get_season_time(session_maker, current_season_id)

    current_prefix = await Season2User.get_user_prefix(session_maker=session_maker,
                                                       telegram_id=message.from_user.id,
                                                       season_id=current_season_id)
    current_prefix_type = await get_prefix_type_reverse(current_prefix)
    prev_prefix = await Season2User.get_user_prefix(session_maker=session_maker,
                                                    telegram_id=message.from_user.id,
                                                    season_id=current_season_id - 1)
    if current_season_id > 1:
        text.append(f'📂 {current_season_id - 1} Сезон: {prev_prefix}')

    text.append(f'📂 {current_season_id} Сезон: {current_prefix}')
    try:
        next_reward = await prefixes(current_prefix_type + 1)
        text.append(f'🎁 Следующая награда - {next_reward[0]}G')
    except KeyError:
        text.append(
            f'🎁 Вы блистательно справились с этим трудным путём, но это лишь начало чего-то более масштабного. '
            'Продолжайте идти по этому пути, но не сдавайте.'
        )
    next_season = datetime.datetime.fromtimestamp(times[1]) - datetime.datetime.fromtimestamp(now)
    text.append(
        f'\n🕛 Следующий сезон через {next_season.days} дней {next_season.seconds // 3600} часов '
        f'{next_season.seconds % 3600 // 60} минут'
    )
    await message.answer('\n'.join(text))


def register_gold(dp: Dispatcher):
    dp.register_message_handler(gold_menu, text='Золото 🥇')
    dp.register_message_handler(back_button, text='Главное меню ⬅️')
    dp.register_message_handler(back_to_gold_menu, text='Назад⬅️', state='*')
    dp.register_message_handler(gold_calculate, text='Посчитать 🥇')
    dp.register_message_handler(get_gold_count, state='calculate_gold')
    dp.register_message_handler(gold_exchange, text='Пополнить 🥇')
    dp.register_message_handler(get_count_gold_exchange, state='get_count_gold_exchange')
    dp.register_callback_query_handler(access_buy, state='get_count_gold_exchange', text='access_buy_gold')

    dp.register_message_handler(output, text='Вывести 🥇')
    dp.register_message_handler(count_gold_output, state=GoldOutput.count)
    dp.register_callback_query_handler(choosing_an_item_type, item_type_callback.filter(),
                                       state=GoldOutput.type)
    dp.register_callback_query_handler(choosing_an_item_category, item_category_callback.filter(),
                                       state=GoldOutput.category)
    dp.register_callback_query_handler(choosing_an_item_quality, item_quality_callback.filter(),
                                       state=GoldOutput.quality)
    dp.register_callback_query_handler(choosing_an_item_name, item_callback.filter(),
                                       state=GoldOutput.item_name)
    dp.register_message_handler(get_photo_output, state=GoldOutput.photo, content_types=['photo', 'document'])

    dp.register_message_handler(output_queue, text='Очередь 👥')
    dp.register_message_handler(rewards, text='Награды 🎁')
