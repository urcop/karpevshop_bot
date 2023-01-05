from aiogram import types, Dispatcher


# Главное меню - Отзывы
async def reviews(message: types.Message):
    await message.answer('Наши отзывы: @gkarpev_reviews')


def register_reviews(dp: Dispatcher):
    dp.register_message_handler(reviews, text='Отзывы 👥')
