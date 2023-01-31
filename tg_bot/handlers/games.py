import asyncio
import datetime
import logging
import random
from random import randint

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from tg_bot.keyboards.inline.games import games_keyboard, choice_game_callback, game_keyboard, accept_game_callback
from tg_bot.keyboards.inline.jackpot import jackpot_keyboard, jackpot_callback
from tg_bot.keyboards.inline.lotterytickets import action_ticket_callback
from tg_bot.keyboards.inline.lotterytickets import generate_lottery_tickets_keyboard, lottery_ticket_callback, \
    buy_ticket_keyboard
from tg_bot.keyboards.inline.tower_game import tower_game_keyboard, tower_game_callback, tower_game_end_callback
from tg_bot.keyboards.reply.back_to_gold_menu import back_to_gold_keyboard
from tg_bot.keyboards.reply.gold_menu import gold_menu_keyboard
from tg_bot.misc.tower_game import tower_game_session, calculate_tower_win
from tg_bot.models.history import GoldHistory
from tg_bot.models.jackpot import JackpotGame, JackpotBets
from tg_bot.models.lottery import LotteryTickets, TicketGames
from tg_bot.models.tower import TowerGames
from tg_bot.models.users import User
from tg_bot.states.tower_game_state import TowerState


async def generate_jackpot_text(room, session_maker):
    users = await JackpotBets.get_users(room_id=room, session_maker=session_maker)
    time_now = datetime.datetime.fromtimestamp(int(datetime.datetime.now().timestamp()))
    end_time = await JackpotGame.get_end_time(room_id=room, session_maker=session_maker)
    remaining_time = datetime.datetime.fromtimestamp(end_time) - time_now
    all_bets = await JackpotBets.get_sum_bets(room_id=room, session_maker=session_maker)
    chances = [int(user[1] / all_bets * 100) for user in users]
    users_text = [f'{index + 1}: {user[0]} - {user[1]}: {chances[index]}%' for index, user in enumerate(users)]
    text = [f'Банк {all_bets}', f'Время: {str(remaining_time)}\n', f'Пользователи:', '\n'.join(users_text)]
    return text


async def get_games(message: types.Message):
    await message.answer('Игры 🎲:', reply_markup=games_keyboard)


async def get_game(call: types.CallbackQuery, callback_data: dict):
    game = callback_data.get("choice")
    text = {
        'tower': "Башня - это игра, где вы делаете ставку в золоте и угадываете направление башни, поднимаясь все выше. "
                 "Чем выше вы поднимитесь, тем больше награда. "
                 "Если вы не угадали, игра заканчивается. "
                 "Максимальной коэффициент выигрыша 3X.",
        'jackpot': "Режим JackPot - Это предельно простой, но очень интересный режим. "
                   "Все участники вносят любую ставку золотом и образуется общий банк. "
                   "Каждый участник получает свой шанс на выигрыш, зависящий от его ставки. "
                   "Чем больше ставка, тем больше шанс выиграть. "
                   "Но и с маленьким шансом есть возможность выиграть весь банк! Мы берём 10% за выигрыш.",
        'lottery': "Мы запустили лотерею, покупайте билеты разной редкости, где вы сможете выиграть 10 000 золота! "
                   "Есть 3 вида редкости билета и его куша, от самого маленького к большому. "
                   "Выигрыш в билете зависит от вашей удачи."
    }

    await call.message.edit_text(text[game], reply_markup=game_keyboard(game))


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
    session_maker = call.bot['db']
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
                await TowerGames.add_game(user_id=call.from_user.id, bet=int(data['current_bet']), win=0,
                                          session_maker=session_maker)
                await state.finish()
                await call.message.delete()
                await call.message.answer('Упс, вам не повезло ☹️', reply_markup=gold_menu_keyboard)
        else:
            win = await calculate_tower_win(int(data['current_bet']), current_step + 1)
            await TowerGames.add_game(user_id=call.from_user.id, bet=int(data['current_bet']), win=win,
                                      session_maker=session_maker)
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


