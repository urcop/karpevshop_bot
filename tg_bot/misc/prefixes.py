async def get_prefix_type(gold):
    if gold is None:
        return 0
    elif 100 <= gold < 500:
        return 1
    elif 500 <= gold < 1500:
        return 2
    elif 1500 <= gold < 3000:
        return 3
    elif 3000 <= gold < 5000:
        return 4
    elif 5000 <= gold < 15000:
        return 5
    elif gold >= 15000:
        return 6
    else:
        return 0


async def prefixes(type_prefix):
    cost_prefix = {
        0: (0, 'Нет префикса'),
        1: (5, 'Новичок'),
        2: (10, 'Мальчик'),
        3: (25, 'Пацан'),
        4: (50, 'Король'),
        5: (100, 'Божество'),
        6: (250, 'Повелитель'),
    }
    return cost_prefix[type_prefix]


async def get_prefix_type_reverse(name):
    names = {
        'Нет префикса': 0,
        'Новичок': 1,
        'Мальчик': 2,
        'Пацан': 3,
        'Король': 4,
        'Божество': 5,
        'Повелитель': 6
    }
    return names[name]
