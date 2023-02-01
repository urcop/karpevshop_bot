import logging

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from tg_bot.keyboards.inline import payment
from tg_bot.keyboards.reply import main_menu, back_to_main
from tg_bot.models.history import BalanceHistory
from tg_bot.models.users import User
from tg_bot.services.payment import Payment, NoPaymentFound, NotEnoughMoney
from tg_bot.states.payment_state import PaymentState


async def get_payment(message: types.Message):
    await message.answer('💳 Введите сумму в рублях', reply_markup=back_to_main.keyboard)
    await PaymentState.amount.set()


async def get_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['amount'] = int(message.text)
            min_payment = message.bot['config'].qiwi.min_payment_qiwi
            if data['amount'] >= min_payment:
                await message.answer(f'Вы хотите пополнить баланс на {data["amount"]} руб.\n'
                                     f'Выберите способ оплаты:', reply_markup=payment.choice_keyboard)
            else:
                await message.answer('Минимальная сумма пополнения 10 рублей')
        except ValueError:
            await message.answer('Введите целое число')


async def get_payment_system(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    async with state.proxy() as data:
        config = call.bot['config']
        payment_amount = data['amount']
        payment_system = callback_data.get('choice')
        if payment_system == 'QIWI':
            url = Payment(amount=payment_amount)
            url.create()
            await call.message.delete()
            await call.message.answer('Не забудьте нажать кнопку <b>Проверить оплату</b> для подтверждения оплаты',
                                      reply_markup=main_menu.keyboard)
            await call.message.answer(
                text=f'Вам нужно отправить  {payment_amount} руб на наш счет Qiwi\n'
                     f'Ссылка: <a href="{url.invoice}">{url.invoice[:40]}...</a>\n'
                     f'Указав комментарий: \n<code>{url.id}</code>',
                reply_markup=payment.generate_qiwi_keyboard(url.invoice)
            )
            await state.finish()
            await state.set_state('qiwi')
            await state.update_data(payment=url)

        elif payment_system == 'another':
            text = [
                'Украина:',
                f'MonoBank: <code>{config.misc.ua_card}</code>\n',
                'Россия:',
                f'Пополнение через терминал киви: <code>{config.misc.phone}</code>',
                f'QIWI: <code>{config.misc.phone}</code>',
                f'Тинькофф: <code>{config.misc.ru_card}</code>'
            ]
            await call.message.answer('\n'.join(text))
            await call.message.answer(
                text='ГЛАВНОЕ ИМЕТЬ ЧЕК, ЧТОБЫ МЫ МОГЛИ УБЕДИТЬСЯ ЧТО ЭТО ВЫ ОТПРАВИЛИ НАМ ДЕНЬГИ.',
                reply_markup=payment.check
            )
            await state.finish()


async def payment_success(call: types.CallbackQuery, state: FSMContext):
    session_maker = call.bot.get('db')
    await call.answer(cache_time=5)
    data = await state.get_data()
    payment: Payment = data.get('payment')
    try:
        payment.check_payment()
    except NoPaymentFound:
        await call.message.answer('Транзакции не найдено')
        return
    except NotEnoughMoney:
        await call.message.answer('Оплаченная сумма меньше необходимой')
        return
    else:
        await call.message.delete()
        await User.add_currency(session_maker=session_maker, telegram_id=call.from_user.id,
                                currency_type='balance', value=int(payment.amount))

        text = [
            f'Пользователь: {call.from_user.id}',
            f'пополнил баланс на {payment.amount} руб'
        ]
        logging.info(' '.join(text))
        for admin in await User.get_admins(session_maker=session_maker):
            await call.bot.send_message(chat_id=int(admin[0]), text='\n'.join(text))

        await call.message.answer('Успешно оплачено', reply_markup=main_menu.keyboard)
        await BalanceHistory.add_balance_purchase(session_maker=session_maker,
                                                  telegram_id=call.from_user.id,
                                                  money=payment.amount)
    await state.finish()


async def payment_cancel(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text('Операция отменена')
    await state.finish()


async def payment_check(call: types.CallbackQuery, state: FSMContext):
    try:
        await state.finish()
    except Exception:
        pass
    await call.message.edit_text('Отправьте скриншот или фотографию чека после этого сообщения')
    await state.set_state('payment_check')


async def get_payment_check(message: types.Message, state: FSMContext):
    if message.content_type in ['photo', 'document']:
        session_maker = message.bot.get('db')
        text = [
            'Получен чек об оплате',
            f'ID Пользователя: <code>{message.from_user.id}</code>'
        ]
        for admin in await User.get_admins(session_maker=session_maker):
            await message.copy_to(chat_id=int(admin[0]), caption='\n'.join(text))

        await message.answer(
            'Спасибо, ожидайте! Выполняется проверка отправленного чека. Проверка занимает до 24 часов.',
            reply_markup=main_menu.keyboard)
        await state.finish()
    else:
        await message.answer('Пожалуйста, прикрепите фото')


def register_payments(dp: Dispatcher):
    dp.register_message_handler(get_payment, text="Пополнить баланс 💳")
    dp.register_message_handler(get_amount, state=PaymentState.amount)
    dp.register_callback_query_handler(get_payment_system,
                                       payment.payment_choice_callback.filter(),
                                       state=PaymentState.amount)
    dp.register_callback_query_handler(payment_success, text='payment_qiwi_success', state='qiwi')
    dp.register_callback_query_handler(payment_cancel, text='payment_qiwi_cancel', state='*')
    dp.register_callback_query_handler(payment_check, text='payment_check', state='*')
    dp.register_message_handler(get_payment_check, state='payment_check', content_types=['any'])
