import asyncio
import sys
from pathlib import Path

from tqdm import tqdm

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(base_dir))

from tg_bot.config import load_config
from tg_bot.misc.prefixes import get_prefix_type, prefixes
from tg_bot.models.history import GoldHistory
from tg_bot.models.seasons import Season, Season2User
from tg_bot.services.database import create_db_session


async def main(season_id):
    config = load_config()
    session_maker = await create_db_session(config)

    season_times = await Season.get_season_time(session_maker=session_maker, id=season_id)

    users = await Season2User.get_all_users(session_maker=session_maker, season_id=season_id)

    fail = 0
    success = 0
    for user in tqdm(users[31955:]):
        user_id = user[0]
        prefix_in_db = await Season2User.get_user_prefix(session_maker=session_maker, telegram_id=user_id,
                                                         season_id=season_id)

        gold_history = await GoldHistory.get_gold_user_period(session_maker, season_times[0], season_times[1], user_id)
        prefix_type = await get_prefix_type(gold_history)
        current_prefix = await prefixes(prefix_type)

        if prefix_in_db != current_prefix[1]:
            fail += 1
            await Season2User.update_prefix(session_maker, user_id, season_id, current_prefix[1])
        else:
            success += 1

    print(f'[LOG] у {success} все ок \n[LOG] у {fail} не все ок')


asyncio.run(main(2))
