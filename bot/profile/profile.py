from aiogram import F, Router
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from backend.repositories.user_repository import ShopUserRepository
from backend.repositories.shop_page_repository import ShopPageRepository
from .keyboards import profile_kb

router = Router()

PAGE_PROFILE = "profile_menu"


@router.callback_query(F.data == "profile")
async def profile_clb(
    callback: CallbackQuery,
    state: FSMContext,
    shop_id: int,
    user_repo: ShopUserRepository,
    page_repo: ShopPageRepository,
):
    tg_id = callback.from_user.id
    user = await user_repo.get_user(shop_id=shop_id, tg_id=tg_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await state.clear()

    page = await page_repo.get_page(shop_id=shop_id, page_type=PAGE_PROFILE)
    image = page.image if page else None
    header = (page.title if page and page.title else "Профиль")

    text = (
        f"<b>{header}</b>\n\n"
        f"Ваш ID профиля: <code>{user.tg_id}</code>\n"
        f"Количество заказов: {user.orders_amount} шт.\n"
        f"Баланс: {user.balance} RUB"
    )

    if image:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=image, caption=text, parse_mode="HTML"),
            reply_markup=profile_kb(),
        )
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=profile_kb())

    await callback.answer()
