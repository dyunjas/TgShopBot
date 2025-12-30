from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

from aiogram.fsm.context import FSMContext

from backend.states import PromocodeStates

from backend.images.images_url import PROMOCODE_MENU_URL, ERROR_PROMOCODE_MENU_URL, SUCCESS_PROMOCODE_MENU_URL

from .keyboards import promocode_kb, back_promocode_kb

from backend.repositories.promocode_repository import ShopPromocodeRepository
from backend.repositories.user_repository import ShopUserRepository

router = Router()

@router.callback_query(F.data == "enter_promocode")
async def enter_promocode_clb(callback: CallbackQuery, state: FSMContext):
    text = "Введите промокод:"
    
    content = InputMediaPhoto(
        media=PROMOCODE_MENU_URL,
        caption=text
    )

    await callback.message.edit_media(
        media=content,
        reply_markup=promocode_kb()
    )
    await state.set_state(PromocodeStates.waiting_for_code)
    await callback.answer()

@router.message(PromocodeStates.waiting_for_code)
async def process_promocode_clb(message: Message, state: FSMContext, user_repo: ShopUserRepository, promocode_repo: ShopPromocodeRepository):
    
    tg_id = message.from_user.id

    code = message.text.strip()

    promocode = await promocode_repo.activate_promocode(code=code, user_id=tg_id)

    if promocode is None:
        text = "❌ Промокод недействителен или уже использован"
        await message.answer_photo(
            photo=ERROR_PROMOCODE_MENU_URL,
            caption=text,
            reply_markup=promocode_kb()
        )
    else:
        try:
            await user_repo.increase_balance(tg_id, promocode.amount)
        except:
            await message.answer(text="Ошибка обновления баланса, обратитесь в поддержку")
            return
        text = (
            f"✅ Промокод активирован!\n"
            f"🎁 Баланс пополнен на {promocode.amount} RUB."
        )
        await message.answer_photo(
            photo=SUCCESS_PROMOCODE_MENU_URL,
            caption=text,
            reply_markup=back_promocode_kb()
        )
    await state.clear()