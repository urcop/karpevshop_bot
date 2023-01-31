async def generate_text_top(top_users: list, period: str):
    period_text = 'недели' if period == 'week' else 'месяца'
    if len(top_users) > 10:
        stop = 10
    else:
        stop = len(top_users)

    text = [f'Топ донатеров {period_text}:']
    i = 0
    while i < stop:
        text.append(f'{i + 1}. {top_users[i][0]} - <code>{top_users[i][1]}</code> G')
        i += 1
    return text


async def generate_next_top_text(top_users: list, user_id: int):
    i = 0
    text = 'Вы не покупали золото в течении этого периода'
    while i < len(top_users):
        if i == 0 and top_users[i][0] == user_id:
            text = f'Вы на {i + 1} месте.'
            break
        elif top_users[i][0] == user_id:
            pred_golds = top_users[i - 1][1] - top_users[i][1]
            text = f'Вы на {i + 1} месте. Чтобы обогнать следующего пользователя, вам нужно купить {pred_golds} G. Займите первое место, чтобы получить вознаграждение.'
        i += 1
    return text
