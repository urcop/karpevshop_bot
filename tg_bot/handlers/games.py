from aiogram import types, Dispatcher

from tg_bot.keyboards.inline.games import games_keyboard, choice_game_callback, game_keyboard, accept_game_callback


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
    await call.answer('lottery')


def register_games(dp: Dispatcher):
    dp.register_message_handler(get_games, text='Игры 🎲')
    dp.register_callback_query_handler(get_game, choice_game_callback.filter())
    dp.register_callback_query_handler(tower, accept_game_callback.filter(game_name='tower'))
    dp.register_callback_query_handler(jackpot, accept_game_callback.filter(game_name='jackpot'))
    dp.register_callback_query_handler(lottery, accept_game_callback.filter(game_name='lottery'))
