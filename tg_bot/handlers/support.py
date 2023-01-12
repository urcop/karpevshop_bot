from aiogram import types, Dispatcher

from tg_bot.keyboards.inline import support


def support_text():
    text = [
        '1. Почему я пополняю в гривнах, а мне пришло меньше рублей, чем пишет в интернете?',
        '2. Сколько по времени выводят золото?',
        '3. Почему так долго проверяют чек?',
        '4. Почему мне не пришли деньги?',
        '5. Безопасно ли у вас покупать?',
        '6. Можно ли вам продать золото/кланы/аккаунт/скины?',
        '7. Почему так долго выводят золото?',
        '\nЕсли вы не смогли найти ответ, нажмите кнопку связаться'
    ]
    return '\n'.join(text)


async def support_questions(message: types.Message):
    await message.answer(support_text(), reply_markup=support.keyboard)


async def support_question(call: types.CallbackQuery, callback_data: dict):
    answers = {
        1: 'Мы не являемся биржей валют, вы у нас покупаете золото, а не рубли. То есть, мы переводим ваши гривны в золото. После, золото в рубли.',
        2: 'Вывод золота происходит до 24 часов от запроса на вывод. Но в большинстве вывод происходит от нескольких секунд до часа.',
        3: 'Чеки проверяются в ручную, а не автоматически. Если вы пополнили рано утром или поздно вечером, то наши сотрудники не смогут проверить чек. Проверка чека занимает до 24 часов.',
        4: "Если вы пополняли через QIWI, то найдите сообщение где вам выдали ссылку на оплату, и под этим сообщением будет кнопка «Проверить оплату» нажмите её. Но если вы пополняли другим способом, то вы, возможно, скинули боту чек файлом. В подобном случае, нажмите: ' Пополнить баланс '; укажите сумму; ' Другим способом '; ' Отправить чек '. После, отправьте скриншот чека.",
        5: 'Весь товар, который продаётся в боте, получен честным путём. Если вы сомневаетесь в безопасности, то лучше покупать в игре.',
        6: 'Мы не покупаем товары других пользователей, так как, не знаем, откуда они их достали, а если знаем, это не является гарантией безопасности. Безопасность пользователей на первом месте для нас, и мы продаём только свои товары, в которых уверенны на 100%',
        7: 'Вывод золота занимает до 24 часов. Но мы стараемся как можно быстрее вывести вам золото. В большинстве случаев, есть очередь, и пока она дойдёт до вас, может пройти немного времени. Но если вы уже пол часа как на 1 месте, это может быть из-за проблем с рынком ( сложно искать скин) или работник взял перерыв.',
    }
    question_id = int(callback_data.get('question_id'))
    await call.message.edit_text(text=answers[question_id], reply_markup=support.answer_menu_keyboard)


async def answer_action(call: types.CallbackQuery, callback_data: dict):
    action = callback_data.get('action')
    if action == 'contact':
        ...
    elif action == 'back':
        await call.message.edit_text(support_text(), reply_markup=support.keyboard)


def register_support(dp: Dispatcher):
    dp.register_message_handler(support_questions, text="Тех. поддержка 👤")
    dp.register_callback_query_handler(support_question, support.support_callback.filter())
    dp.register_callback_query_handler(answer_action, support.support_menu_callback.filter())
