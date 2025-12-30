from aiogram import Router, F
from aiogram.types import InputMediaPhoto, CallbackQuery

from .keyboards import build_shop_keyboard

from backend.images.images_url import SHOP_MENU_URL

from backend.repositories.shop_repository import ShopRepository

router = Router()

@router.callback_query(F.data == "shop")
async def shop_clb(callback: CallbackQuery, shop_repo: ShopRepository):

    keyboard = await build_shop_keyboard(shop_repo, parent_id=None)

    text = "Активные категории:"

    content = InputMediaPhoto(
        media=SHOP_MENU_URL,
        caption=text
    )

    await callback.message.edit_media(
        media=content,
        reply_markup=keyboard.as_markup()
    )