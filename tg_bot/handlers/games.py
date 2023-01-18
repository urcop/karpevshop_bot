import logging
from random import randint

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from tg_bot.keyboards.inline.games import games_keyboard, choice_game_callback, game_keyboard, accept_game_callback
from tg_bot.keyboards.inline.lotterytickets import action_ticket_callback
from tg_bot.keyboards.inline.lotterytickets import generate_lottery_tickets_keyboard, lottery_ticket_callback, \
    buy_ticket_keyboard
from tg_bot.keyboards.inline.tower_game import tower_game_keyboard, tower_game_callback, tower_game_end_callback
from tg_bot.keyboards.reply.back_to_gold_menu import back_to_gold_keyboard
from tg_bot.keyboards.reply.gold_menu import gold_menu_keyboard
from tg_bot.models.history import GoldHistory
from tg_bot.models.lottery import LotteryTickets, TicketGames
from tg_bot.models.users import User
from tg_bot.services.tower_game import tower_game_session, calculate_tower_win
from tg_bot.states.tower_game_state import TowerState


async def get_games(message: types.Message):
    await message.answer('Игры 🎲:', reply_markup=games_keyboard)


async def get_game(call: types.CallbackQuery, callback_data: dict):
    game = callback_data.get("choice")
    text = ''
    if game == 'tower':
        text = "Башня - это игра, где вы делаете ставку в золоте и угадываете направление башни, поднимаясь все выше. " \
               "Чем выше вы поднимитесь, тем больше награда. " \
               "Если вы не угадали, игра заканчивается. " \
               "Максимальной коэффициент выигрыша 3X."
    elif game == 'jackpot':
        text = "Режим JackPot - Это предельно простой, но очень интересный режим. " \
               "Все участники вносят любую ставку золотом и образуется общий банк. " \
               "Каждый участник получает свой шанс на выигрыш, зависящий от его ставки. " \
               "Чем больше ставка, тем больше шанс выиграть. " \
               "Но и с маленьким шансом есть возможность выиграть весь банк! Мы берём 10% за выигрыш."
    elif game == 'lottery':
        text = "Мы запустили лотерею, покупайте билеты разной редкости, где вы сможете выиграть 10 000 золота! " \
               "Есть 3 вида редкости билета и его куша, от самого маленького к большому. " \
               "Выигрыш в билете зависит от вашей удачи."

    await call.message.edit_text(text, reply_markup=game_keyboard(game))


