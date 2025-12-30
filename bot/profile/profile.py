from aiogram import F, Router
from aiogram.types import CallbackQuery, InputMediaPhoto

from backend.repositories.user_repository import ShopUserRepository

from backend.images.images_url import PROFILE_MENU_URL

from .keyboards import profile_kb

from aiogram.fsm.context import FSMContext

router = Router()

@router.callback_query(F.data == "profile")
async def profile_clb(callback: CallbackQuery, user_repo: ShopUserRepository, state: FSMContext):
    tg_id = callback.from_user.id
    user = await user_repo.get_user(tg_id)

    await state.clear()

    text = (
        f"Ваш ID Профиля: <code>{user.tg_id}</code>\n"
        f"Количество заказов: {user.orders_amount} шт.\n"
        f"Баланс: {user.balance} RUB"
    )
    content = InputMediaPhoto(
        caption=text,
        media=PROFILE_MENU_URL
    )

    await callback.message.edit_media(
        media=content,
        reply_markup=profile_kb()
    )