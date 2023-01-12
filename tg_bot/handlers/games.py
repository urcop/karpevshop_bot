import logging
from random import randint

from aiogram import types, Dispatcher

from tg_bot.keyboards.inline.games import games_keyboard, choice_game_callback, game_keyboard, accept_game_callback
from tg_bot.keyboards.inline.lotterytickets import action_ticket_callback
from tg_bot.keyboards.inline.lotterytickets import generate_lottery_tickets_keyboard, lottery_ticket_callback, \
    buy_ticket_keyboard
from tg_bot.models.lottery import LotteryTickets, TicketGames
from tg_bot.models.users import User


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
    await call.answer('tower')


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
    dp.register_callback_query_handler(jackpot, accept_game_callback.filter(game_name='jackpot'))
    dp.register_callback_query_handler(lottery, accept_game_callback.filter(game_name='lottery'))
    dp.register_callback_query_handler(lottery_ticket, lottery_ticket_callback.filter())
    dp.register_callback_query_handler(lottery_ticket_back, action_ticket_callback.filter(action='back'))
    dp.register_callback_query_handler(lottery_ticket_buy, action_ticket_callback.filter(action='buy'))