async def jackpot(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    session_maker = call.bot['db']
    room = await JackpotGame.check_available_room(session_maker)
    action = callback_data.get('action')
    if not action:
        if room:
            text = await generate_jackpot_text(room, session_maker)
            await call.message.edit_text('\n'.join(text), reply_markup=await jackpot_keyboard(room_id=room))
        else:
            await call.message.edit_text('Банк 0G\n'
                                         'Время: Ожидаем ставки', reply_markup=await jackpot_keyboard())
            return

    if action == 'bet':
        await call.message.delete()
        await call.message.answer('Введите сумму ставки', reply_markup=back_to_gold_keyboard)
        await state.set_state('jackpot_bet')
    elif action == 'refresh':
        if room:
            text = await generate_jackpot_text(room, session_maker)
            await call.message.delete()
            await call.message.answer('\n'.join(text), reply_markup=await jackpot_keyboard(room_id=room))
        else:
            await call.message.delete()
            await call.message.answer('Банк 0G\n'
                                      'Время: Ожидаем ставки', reply_markup=await jackpot_keyboard())
            return


async def get_jackpot_bet(message: types.Message, state: FSMContext):
    session_maker = message.bot['db']
    async with state.proxy() as data:
        try:
            data['bet'] = int(message.text)
        except ValueError:
            await message.answer('Введите целое число')
            return

        if data['bet'] >= 10:
            if await User.is_enough(session_maker, message.from_user.id, 'gold', data['bet']):
                room = await JackpotGame.check_available_room(session_maker=session_maker)
                if not room:
                    unix_time = int(datetime.datetime.now().timestamp()) + 600
                    await JackpotGame.create_room(session_maker=session_maker, end_time=unix_time)
                    room = await JackpotGame.check_available_room(session_maker=session_maker)
                    loop = asyncio.get_event_loop()
                    loop.create_task(jackpot_game(message.bot, session_maker, room))
                    await JackpotBets.add_bet(user_id=message.from_user.id, room_id=room, bet=data['bet'],
                                              session_maker=session_maker)
                else:
                    await JackpotBets.add_bet(user_id=message.from_user.id, room_id=room, bet=data['bet'],
                                              session_maker=session_maker)
                await User.take_currency(session_maker, message.from_user.id, 'gold', data['bet'])
                await message.answer('Ваша ставка принята', reply_markup=gold_menu_keyboard)
                await state.finish()
            else:
                await message.answer('У вас недостаточно средств')
                return
        else:
            await message.answer('Минимальная ставка 10 G')
            return


async def jackpot_game(bot, session_maker, room_id):
    logging.info('Jackpot game started')
    await asyncio.sleep(600)
    logging.info('Jackpot game finishing')
    users = await JackpotBets.get_users(room_id=room_id, session_maker=session_maker)
    if len(users) == 1:
        await JackpotGame.update_active_room(room_id, -1, session_maker)
        await bot.send_message(users[0][0], text='Другие игроки не сделали ставки!\n'
                                                 f'Вам возвращено: {users[0][1]}G')
        await User.add_currency(session_maker, users[0][0], 'gold', users[0][1])
        await JackpotGame.update_params_room(room_id, users[0][0], users[0][1], bot_jackpot=0,
                                             session_maker=session_maker)
    else:
        bank = await JackpotBets.get_sum_bets(room_id, session_maker)
        users_clear = [user[0] for user in users]
        chances = [user[1] / bank for user in users]
        winner = (random.choices(users_clear, weights=chances))[0]
        await JackpotGame.update_active_room(room_id, 0, session_maker)
        winner_winning = bank / 100 * 90
        bot_win = bank / 100 * 10
        await User.add_currency(session_maker, winner, 'gold', winner_winning)
        await JackpotGame.update_params_room(room_id, winner, int(winner_winning), bot_jackpot=bot_win,
                                             session_maker=session_maker)

        await bot.send_message(chat_id=winner, text='Поздравляем!\n'
                                                    f'Вы выиграли {int(winner_winning)}G в JackPot')
        users_clear.remove(winner)
        for user in users_clear:
            lose = await JackpotBets.get_user_bet(room_id, user, session_maker)
            await bot.send_message(user, f'Вы проиграли {lose}G в JackPot')


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
    dp.register_callback_query_handler(jackpot, jackpot_callback.filter())
    dp.register_message_handler(get_jackpot_bet, state='jackpot_bet')
    dp.register_callback_query_handler(lottery, accept_game_callback.filter(game_name='lottery'))
    dp.register_callback_query_handler(lottery_ticket, lottery_ticket_callback.filter())
    dp.register_callback_query_handler(lottery_ticket_back, action_ticket_callback.filter(action='back'))
    dp.register_callback_query_handler(lottery_ticket_buy, action_ticket_callback.filter(action='buy'))
