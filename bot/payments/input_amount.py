from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.images.images_url import TOPUP_BALANCE_MENU_URL, CHOOSE_PAYMENT_MENU_URL

from .keyboards import back_profile_kb, payment_choice_kb

from backend.states import PaymentStates



router = Router()

@router.callback_query(F.data == "topup_balance")
async def topup_balance_clb(callback: CallbackQuery, state: FSMContext):

    text = "Введите сумму пополнения (RUB):"
    content = InputMediaPhoto(
        media=TOPUP_BALANCE_MENU_URL,
        caption=text
    )
    await callback.message.edit_media(
        media=content,
        reply_markup=back_profile_kb()
    )
    await state.set_state(PaymentStates.waiting_for_amount)
    await callback.answer()

@router.message(PaymentStates.waiting_for_amount)
async def choose_payment_system_clb(message: Message, state: FSMContext):
    try:
        amount = int(message.text)

        if amount <= 0:
            raise ValueError

    except ValueError:
        text = "Введите целое положительное число (больше 0)"
        await message.answer_photo(
            photo=TOPUP_BALANCE_MENU_URL,
            caption=text,
            reply_markup=back_profile_kb()
        )
        return

    await state.update_data(amount=amount)
    text = "Выберите платёжную систему:"
    await message.answer_photo(
        photo=CHOOSE_PAYMENT_MENU_URL,
        caption=text,
        reply_markup=payment_choice_kb()
    )
    await state.set_state(PaymentStates.waiting_for_payment_system)