async def tower(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer('Минимальная Ставка 10G\n'
                              'Введите сумму ставки:', reply_markup=back_to_gold_keyboard)
    await TowerState.first()


async def tower_bet(message: types.Message, state: FSMContext):
    session_maker = message.bot['db']
    async with state.proxy() as data:
        try:
            data['current_bet'] = int(message.text)
        except ValueError:
            await message.answer('Введите целое число')

        if data['current_bet'] >= 10:
            await message.answer(f'Ваша ставка {data["current_bet"]}\n'
                                 f'Выберите кнопку',
                                 reply_markup=tower_game_keyboard(current_bet=data['current_bet']))
            await User.take_currency(session_maker=session_maker, telegram_id=message.from_user.id,
                                     currency_type='gold', value=data["current_bet"])
        else:
            await message.answer('Минимальная ставка 10G')


async def tower_game(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    current_step = int(callback_data.get('current_step'))
    config = call.bot['config']
    async with state.proxy() as data:
        if current_step + 1 != 5:
            if await tower_game_session(config):
                win = await calculate_tower_win(int(data['current_bet']), current_step + 1)
                await call.message.edit_text(
                    f'Поздравляем, Вы выиграли {win} золота.\n'
                    'Чтобы продолжить играть, нажмите кнопку ‘Лево’ или ‘Право’. '
                    'А если хотите забрать средства, жмите кнопку ‘забрать выигрыш’.',
                    reply_markup=tower_game_keyboard(current_bet=win,
                                                     current_step=current_step + 1))
            else:
                await state.finish()
                await call.message.delete()
                await call.message.answer('Упс, вам не повезло ☹️', reply_markup=gold_menu_keyboard)
        else:
            win = await calculate_tower_win(int(data['current_bet']), current_step + 1)
            await call.message.delete()
            await call.message.answer(f'Поздравляем, Вы выиграли {win} золота.', reply_markup=gold_menu_keyboard)
            await state.finish()


async def tower_game_end(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    session_maker = call.bot['db']
    win = int(callback_data.get('current_bet'))
    await call.message.delete()
    await call.message.answer(f'Поздравляем, Вы выиграли {win} золота.', reply_markup=gold_menu_keyboard)
    await User.add_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                            currency_type='gold', value=win)
    await GoldHistory.add_gold_purchase(session_maker=session_maker, telegram_id=call.from_user.id, gold=win)
    await state.finish()


async def jackpot(call: types.CallbackQuery):
    await call.answer('jackpot')


async def lottery(call: types.CallbackQuery):
    session_maker = call.bot['db']
    lottery_tickets: list = await LotteryTickets.get_all_lottery_tickets(session_maker)
    await call.message.edit_text('Выберите редкость билета:',
                                 reply_markup=generate_lottery_tickets_keyboard(lottery_tickets))


async def lottery_ticket(call: types.CallbackQuery, callback_data: dict):
    session_maker = call.bot['db']
    id = callback_data.get('id')
    price = callback_data.get('price')
    name = callback_data.get('name')
    ticket: str = await LotteryTickets.get_ticket(id=int(id), session_maker=session_maker)
    ticket_max_win = str(ticket).split(':')[-2]
    ticket_min_win = str(ticket).split(':')[-1]
    text = f'{name} - возможный выигрыш до {ticket_max_win} золота. ' \
           f'Случайным образом генерируется число от {ticket_min_win} до {ticket_max_win}. ' \
           f'Стоимость билета {price} золота.'
    await call.message.edit_text(text, reply_markup=buy_ticket_keyboard(ticket_id=id, price=price))


async def lottery_ticket_buy(call: types.CallbackQuery, callback_data: dict):
    session_maker = call.bot['db']
    user_gold = await User.get_gold(session_maker=session_maker, telegram_id=call.from_user.id)
    price = int(callback_data.get('price'))
    ticket_id = int(callback_data.get('id'))

    if int(user_gold) >= price:
        await User.take_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                 currency_type='gold', value=price)
        count_games = await TicketGames.get_count_games(user_id=call.from_user.id,
                                                        ticket_id=ticket_id,
                                                        session_maker=session_maker)
        if count_games % 3 == 0:
            win = int((price / 100 * randint(20, 45)) + price)
        elif count_games % 10 == 0:
            win = int((price / 100 * randint(50, 100)) + price)
        else:
            win = randint(0, price - 1)

        await TicketGames.add_game(user_id=call.from_user.id, ticket_id=ticket_id,
                                   bet=price, win=win, session_maker=session_maker)
        await User.add_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                currency_type='gold', value=win)

        await call.message.edit_text(f'Вы выиграли {win}G')
        logging.info(f'пользователь - {call.from_user.id} выиграл в лотерее {win}G')
    else:
        await call.message.edit_text('Недостаточно средств')


async def lottery_ticket_back(call: types.CallbackQuery):
    session_maker = call.bot['db']
    lottery_tickets: list = await LotteryTickets.get_all_lottery_tickets(session_maker)
    await call.message.edit_text('Выберите редкость билета:',
                                 reply_markup=generate_lottery_tickets_keyboard(lottery_tickets))


def register_games(dp: Dispatcher):
    dp.register_message_handler(get_games, text='Игры 🎲')
    dp.register_callback_query_handler(get_game, choice_game_callback.filter())
    dp.register_callback_query_handler(tower, accept_game_callback.filter(game_name='tower'))
    dp.register_message_handler(tower_bet, state=TowerState.current_bet)
    dp.register_callback_query_handler(tower_game, tower_game_callback.filter(), state=TowerState.current_bet)
    dp.register_callback_query_handler(tower_game_end, tower_game_end_callback.filter(), state=TowerState.current_bet)
    dp.register_callback_query_handler(jackpot, accept_game_callback.filter(game_name='jackpot'))
    dp.register_callback_query_handler(lottery, accept_game_callback.filter(game_name='lottery'))
    dp.register_callback_query_handler(lottery_ticket, lottery_ticket_callback.filter())
    dp.register_callback_query_handler(lottery_ticket_back, action_ticket_callback.filter(action='back'))
    dp.register_callback_query_handler(lottery_ticket_buy, action_ticket_callback.filter(action='buy'))
