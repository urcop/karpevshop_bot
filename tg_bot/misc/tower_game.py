import random

from tg_bot.config import Config


async def calculate_tower_win(bet, step):
    if step == 1:
        return int(bet * 1.15)
    elif step == 2:
        return int(bet * 1.50)
    elif step == 3:
        return int(bet * 2)
    elif step == 4:
        return int(bet * 2.50)
    elif step == 5:
        return int(bet * 3)


async def tower_game_session(config: Config):
    win_chance = config.misc.tower_chance
    lose_chance = 1 - win_chance
    return bool(int(random.choices(['0', '1'], weights=[lose_chance, win_chance])[0]))
